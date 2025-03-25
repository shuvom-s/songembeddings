"""
Script to train a sparse autoencoder on song lyrics embeddings.
This will create a model that can be used for visualization.
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import os
import argparse
from tqdm import tqdm

from sparse_autoencoder import FastAutoencoder, unit_norm_decoder_

def unit_norm_decoder_grad_adjustment_(autoencoder):
    """Adjust gradients to maintain unit norm constraint."""
    if autoencoder.decoder.weight.grad is not None:
        with torch.no_grad():
            proj = torch.sum(autoencoder.decoder.weight * autoencoder.decoder.weight.grad, dim=0, keepdim=True)
            autoencoder.decoder.weight.grad.sub_(proj * autoencoder.decoder.weight)

def normalized_mse(recon, xs):
    """Normalized mean squared error."""
    return F.mse_loss(recon, xs) / F.mse_loss(xs.mean(dim=0, keepdim=True).expand_as(xs), xs)

def loss_fn(ae, x, recons, info, auxk_coef, multik_coef=0):
    """Compute loss for the autoencoder."""
    device = x.device
    recons_loss = normalized_mse(recons, x)
    
    if multik_coef > 0 and info["multik_recons"] is not None:
        recons_loss = recons_loss + multik_coef * normalized_mse(info["multik_recons"], x)
    
    if ae.auxk is not None:
        e = x - recons
        auxk_latents = torch.zeros_like(info["latents_pre_act"])
        if info["auxk_indices"] is not None and info["auxk_values"] is not None:
            auxk_latents.scatter_(-1, info["auxk_indices"], info["auxk_values"])
        e_hat = ae.decoder(auxk_latents)  # reconstruction of error using dead latents
        auxk_loss = normalized_mse(e_hat, e)
        total_loss = recons_loss + auxk_coef * auxk_loss
    else:
        auxk_loss = torch.tensor(0.0, device=device)
        total_loss = recons_loss
    
    return total_loss, recons_loss, auxk_loss

def init_from_data_(ae, data_sample):
    """Initialize autoencoder parameters from data."""
    # Set pre_bias to median of data
    ae.pre_bias.data = torch.median(data_sample, dim=0).values
    nn.init.xavier_uniform_(ae.decoder.weight)

    # Decoder is unit norm
    unit_norm_decoder_(ae)

    # Encoder as transpose of decoder
    ae.encoder.weight.data = ae.decoder.weight.t().clone()

    # Zero initialize latent bias
    nn.init.zeros_(ae.latent_bias)

def train(ae, train_loader, optimizer, epochs, k, auxk_coef, multik_coef=0, clip_grad=None, save_dir="models/sparse_autoencoder"):
    """Train the autoencoder."""
    os.makedirs(save_dir, exist_ok=True)
    device = next(ae.parameters()).device
    
    num_batches = len(train_loader)
    print(f"Training for {epochs} epochs with {num_batches} batches per epoch")
    print(f"Model is on device: {device}")
    print(f"stats_last_nonzero is on device: {ae.stats_last_nonzero.device}")
    
    for epoch in range(epochs):
        ae.train()
        total_loss = 0
        
        for batch in tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}"):
            optimizer.zero_grad()
            x = batch[0].to(device)
            recons, info = ae(x)
            loss, recons_loss, auxk_loss = loss_fn(ae, x, recons, info, auxk_coef, multik_coef)
            loss.backward()
            
            # Apply gradient adjustment to maintain unit norm constraint
            unit_norm_decoder_grad_adjustment_(ae)
            
            if clip_grad is not None:
                torch.nn.utils.clip_grad_norm_(ae.parameters(), clip_grad)
            
            optimizer.step()
            
            # Ensure decoder weight is normalized after the update
            unit_norm_decoder_(ae)
            
            total_loss += loss.item()
        
        avg_loss = total_loss / len(train_loader)
        print(f"Epoch {epoch+1}, Average Loss: {avg_loss:.4f}")
        
        # Calculate proportion of dead latents
        dead_latents_prop = (ae.stats_last_nonzero > num_batches).float().mean().item()
        print(f"Proportion of dead latents: {dead_latents_prop:.4f}")

        # Save model periodically
        if (epoch + 1) % 10 == 0 or epoch == epochs - 1:
            save_path = os.path.join(save_dir, f"epoch_{epoch+1}.pth")
            torch.save(ae.state_dict(), save_path)
            print(f"Model saved to {save_path}")
    
    # Save final model
    save_path = os.path.join(save_dir, f"epoch_end.pth")
    torch.save(ae.state_dict(), save_path)
    print(f"Final model saved to {save_path}")

def main():
    parser = argparse.ArgumentParser(description='Train a sparse autoencoder on song lyrics embeddings')
    parser.add_argument('--input', type=str, default='embeddings/liked_songs_embeddings_openai-small.npy',
                       help='Input embeddings file (.npy)')
    parser.add_argument('--output-dir', type=str, default='models/sparse_autoencoder',
                       help='Output directory for model')
    parser.add_argument('--n-neurons', type=int, default=32,
                       help='Number of neurons in the SAE')
    parser.add_argument('--k', type=int, default=2,
                       help='Sparsity parameter (top-k)')
    parser.add_argument('--auxk', type=int, default=4,
                       help='Auxiliary k parameter (2*k recommended)')
    parser.add_argument('--batch-size', type=int, default=128,
                       help='Batch size for training')
    parser.add_argument('--epochs', type=int, default=50,
                       help='Number of training epochs')
    parser.add_argument('--lr', type=float, default=1e-4,
                       help='Learning rate')
    parser.add_argument('--auxk-coef', type=float, default=1/32,
                       help='Coefficient for auxiliary loss')
    parser.add_argument('--multik-coef', type=float, default=0,
                       help='Coefficient for multi-k loss (0 to disable)')
    parser.add_argument('--clip-grad', type=float, default=1.0,
                       help='Gradient clipping value')
    parser.add_argument('--no-cuda', action='store_true',
                       help='Disable CUDA even if available')
    args = parser.parse_args()
    
    # Create output directory if it doesn't exist
    model_dir = os.path.join(
        args.output_dir,
        f"{os.path.basename(args.input).replace('.npy', '')}_ndirs:{args.n_neurons}_k:{args.k}"
    )
    os.makedirs(model_dir, exist_ok=True)
    
    # Load embeddings
    print(f"Loading embeddings from {args.input}...")
    embeddings = np.load(args.input).astype(np.float32)
    print(f"Loaded embeddings with shape {embeddings.shape}")
    
    # Create dataset and dataloader
    dataset = TensorDataset(torch.tensor(embeddings))
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True)
    
    # Initialize model
    d_model = embeddings.shape[1]
    
    # Set device
    if args.no_cuda:
        device = torch.device("cpu")
    else:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Create model and move to device
    model = FastAutoencoder(args.n_neurons, d_model, args.k, args.auxk, 128)
    model = model.to(device)
    
    # Verify all model parts are on the same device
    print(f"Model parameters device check:")
    print(f"- encoder: {model.encoder.weight.device}")
    print(f"- decoder: {model.decoder.weight.device}")
    print(f"- pre_bias: {model.pre_bias.device}")
    print(f"- stats_last_nonzero: {model.stats_last_nonzero.device}")
    
    # Initialize model parameters
    print("Initializing model parameters from data...")
    init_from_data_(model, torch.tensor(embeddings, dtype=torch.float32).to(device))
    
    # Initialize optimizer
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
    
    # Train model
    print("Starting training...")
    train(
        model, 
        dataloader, 
        optimizer, 
        args.epochs, 
        args.k, 
        args.auxk_coef,
        args.multik_coef,
        args.clip_grad,
        save_dir=model_dir
    )
    
    print("Training complete!")

if __name__ == "__main__":
    main() 