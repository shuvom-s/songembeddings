"""
Utility functions for working with lyrics files, supporting both regular and gzipped formats.
"""

import os
import gzip
import re

def slugify(text):
    """
    Convert text to a filesystem-friendly slug format.
    
    Args:
        text (str): Text to convert to slug format
        
    Returns:
        str: Slugified text
    """
    # Convert to lowercase
    text = text.lower()
    # Remove characters that are not alphanumeric, spaces, or hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    # Replace any sequence of whitespace with a single hyphen
    text = re.sub(r'\s+', '-', text)
    return text.strip('-')

def get_lyrics_path(artist, track, base_dir='songs'):
    """
    Get the expected path for a lyrics file.
    
    Args:
        artist (str): Artist name
        track (str): Track name
        base_dir (str): Base directory for lyrics files (default: 'songs')
        
    Returns:
        tuple: (artist_slug, track_slug, expected_path)
    """
    artist_slug = slugify(artist)
    track_slug = slugify(track)
    expected_path = os.path.join(base_dir, artist_slug, f'{track_slug}.txt')
    return artist_slug, track_slug, expected_path

def read_lyrics_file(filepath):
    """
    Read lyrics from a file, handling both regular and gzipped files.
    
    Args:
        filepath (str): Path to the lyrics file
        
    Returns:
        str or None: Lyrics content if file exists, None otherwise
    """
    # Check for regular file first
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    
    # Check for gzipped file
    gzipped_filepath = f"{filepath}.gz"
    if os.path.exists(gzipped_filepath):
        with gzip.open(gzipped_filepath, 'rt', encoding='utf-8') as f:
            return f.read()
            
    # Neither file exists
    return None

def save_lyrics(lyrics, artist_name, song_name, compress=True, base_dir='songs'):
    """
    Save lyrics to a file, optionally compressing with gzip.
    
    Args:
        lyrics (str): Lyrics content to save
        artist_name (str): Artist name
        song_name (str): Song name
        compress (bool): Whether to compress the file with gzip (default: True)
        base_dir (str): Base directory for lyrics files (default: 'songs')
    """
    songs_dir = os.path.join(os.getcwd(), base_dir)
    os.makedirs(songs_dir, exist_ok=True)
    
    artist_slug = slugify(artist_name)
    artist_dir = os.path.join(songs_dir, artist_slug)
    os.makedirs(artist_dir, exist_ok=True)
    
    track_slug = slugify(song_name)
    
    if compress:
        # Save as gzipped file
        lyrics_file = os.path.join(artist_dir, f"{track_slug}.txt.gz")
        with gzip.open(lyrics_file, 'wt', encoding='utf-8') as f:
            f.write(lyrics)
    else:
        # Save as regular file
        lyrics_file = os.path.join(artist_dir, f"{track_slug}.txt")
        with open(lyrics_file, 'w', encoding='utf-8') as f:
            f.write(lyrics)
            
def lyrics_exists(artist, track, base_dir='songs'):
    """
    Check if lyrics file exists for a given artist and track.
    
    Args:
        artist (str): Artist name
        track (str): Track name
        base_dir (str): Base directory for lyrics files (default: 'songs')
        
    Returns:
        bool: True if lyrics file exists (compressed or uncompressed), False otherwise
    """
    _, _, expected_path = get_lyrics_path(artist, track, base_dir)
    return os.path.exists(expected_path) or os.path.exists(f"{expected_path}.gz")

def get_lyrics(artist, track, base_dir='songs'):
    """
    Get lyrics for a given artist and track.
    
    Args:
        artist (str): Artist name
        track (str): Track name
        base_dir (str): Base directory for lyrics files (default: 'songs')
        
    Returns:
        str or None: Lyrics content if file exists, None otherwise
    """
    _, _, expected_path = get_lyrics_path(artist, track, base_dir)
    return read_lyrics_file(expected_path)

def compress_lyrics_directory(base_dir='songs'):
    """
    Compress all lyrics files in a directory with gzip.
    
    Args:
        base_dir (str): Base directory for lyrics files (default: 'songs')
        
    Returns:
        tuple: (compressed_count, total_count) - number of files compressed and total files
    """
    compressed_count = 0
    total_count = 0
    
    # Walk through the directory structure
    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.txt') and not file.endswith('.txt.gz'):
                filepath = os.path.join(root, file)
                total_count += 1
                
                # Read content
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Write compressed version
                gzipped_filepath = f"{filepath}.gz"
                with gzip.open(gzipped_filepath, 'wt', encoding='utf-8') as f:
                    f.write(content)
                
                # Remove original file
                os.remove(filepath)
                compressed_count += 1
    
    return compressed_count, total_count 