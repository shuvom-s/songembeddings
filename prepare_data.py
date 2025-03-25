import numpy as np
import pandas as pd
import json
import umap.umap_ as umap
import os
import gzip
from collections import Counter
import argparse
import torch

# Import our lyrics utilities
import lyrics_utils

def read_lyrics_for_dataset(df):
    """
    Read lyrics for all songs in the dataset, handling both compressed and uncompressed files.
    
    Args:
        df (pandas.DataFrame): DataFrame containing song metadata
        
    Returns:
        pandas.DataFrame: Updated DataFrame with lyrics and has_lyrics columns
    """
    print("Reading lyrics from song files (supporting both .txt and .txt.gz)...")
    
    has_lyrics = []
    lyrics = []
    
    for _, row in df.iterrows():
        # Get artist and track name
        artist = str(row['Artist Name(s)']).split(',')[0].strip()  # Get first artist only
        track = str(row['Track Name'])
        
        # Try to get lyrics using our utility
        lyric_content = lyrics_utils.get_lyrics(artist, track)
        has_lyric = lyric_content is not None
        
        has_lyrics.append(has_lyric)
        lyrics.append(lyric_content if has_lyric else "")
    
    # Add has_lyrics column to dataframe    
    df['has_lyrics'] = has_lyrics
    
    # Create new dataframe with only rows that have lyrics files
    df_with_lyrics = df[df['has_lyrics']].reset_index(drop=True)
    df_with_lyrics['lyrics'] = lyrics
    
    # Print summary
    print(f"Found lyrics files for {len(df_with_lyrics)} out of {len(df)} songs")
    
    return df_with_lyrics

