import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from tqdm import tqdm

class FastAutoencoder(nn.Module):
    def __init__(self, n_dirs: int, d_model: int, k: int, auxk: int = None, multik: int = 128, dead_steps_threshold: int = 266):
        super().__init__()
        self.n_dirs = n_dirs
        self.d_model = d_model
        self.k = k
        self.auxk = auxk
        self.multik = multik 
        self.dead_steps_threshold = dead_steps_threshold

        self.encoder = nn.Linear(d_model, n_dirs, bias=False)
        self.decoder = nn.Linear(n_dirs, d_model, bias=False)

        self.pre_bias = nn.Parameter(torch.zeros(d_model))
        self.latent_bias = nn.Parameter(torch.zeros(n_dirs))

        # Initialize stats_last_nonzero as a registered buffer instead of a regular tensor
        # This ensures it will be properly moved to the correct device with the model
        self.register_buffer('stats_last_nonzero', torch.zeros(n_dirs, dtype=torch.long))
        
        # Don't manually move to device here - let the user do this with model.to(device)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def forward(self, x):
        """Forward pass through the autoencoder."""
        device = self.pre_bias.device  # Get the current device from a parameter
        
        if isinstance(x, np.ndarray):
            x = torch.tensor(x, dtype=torch.float32).to(device)
            
        x = x - self.pre_bias
        latents_pre_act = self.encoder(x) + self.latent_bias

        # Main top-k selection
        topk_values, topk_indices = torch.topk(latents_pre_act, k=self.k, dim=-1)
        topk_values = F.relu(topk_values)
        
        if self.multik:
            multik_values, multik_indices = torch.topk(latents_pre_act, k=min(4*self.k, latents_pre_act.shape[-1]), dim=-1)
            multik_values = F.relu(multik_values)
            multik_latents = torch.zeros_like(latents_pre_act)
            multik_latents.scatter_(-1, multik_indices, multik_values)
        else:
            multik_latents = None

        latents = torch.zeros_like(latents_pre_act)
        latents.scatter_(-1, topk_indices, topk_values)

        # Update stats_last_nonzero
        self.stats_last_nonzero += 1
        unique_indices = topk_indices.unique()
        if unique_indices.numel() > 0:  # Check if there are any unique indices
            # Ensure unique_indices is on the same device as stats_last_nonzero
            unique_indices = unique_indices.to(self.stats_last_nonzero.device)
            self.stats_last_nonzero.scatter_(0, unique_indices, 0)

        recons = self.decoder(latents) + self.pre_bias
        
        if multik_latents is not None:
            multik_recons = self.decoder(multik_latents) + self.pre_bias
        else:
            multik_recons = None

        # AuxK
        auxk_values, auxk_indices = None, None
        if self.auxk is not None:
            # Create dead latents mask
            dead_mask = (self.stats_last_nonzero > self.dead_steps_threshold).float()
            
            # Apply mask to latents_pre_act
            dead_latents_pre_act = latents_pre_act * dead_mask
            
            # Select top-k_aux from dead latents
            auxk_values, auxk_indices = torch.topk(dead_latents_pre_act, k=min(self.auxk, dead_latents_pre_act.shape[-1]), dim=-1)
            auxk_values = F.relu(auxk_values)

        return recons, {
            "topk_indices": topk_indices,
            "topk_values": topk_values,
            "multik_recons": multik_recons,
            "auxk_indices": auxk_indices,
            "auxk_values": auxk_values,
            "latents_pre_act": latents_pre_act,
            "latents_post_act": latents,
        }

    def decode_sparse(self, indices, values):
        """Decode from sparse representation (indices and values)."""
        device = self.pre_bias.device
        if isinstance(indices, np.ndarray):
            indices = torch.tensor(indices, dtype=torch.long).to(device)
        if isinstance(values, np.ndarray):
            values = torch.tensor(values, dtype=torch.float32).to(device)
            
        latents = torch.zeros(self.n_dirs, device=device)
        latents.scatter_(-1, indices, values)
        return self.decoder(latents) + self.pre_bias
    
    def decode_clamp(self, latents, clamp):
        """Decode with clamping."""
        device = self.pre_bias.device
        if isinstance(latents, np.ndarray):
            latents = torch.tensor(latents, dtype=torch.float32).to(device)
        if isinstance(clamp, np.ndarray):
            clamp = torch.tensor(clamp, dtype=torch.float32).to(device)
            
        topk_values, topk_indices = torch.topk(latents, k=min(64, latents.shape[-1]), dim=-1)
        topk_values = F.relu(topk_values)
        latents = torch.zeros_like(latents)
        latents.scatter_(-1, topk_indices, topk_values)
        # multiply latents by clamp, which is 1D but has has the same size as each latent vector
        latents = latents * clamp
        
        return self.decoder(latents) + self.pre_bias
    
    def decode_at_k(self, latents, k):
        """Decode with specific k value."""
        device = self.pre_bias.device
        if isinstance(latents, np.ndarray):
            latents = torch.tensor(latents, dtype=torch.float32).to(device)
            
        topk_values, topk_indices = torch.topk(latents, k=min(k, latents.shape[-1]), dim=-1)
        topk_values = F.relu(topk_values)
        latents = torch.zeros_like(latents)
        latents.scatter_(-1, topk_indices, topk_values)
        
        return self.decoder(latents) + self.pre_bias
    
    def get_topk_activations(self, x, batch_size=1024):
        """Get top-k activations for each neuron."""
        device = self.pre_bias.device
        if isinstance(x, np.ndarray):
            x = torch.tensor(x, dtype=torch.float32)
            
        all_activations = self.compute_activations(x, batch_size)
        
        # Get top-k values and indices for each neuron
        topk_values = []
        topk_indices = []
        
        for neuron_idx in range(self.n_dirs):
            neuron_activations = all_activations[:, neuron_idx]
            # Get top-k indices and values
            k = min(self.k, len(neuron_activations))
            indices = np.argsort(neuron_activations)[-k:][::-1]
            values = neuron_activations[indices]
            
            topk_indices.append(indices)
            topk_values.append(values)
            
        return np.array(topk_indices), np.array(topk_values)
    
    def compute_activations(self, x, batch_size=1024):
        """Compute activations for all inputs."""
        device = self.pre_bias.device
        all_activations = []
        
        # Process in batches
        num_samples = len(x)
        for i in range(0, num_samples, batch_size):
            batch = x[i:i+batch_size]
            if isinstance(batch, np.ndarray):
                batch = torch.tensor(batch, dtype=torch.float32).to(device)
                
            with torch.no_grad():
                # Get raw activations from encoder (pre-ReLU)
                x_centered = batch - self.pre_bias
                latents_pre_act = self.encoder(x_centered) + self.latent_bias
                # Apply ReLU
                activations = F.relu(latents_pre_act)
            
            all_activations.append(activations.cpu().numpy())
            
        # Combine batches
        return np.vstack(all_activations)


def load_sae_model(model_path, n_neurons=64, n_input_features=1536, k=2, auxk=4):
    """Load a pre-trained sparse autoencoder model."""
    try:
        model = FastAutoencoder(n_neurons, n_input_features, k, auxk)
        
        # Check if CUDA is available and move model to GPU if possible
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        
        # Load model weights
        state_dict = torch.load(model_path, map_location=device)
        model.load_state_dict(state_dict)
        model.eval()  # Set model to evaluation mode
        
        print(f"Successfully loaded SAE model from {model_path}")
        return model
    except Exception as e:
        print(f"Error loading SAE model: {e}")
        return None


def unit_norm_decoder_(autoencoder):
    """Normalize decoder weights to unit norm."""
    with torch.no_grad():
        autoencoder.decoder.weight.div_(autoencoder.decoder.weight.norm(dim=0, keepdim=True)) 