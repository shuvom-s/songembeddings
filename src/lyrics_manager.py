#!/usr/bin/env python3
"""
Consolidated Lyrics Manager

This script provides a comprehensive solution for managing song lyrics while complying
with copyright restrictions. It offers functionality to:

1. Extract real lyrics from a tarball for local development
2. Create placeholder lyrics for public sharing
3. Switch between real and placeholder lyrics
4. Compress lyrics files to save disk space
5. Update the application to work with either set

All functionality is accessible through a single command-line interface.
"""

import os
import sys
import re
import argparse
import tarfile
import gzip
import shutil
import subprocess
import random
import pandas as pd
from pathlib import Path
from tqdm import tqdm

# Import lyrics_utils if available, otherwise include core functions directly
try:
    import lyrics_utils
    from lyrics_utils import slugify, get_lyrics_path, read_lyrics_file
except ImportError:
    # Define core functions inline if lyrics_utils is not available
    def slugify(text):
        """Convert text to a filesystem-friendly slug format."""
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'\s+', '-', text)
        return text.strip('-')
    
    def get_lyrics_path(artist, track, base_dir='songs'):
        """Get the expected path for a lyrics file."""
        artist_slug = slugify(artist)
        track_slug = slugify(track)
        expected_path = os.path.join(base_dir, artist_slug, f'{track_slug}.txt')
        return artist_slug, track_slug, expected_path
    
    def read_lyrics_file(filepath):
        """Read lyrics from a file, handling both regular and gzipped files."""
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        
        gzipped_filepath = f"{filepath}.gz"
        if os.path.exists(gzipped_filepath):
            with gzip.open(gzipped_filepath, 'rt', encoding='utf-8') as f:
                return f.read()
                
        return None

# Constants
DEFAULT_TARBALL = 'data/songs.tar.gz'
DEFAULT_OUTPUT_DIR = 'songs'
DEFAULT_METADATA = 'data/embeddings/liked_songs_with_lyrics_openai-small.csv'
DEFAULT_GITIGNORE_CONTENT = """# Lyrics management - DO NOT COMMIT REAL LYRICS
*.tar.gz
*.gz
# Ignore extracted songs from tarball
/songs_real/
# Add other patterns as needed
"""

# Placeholder templates for copyright-safe placeholders
PLACEHOLDER_TEMPLATES = [
    "[Placeholder lyrics for copyright reasons]\n\nThis is a placeholder for the song '{title}' by {artist}.\nThe original lyrics are not included for copyright reasons.",
    
    "// PLACEHOLDER CONTENT //\n\nSong: {title}\nArtist: {artist}\n\nActual lyrics have been removed for copyright protection.\nPlease obtain lyrics from a licensed source.",
    
    "LYRICS PLACEHOLDER\n\n{title} - {artist}\n\nThis file contains no actual lyrics due to copyright restrictions.\nThe visualization will still work with this placeholder.",
]

def extract_real_lyrics(tarball_path, output_dir, keep_tar=True):
    """Extract real lyrics from tarball for local development."""
    # Ensure tarball exists
    if not os.path.exists(tarball_path):
        print(f"Error: Tarball file '{tarball_path}' not found.")
        return False
    
    # Create temp output directory name
    temp_dir = f"{output_dir}_real"
    
    # Remove temp dir if it exists
    if os.path.exists(temp_dir):
        print(f"Removing existing directory '{temp_dir}'...")
        shutil.rmtree(temp_dir)
    
    # Create temp directory
    os.makedirs(temp_dir, exist_ok=True)
    
    # Extract tarball
    print(f"Extracting '{tarball_path}' to '{temp_dir}'...")
    try:
        with tarfile.open(tarball_path, 'r:gz') as tar:
            tar.extractall(path=temp_dir)
        
        # Count extracted files
        file_count = 0
        for root, _, files in os.walk(temp_dir):
            file_count += len(files)
        print(f"Extracted {file_count} files.")
        
        # Success
        return True
        
    except Exception as e:
        print(f"Error during extraction: {e}")
        return False