def main():
    parser = argparse.ArgumentParser(description='Prepare data for song lyrics embedding visualization')
    parser.add_argument('--sae-model', type=str, default=None, help='Path to sparse autoencoder model')
    parser.add_argument('--n-neurons', type=int, default=32, help='Number of neurons in the sparse autoencoder')
    parser.add_argument('--k', type=int, default=2, help='Sparsity parameter for the autoencoder')
    parser.add_argument('--auxk', type=int, default=4, help='Auxiliary k parameter for the autoencoder')
    parser.add_argument('--embeddings-file', type=str, default='embeddings/liked_songs_embeddings_openai-small.npy',
                       help='Path to embeddings file (.npy)')
    parser.add_argument('--metadata-file', type=str, default='embeddings/liked_songs_with_lyrics_openai-small.csv',
                       help='Path to metadata file (.csv)')
    args = parser.parse_args()

    print("Preparing data for the song lyrics embedding visualization...")
    
    # Load the embeddings and song data
    embeddings_file = args.embeddings_file
    metadata_file = args.metadata_file
    
    print(f"Loading embeddings from {embeddings_file}...")
    embeddings = np.load(embeddings_file)
    
    print(f"Loading song metadata from {metadata_file}...")
    df = pd.read_csv(metadata_file)
    
    print(f"Loaded {len(df)} songs with {embeddings.shape[1]} dimensional embeddings")
    
    # Check if 'lyrics' column is missing, in which case we need to read lyrics files
    if 'lyrics' not in df.columns:
        df = read_lyrics_for_dataset(df)
    
    # Load sparse autoencoder model if specified
    sae_data = None
    if args.sae_model:
        try:
            from sparse_autoencoder import load_sae_model
            print(f"Loading sparse autoencoder model from {args.sae_model}...")
            sae_model = load_sae_model(
                args.sae_model, 
                n_neurons=args.n_neurons, 
                n_input_features=embeddings.shape[1], 
                k=args.k,
                auxk=args.auxk
            )
            
            if sae_model:
                print("Computing neuron activations...")
                activations = sae_model.compute_activations(embeddings)
                
                # Get top activating songs for each neuron
                topk_indices, topk_values = sae_model.get_topk_activations(embeddings)
                
                # Prepare data about each neuron
                neuron_data = []
                for neuron_idx in range(args.n_neurons):
                    # Get top-5 activations for this neuron
                    top_indices = topk_indices[neuron_idx]
                    top_values = topk_values[neuron_idx]
                    
                    top_songs = []
                    for i in range(min(5, len(top_indices))):
                        song_idx = top_indices[i]
                        song_data = {
                            'index': int(song_idx),
                            'title': str(df.iloc[song_idx]['Track Name']),
                            'artist': str(df.iloc[song_idx]['Artist Name(s)']),
                            'activation': float(top_values[i])
                        }
                        top_songs.append(song_data)
                    
                    neuron_data.append({
                        'id': neuron_idx,
                        'top_songs': top_songs
                    })
                
                # Save SAE data
                sae_data = {
                    'neurons': neuron_data,
                    'activations': activations.tolist()
                }
                
                print(f"Generated SAE data for {args.n_neurons} neurons")
        except Exception as e:
            print(f"Error loading or using SAE model: {e}")
            print("Continuing without SAE features...")
    
    # Run UMAP with DensMAP for dimensionality reduction
    print("Performing dimensionality reduction with DensMAP...")
    reducer = umap.UMAP(densmap=True, random_state=42)
    embeddings_2d = reducer.fit_transform(embeddings)
    
    print(f"Reduced embeddings to 2D: {embeddings_2d.shape}")
    
    # Prepare data for visualization
    print("Preparing data for visualization...")
    
    # Extract genres and make them a list for each song
    df['genre_list'] = df['Genres'].apply(lambda x: [] if pd.isna(x) else [g.strip() for g in x.split(',')])
    
    # Prepare a list of all unique genres for filtering and count occurrences
    all_genres = []
    for genres in df['genre_list']:
        all_genres.extend(genres)
    
    # Count genres
    genre_counts = Counter(all_genres)
    
    # Create a list of (genre, count) tuples sorted by count (descending)
    sorted_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Prepare a list of all unique artists for filtering
    # Extract first artist from Artist Name(s) column
    df['primary_artist'] = df['Artist Name(s)'].apply(lambda x: x.split(',')[0].strip() if pd.notna(x) else "Unknown")
    
    # Count artists
    artist_counts = Counter(df['primary_artist'])
    
    # Create a list of (artist, count) tuples sorted by count (descending)
    sorted_artists = sorted(artist_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Create a JSON object with the data for visualization
    visualization_data = {
        'embeddings': embeddings_2d.tolist(),
        'songs': []
    }
    
    # Add song details
    for i, row in df.iterrows():
        # Truncate lyrics to first 10 lines for preview
        lyrics_preview = '\n'.join(row['lyrics'].split('\n')[:10]) if pd.notna(row['lyrics']) else ""
        
        # Ensure genres are strings and not numpy objects or other non-serializable types
        genres = [str(g) for g in row['genre_list']]
        
        song_data = {
            'id': int(i),  # Ensure id is an integer
            'title': str(row['Track Name']),
            'artist': str(row['Artist Name(s)']),
            'primary_artist': str(row['primary_artist']),
            'album': str(row['Album Name']) if pd.notna(row['Album Name']) else "",
            'genres': genres,
            'lyrics_preview': lyrics_preview,
            'popularity': int(row['Popularity']) if pd.notna(row['Popularity']) else 0,
            'release_date': str(row['Release Date']) if pd.notna(row['Release Date']) else "",
        }
        visualization_data['songs'].append(song_data)
    
    # Add filter options with counts
    visualization_data['filters'] = {
        'genres': sorted_genres,
        'artists': sorted_artists
    }
    
    # Add SAE data if available
    if sae_data:
        visualization_data['sae'] = sae_data
    
    # Debug: Print some information about the data
    print(f"Total unique genres: {len(sorted_genres)}")
    print(f"Top 5 genres: {sorted_genres[:5]}")
    print(f"Total unique artists: {len(sorted_artists)}")
    print(f"Top 5 artists: {sorted_artists[:5]}")
    
    # Debug: Print a sample song to check structure
    print("\nSample song data:")
    print(json.dumps(visualization_data['songs'][0], indent=2))
    
    # Save the data to a JSON file
    output_file = 'data.json'
    print(f"Saving visualization data to {output_file}...")
    
    with open(output_file, 'w') as f:
        json.dump(visualization_data, f)
    
    print("Data preparation complete!")

if __name__ == "__main__":
    main() 