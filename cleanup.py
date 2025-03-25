#!/usr/bin/env python3
"""
Cleanup script for the song lyrics visualization project.

This script:
1. Removes old files that have been consolidated or are no longer needed
2. Ensures the correct directory structure
3. Updates file paths in remaining files if needed
"""

import os
import shutil
import sys

# Files to remove (old or consolidated)
files_to_remove = [
    'extract_songs.py',
    'COMPRESSION_README.md',
    'LYRICS_COPYRIGHT_README.md',
    'setup_lyrics.py',
    'compress_songs.py',
    'lyrics_placeholder.py',
    'full_scraper.ipynb',
    'genius_scraper.ipynb',
    'stock_simulation.ipynb',
    'songs.txt',
    'deployment_guide.md',
]

# Directories to remove or clean
directories_to_clean = [
    '__pycache__',
    'website',
]

def main():
    print("Starting cleanup process...")
    
    # Get current directory
    current_dir = os.getcwd()
    print(f"Current directory: {current_dir}")
    
    # Check if expected directories exist, create if not
    for dir_name in ['data', 'data/embeddings', 'src', 'web']:
        dir_path = os.path.join(current_dir, dir_name)
        if not os.path.exists(dir_path):
            print(f"Creating directory: {dir_path}")
            os.makedirs(dir_path, exist_ok=True)
    
    # Remove old files
    for file_name in files_to_remove:
        file_path = os.path.join(current_dir, file_name)
        if os.path.exists(file_path):
            print(f"Removing file: {file_path}")
            os.remove(file_path)
    
    # Clean directories
    for dir_name in directories_to_clean:
        dir_path = os.path.join(current_dir, dir_name)
        if os.path.exists(dir_path):
            print(f"Removing directory: {dir_path}")
            shutil.rmtree(dir_path)
    
    # Check that all required files exist in the new structure
    required_files = {
        'src/lyrics_manager.py': 'src/lyrics_manager.py exists - ✓',
        'src/lyrics_utils.py': 'src/lyrics_utils.py exists - ✓',
        'src/prepare_data.py': 'src/prepare_data.py exists - ✓',
        'src/sparse_autoencoder.py': 'src/sparse_autoencoder.py exists - ✓',
        'web/index.html': 'web/index.html exists - ✓',
        'web/styles.css': 'web/styles.css exists - ✓',
        'web/scripts.js': 'web/scripts.js exists - ✓',
        'web/server.py': 'web/server.py exists - ✓',
        'README.md': 'README.md exists - ✓'
    }
    
    missing_files = []
    for file_path, message in required_files.items():
        full_path = os.path.join(current_dir, file_path)
        if os.path.exists(full_path):
            print(message)
        else:
            missing_files.append(file_path)
            print(f"{file_path} is missing - ✗")
    
    if missing_files:
        print("\nWARNING: Some required files are missing. Please make sure they exist before continuing.")
    
    # Check for songs.tar.gz in the correct location
    tarball_path = os.path.join(current_dir, 'data', 'songs.tar.gz')
    if os.path.exists(tarball_path):
        print("songs.tar.gz exists in data/ directory - ✓")
    else:
        old_tarball_path = os.path.join(current_dir, 'songs.tar.gz')
        if os.path.exists(old_tarball_path):
            print("Moving songs.tar.gz to data/ directory...")
            shutil.move(old_tarball_path, tarball_path)
        else:
            print("WARNING: songs.tar.gz is missing. You will need to provide it for full functionality.")
    
    # Check for embeddings files
    embeddings_file = os.path.join(current_dir, 'data', 'embeddings', 'liked_songs_embeddings_openai-small.npy')
    metadata_file = os.path.join(current_dir, 'data', 'embeddings', 'liked_songs_with_lyrics_openai-small.csv')
    
    if not os.path.exists(embeddings_file) or not os.path.exists(metadata_file):
        old_embeddings_dir = os.path.join(current_dir, 'embeddings')
        if os.path.exists(old_embeddings_dir):
            print("Moving embeddings files to data/embeddings/ directory...")
            for filename in os.listdir(old_embeddings_dir):
                if filename.startswith('liked_songs_'):
                    src_path = os.path.join(old_embeddings_dir, filename)
                    dst_path = os.path.join(current_dir, 'data', 'embeddings', filename)
                    shutil.copy2(src_path, dst_path)
    
    print("\nCleanup completed!")
    print("\nTo start the visualization:")
    print("1. Set up lyrics: python src/lyrics_manager.py setup")
    print("2. Prepare data:  python src/prepare_data.py")
    print("3. Start server:  python web/server.py")

if __name__ == "__main__":
    main() 