def create_placeholder_lyrics(output_dir, metadata_file):
    """Create placeholder lyrics for public sharing."""
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load metadata
    try:
        df = pd.read_csv(metadata_file)
        print(f"Loaded metadata for {len(df)} songs")
    except Exception as e:
        print(f"Error loading metadata file: {e}")
        return False
    
    files_created = 0
    
    # Create placeholder files for each song
    for _, row in tqdm(df.iterrows(), total=len(df), desc="Creating placeholders"):
        try:
            # Get artist and track
            artist = str(row['Artist Name(s)']).split(',')[0].strip()
            track = str(row['Track Name'])
            
            # Skip if artist or track is invalid
            if artist.lower() == 'nan' or track.lower() == 'nan':
                continue
                
            # Get album and release date for extra metadata
            album = str(row['Album Name']) if 'Album Name' in row and pd.notna(row['Album Name']) else "Unknown Album"
            release_date = str(row['Release Date']) if 'Release Date' in row and pd.notna(row['Release Date']) else "Unknown Date"
            
            # Create artist directory
            artist_slug = slugify(artist)
            artist_dir = os.path.join(output_dir, artist_slug)
            os.makedirs(artist_dir, exist_ok=True)
            
            # Create track file
            track_slug = slugify(track)
            track_file = os.path.join(artist_dir, f"{track_slug}.txt")
            
            # Choose a random placeholder template
            placeholder = random.choice(PLACEHOLDER_TEMPLATES)
            placeholder_text = placeholder.format(
                title=track,
                artist=artist,
                album=album,
                release_date=release_date
            )
            
            # Write placeholder file
            with open(track_file, 'w', encoding='utf-8') as f:
                f.write(placeholder_text)
            
            files_created += 1
            
        except Exception as e:
            print(f"Error creating placeholder for {artist} - {track}: {e}")
    
    print(f"Created {files_created} placeholder lyrics files in '{output_dir}'")
    
    # Create .gitignore to protect real lyrics if they exist
    gitignore_path = os.path.join(output_dir, '.gitignore')
    with open(gitignore_path, 'w') as f:
        f.write("# Ignore actual lyrics files if they exist\n")
        f.write("*.gz\n")
        f.write("# Add other patterns as needed\n")
    
    print(f"Created .gitignore file in {output_dir} to protect any real lyrics files")
    
    return True

def use_real_lyrics(output_dir):
    """Switch to using real lyrics from extracted tarball."""
    real_dir = f"{output_dir}_real"
    
    # Check if real lyrics exist
    if not os.path.exists(real_dir):
        print(f"Error: Real lyrics directory '{real_dir}' not found.")
        print("Please run extract first.")
        return False
    
    # Backup current songs directory if it exists
    if os.path.exists(output_dir):
        backup_dir = f"{output_dir}_backup"
        print(f"Backing up '{output_dir}' to '{backup_dir}'...")
        
        # Remove old backup if it exists
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        
        # Create backup
        shutil.copytree(output_dir, backup_dir)
    
    # Clear output directory
    if os.path.exists(output_dir):
        print(f"Clearing '{output_dir}'...")
        shutil.rmtree(output_dir)
    
    # Copy real lyrics to output directory
    print(f"Copying real lyrics from '{real_dir}' to '{output_dir}'...")
    shutil.copytree(real_dir, output_dir)
    
    print(f"Now using real lyrics in '{output_dir}'")
    print("WARNING: Do not commit these files to a public repository.")
    
    # Create a .gitignore file to prevent accidental commits
    gitignore_path = os.path.join(output_dir, '.gitignore')
    with open(gitignore_path, 'w') as f:
        f.write("# REAL LYRICS - DO NOT COMMIT\n")
        f.write("*\n")  # Ignore everything in this directory
    
    return True

def use_placeholder_lyrics(output_dir, metadata_file):
    """Switch to using placeholder lyrics for public sharing."""
    # Backup current songs directory if it exists
    if os.path.exists(output_dir):
        backup_dir = f"{output_dir}_backup"
        print(f"Backing up '{output_dir}' to '{backup_dir}'...")
        
        # Remove old backup if it exists
        if os.path.exists(backup_dir):
            shutil.rmtree(backup_dir)
        
        # Create backup
        shutil.copytree(output_dir, backup_dir)
    
    # Clear output directory
    if os.path.exists(output_dir):
        print(f"Clearing '{output_dir}'...")
        shutil.rmtree(output_dir)
    
    # Create placeholder lyrics
    return create_placeholder_lyrics(output_dir, metadata_file)

def compress_lyrics_directory(songs_dir):
    """Compress all lyrics files in a directory with gzip."""
    # Count total files first to show progress
    total_files = 0
    for root, _, files in os.walk(songs_dir):
        for file in files:
            if file.endswith('.txt') and not file.endswith('.txt.gz'):
                total_files += 1
    
    print(f"Found {total_files} uncompressed text files.")
    
    if total_files == 0:
        print("No uncompressed .txt files found. Nothing to do.")
        return True
    
    print(f"Compressing {total_files} lyrics files...")
    
    # Process files with progress bar
    compressed_count = 0
    skipped_count = 0
    
    for root, _, files in tqdm(list(os.walk(songs_dir)), desc="Processing directories"):
        for file in files:
            if file.endswith('.txt') and not file.endswith('.txt.gz'):
                filepath = os.path.join(root, file)
                
                try:
                    # Read content
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Write compressed version
                    gzipped_filepath = f"{filepath}.gz"
                    with open(gzipped_filepath, 'wb') as f:
                        # Use a higher compression level (9 is highest)
                        with gzip.GzipFile(fileobj=f, mode='wb', compresslevel=9) as gz:
                            gz.write(content.encode('utf-8'))
                    
                    # Remove original file
                    os.remove(filepath)
                    compressed_count += 1
                    
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
                    skipped_count += 1
    
    # Print summary
    print("\nCompression complete!")
    print(f"Compressed: {compressed_count} files")
    print(f"Skipped due to errors: {skipped_count} files")
    
    # Test that we can read a compressed file
    if compressed_count > 0:
        # Find a compressed file for testing
        test_file = None
        for root, _, files in os.walk(songs_dir):
            for file in files:
                if file.endswith('.txt.gz'):
                    test_file = os.path.join(root, file)
                    break
            if test_file:
                break
        
        if test_file:
            print(f"\nTesting read access to compressed file: {test_file}")
            try:
                with gzip.open(test_file, 'rt', encoding='utf-8') as f:
                    content = f.read()
                    preview = content[:100] + "..." if len(content) > 100 else content
                    print(f"Successfully read {len(content)} characters from test file.")
                    print(f"Preview: {preview}")
            except Exception as e:
                print(f"Error reading test file: {e}")
    
    return True

def decompress_lyrics_directory(songs_dir):
    """Decompress all gzipped lyrics files in a directory."""
    # Count total files first to show progress
    total_files = 0
    for root, _, files in os.walk(songs_dir):
        for file in files:
            if file.endswith('.txt.gz'):
                total_files += 1
    
    print(f"Found {total_files} compressed text files.")
    
    if total_files == 0:
        print("No compressed .txt.gz files found. Nothing to do.")
        return True
    
    print(f"Decompressing {total_files} lyrics files...")
    
    # Process files with progress bar
    decompressed_count = 0
    skipped_count = 0
    
    for root, _, files in tqdm(list(os.walk(songs_dir)), desc="Processing directories"):
        for file in files:
            if file.endswith('.txt.gz'):
                filepath = os.path.join(root, file)
                
                try:
                    # Determine the output path (remove .gz extension)
                    output_path = filepath[:-3]  # Remove .gz
                    
                    # Read compressed content
                    with gzip.open(filepath, 'rt', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Write uncompressed version
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Remove compressed file
                    os.remove(filepath)
                    decompressed_count += 1
                    
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
                    skipped_count += 1
    
    # Print summary
    print("\nDecompression complete!")
    print(f"Decompressed: {decompressed_count} files")
    print(f"Skipped due to errors: {skipped_count} files")
    
    return True

def update_gitignore():
    """Update root .gitignore to prevent committing real lyrics."""
    gitignore_path = '.gitignore'
    
    # Read existing .gitignore if it exists
    existing_content = ""
    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            existing_content = f.read()
    
    # Check if our content is already in .gitignore
    if "songs.tar.gz" in existing_content:
        print(".gitignore already updated for lyrics management.")
        return
    
    # Add our content
    with open(gitignore_path, 'a') as f:
        f.write("\n# Lyrics management\n")
        f.write(DEFAULT_GITIGNORE_CONTENT)
    
    print("Updated .gitignore to prevent committing real lyrics.")

def check_status(output_dir):
    """Check current lyrics status (real vs placeholder)."""
    real_dir = f"{output_dir}_real"
    
    print("\n=== Lyrics Status ===")
    
    # Check if tarball exists
    tarball_exists = os.path.exists(DEFAULT_TARBALL)
    print(f"Tarball '{DEFAULT_TARBALL}': {'Found' if tarball_exists else 'Not found'}")
    
    # Check if real lyrics exist
    real_exists = os.path.exists(real_dir)
    if real_exists:
        real_count = sum(1 for _ in Path(real_dir).rglob('*.txt'))
        compressed_real_count = sum(1 for _ in Path(real_dir).rglob('*.txt.gz'))
        print(f"Real lyrics directory '{real_dir}': Found ({real_count} txt, {compressed_real_count} compressed)")
    else:
        print(f"Real lyrics directory '{real_dir}': Not found")
    
    # Check if output directory exists
    output_exists = os.path.exists(output_dir)
    if output_exists:
        output_count = sum(1 for _ in Path(output_dir).rglob('*.txt'))
        compressed_count = sum(1 for _ in Path(output_dir).rglob('*.txt.gz'))
        print(f"Lyrics directory '{output_dir}': Found ({output_count} txt, {compressed_count} compressed)")
        
        # Try to determine if real or placeholder
        is_real = False
        is_placeholder = False
        
        if output_count > 0 or compressed_count > 0:
            # Check a sample file
            sample_file = next((f for f in Path(output_dir).rglob('*.txt')), None)
            if not sample_file:
                sample_file = next((f for f in Path(output_dir).rglob('*.txt.gz')), None)
                
            if sample_file:
                try:
                    # Read the content appropriately based on file extension
                    if str(sample_file).endswith('.gz'):
                        with gzip.open(sample_file, 'rt', encoding='utf-8') as f:
                            content = f.read()
                    else:
                        with open(sample_file, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                    is_placeholder = "placeholder" in content.lower() or "copyright" in content.lower()
                    is_real = not is_placeholder
                except Exception:
                    print("Could not determine content type (error reading sample file)")
        
        if is_real:
            print("Current status: Using REAL lyrics (DO NOT COMMIT)")
        elif is_placeholder:
            print("Current status: Using PLACEHOLDER lyrics (safe for sharing)")
        else:
            print("Current status: Unknown (cannot determine if real or placeholder)")
    else:
        print(f"Lyrics directory '{output_dir}': Not found")
    
    print("===================\n")

def setup_wizard(output_dir, metadata_file, tarball_path):
    """Interactive setup wizard to guide users through the process."""
    # Show welcome message
    print("\n" + "=" * 60)
    print(" Song Lyrics Visualization Setup ".center(60, "="))
    print("=" * 60 + "\n")
    print("This wizard will help you set up the lyrics for the visualization.")
    print("It will check for real lyrics and allow you to choose between")
    print("using real lyrics or copyright-safe placeholders.")
    print("\nPress Enter to continue...")
    input()
    
    # Check current status
    print("\n" + "=" * 60)
    print(" Checking Current Status ".center(60, "="))
    print("=" * 60 + "\n")
    check_status(output_dir)
    print("\nPress Enter to continue...")
    input()
    
    # Check for tarball and extract if needed
    tarball_exists = os.path.exists(tarball_path)
    real_exists = os.path.exists(f"{output_dir}_real")
    
    if tarball_exists and not real_exists:
        print("\n" + "=" * 60)
        print(" Extracting Real Lyrics ".center(60, "="))
        print("=" * 60 + "\n")
        print(f"Found tarball at '{tarball_path}' - extracting real lyrics...")
        extract_real_lyrics(tarball_path, output_dir)
        print("\nPress Enter to continue...")
        input()
    
    # Let user choose mode
    print("\n" + "=" * 60)
    print(" Choose Lyrics Mode ".center(60, "="))
    print("=" * 60 + "\n")
    print("You can now choose which mode to use:")
    print("  1. Real Lyrics Mode (local use only, DO NOT commit to public repos)")
    print("  2. Placeholder Lyrics Mode (safe for sharing, copyright compliant)")
    
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        if choice in ['1', '2']:
            break
        print("Invalid choice. Please enter 1 or 2.")
    
    # Apply selected mode
    if choice == '1':
        if not os.path.exists(f"{output_dir}_real"):
            print(f"Error: Real lyrics directory '{output_dir}_real' not found.")
            print(f"Please ensure {tarball_path} exists and has been extracted.")
            return False
            
        print("\n" + "=" * 60)
        print(" Switching to Real Lyrics Mode ".center(60, "="))
        print("=" * 60 + "\n")
        print("WARNING: This mode is for local use only. Do not commit these files")
        print("to a public repository as it may violate copyright laws.")
        use_real_lyrics(output_dir)
    else:
        print("\n" + "=" * 60)
        print(" Switching to Placeholder Lyrics Mode ".center(60, "="))
        print("=" * 60 + "\n")
        print("This mode creates placeholder lyrics that are safe to share")
        print("and will not violate copyright laws.")
        use_placeholder_lyrics(output_dir, metadata_file)
    
    print("\nPress Enter to continue...")
    input()
    
    # Ask about compression
    print("\n" + "=" * 60)
    print(" Compression Options ".center(60, "="))
    print("=" * 60 + "\n")
    print("Would you like to compress the lyrics files to save disk space?")
    print("1. Yes, compress the lyrics files")
    print("2. No, keep as regular text files")
    
    while True:
        compression_choice = input("\nEnter your choice (1 or 2): ").strip()
        if compression_choice in ['1', '2']:
            break
        print("Invalid choice. Please enter 1 or 2.")
    
    if compression_choice == '1':
        print("\nCompressing lyrics files...")
        compress_lyrics_directory(output_dir)
    
    # Final status
    print("\n" + "=" * 60)
    print(" Setup Complete ".center(60, "="))
    print("=" * 60 + "\n")
    check_status(output_dir)
    
    print("\nSetup is complete! You can now run the visualization with:")
    print("  python src/prepare_data.py  # Generate data.json")
    print("  python web/server.py        # Start the visualization server")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='Manage lyrics for copyright compliance and organization')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Extract command
    extract_parser = subparsers.add_parser('extract', help='Extract real lyrics from tarball')
    extract_parser.add_argument('--tarball', type=str, default=DEFAULT_TARBALL,
                              help=f'Path to tarball (default: {DEFAULT_TARBALL})')
    extract_parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
                              help=f'Base output directory name (default: {DEFAULT_OUTPUT_DIR})')
    
    # Create placeholder command
    placeholder_parser = subparsers.add_parser('placeholder', help='Create placeholder lyrics')
    placeholder_parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
                                  help=f'Directory to save placeholders (default: {DEFAULT_OUTPUT_DIR})')
    placeholder_parser.add_argument('--metadata', type=str, default=DEFAULT_METADATA,
                                  help=f'Path to metadata CSV (default: {DEFAULT_METADATA})')
    
    # Use real lyrics command
    real_parser = subparsers.add_parser('use-real', help='Switch to using real lyrics')
    real_parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
                           help=f'Directory to use (default: {DEFAULT_OUTPUT_DIR})')
    
    # Use placeholder lyrics command
    use_placeholder_parser = subparsers.add_parser('use-placeholder', help='Switch to using placeholder lyrics')
    use_placeholder_parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
                                      help=f'Directory to use (default: {DEFAULT_OUTPUT_DIR})')
    use_placeholder_parser.add_argument('--metadata', type=str, default=DEFAULT_METADATA,
                                      help=f'Path to metadata CSV (default: {DEFAULT_METADATA})')
    
    # Compress command
    compress_parser = subparsers.add_parser('compress', help='Compress lyrics files to save space')
    compress_parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
                               help=f'Directory containing lyrics (default: {DEFAULT_OUTPUT_DIR})')
    
    # Decompress command
    decompress_parser = subparsers.add_parser('decompress', help='Decompress lyrics files to regular text')
    decompress_parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
                                 help=f'Directory containing lyrics (default: {DEFAULT_OUTPUT_DIR})')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check lyrics status')
    status_parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
                             help=f'Directory to check (default: {DEFAULT_OUTPUT_DIR})')
    
    # Setup wizard command
    setup_parser = subparsers.add_parser('setup', help='Run interactive setup wizard')
    setup_parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
                            help=f'Directory to use (default: {DEFAULT_OUTPUT_DIR})')
    setup_parser.add_argument('--metadata', type=str, default=DEFAULT_METADATA,
                            help=f'Path to metadata CSV (default: {DEFAULT_METADATA})')
    setup_parser.add_argument('--tarball', type=str, default=DEFAULT_TARBALL,
                            help=f'Path to tarball (default: {DEFAULT_TARBALL})')
    
    args = parser.parse_args()
    
    # Update .gitignore in all cases
    update_gitignore()
    
    # Run the appropriate command
    if args.command == 'extract':
        return extract_real_lyrics(args.tarball, args.output_dir)
        
    elif args.command == 'placeholder':
        return create_placeholder_lyrics(args.output_dir, args.metadata)
        
    elif args.command == 'use-real':
        return use_real_lyrics(args.output_dir)
        
    elif args.command == 'use-placeholder':
        return use_placeholder_lyrics(args.output_dir, args.metadata)
        
    elif args.command == 'compress':
        return compress_lyrics_directory(args.output_dir)
        
    elif args.command == 'decompress':
        return decompress_lyrics_directory(args.output_dir)
        
    elif args.command == 'status':
        check_status(args.output_dir)
        return True
        
    elif args.command == 'setup':
        return setup_wizard(args.output_dir, args.metadata, args.tarball)
        
    else:
        # If no command specified, show status and help
        check_status(DEFAULT_OUTPUT_DIR)
        parser.print_help()
        return True

if __name__ == "__main__":
    sys.exit(0 if main() else 1) 