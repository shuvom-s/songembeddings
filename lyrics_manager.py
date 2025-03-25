#!/usr/bin/env python3
"""
Lyrics Manager - A tool to manage real vs placeholder lyrics for copyright compliance.

This script provides utilities to:
1. Extract real lyrics from a tarball for local development
2. Create placeholder lyrics for public sharing
3. Switch between real and placeholder lyrics as needed
4. Update the application to work with either set
"""

import os
import sys
import argparse
import tarfile
import shutil
import subprocess
from pathlib import Path

# Constants
DEFAULT_TARBALL = 'songs.tar.gz'
DEFAULT_OUTPUT_DIR = 'songs'
DEFAULT_METADATA = 'embeddings/liked_songs_with_lyrics_openai-small.csv'
DEFAULT_PLACEHOLDER_SCRIPT = 'lyrics_placeholder.py'
DEFAULT_GITIGNORE_CONTENT = """# Ignore actual lyrics files if they exist
*.tar.gz
*.gz
# Ignore extracted songs from tarball
/songs_real/
# Add other patterns as needed
"""

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
    # Check if placeholder script exists
    if not os.path.exists(DEFAULT_PLACEHOLDER_SCRIPT):
        print(f"Error: Placeholder script '{DEFAULT_PLACEHOLDER_SCRIPT}' not found.")
        return False
    
    # Run placeholder script
    print("Creating placeholder lyrics...")
    try:
        result = subprocess.run([
            sys.executable, DEFAULT_PLACEHOLDER_SCRIPT,
            '--output-dir', output_dir,
            '--metadata', metadata_file
        ])
        return result.returncode == 0
    except Exception as e:
        print(f"Error running placeholder script: {e}")
        return False

def use_real_lyrics(real_dir, output_dir):
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
    # Check if placeholder script exists
    if not os.path.exists(DEFAULT_PLACEHOLDER_SCRIPT):
        print(f"Error: Placeholder script '{DEFAULT_PLACEHOLDER_SCRIPT}' not found.")
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
    
    # Create placeholder lyrics
    return create_placeholder_lyrics(output_dir, metadata_file)

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
        print(f"Real lyrics directory '{real_dir}': Found ({real_count} files)")
    else:
        print(f"Real lyrics directory '{real_dir}': Not found")
    
    # Check if output directory exists
    output_exists = os.path.exists(output_dir)
    if output_exists:
        output_count = sum(1 for _ in Path(output_dir).rglob('*.txt'))
        print(f"Lyrics directory '{output_dir}': Found ({output_count} files)")
        
        # Try to determine if real or placeholder
        is_real = False
        is_placeholder = False
        
        if output_count > 0:
            # Check a sample file
            sample_file = next(Path(output_dir).rglob('*.txt'), None)
            if sample_file:
                with open(sample_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    is_placeholder = "placeholder" in content.lower() or "copyright" in content.lower()
                    is_real = not is_placeholder
        
        if is_real:
            print("Current status: Using REAL lyrics (DO NOT COMMIT)")
        elif is_placeholder:
            print("Current status: Using PLACEHOLDER lyrics (safe for sharing)")
        else:
            print("Current status: Unknown (cannot determine if real or placeholder)")
    else:
        print(f"Lyrics directory '{output_dir}': Not found")
    
    print("===================\n")

def main():
    parser = argparse.ArgumentParser(description='Manage lyrics for copyright compliance')
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
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Check lyrics status')
    status_parser.add_argument('--output-dir', type=str, default=DEFAULT_OUTPUT_DIR,
                             help=f'Directory to check (default: {DEFAULT_OUTPUT_DIR})')
    
    args = parser.parse_args()
    
    # Update .gitignore in all cases
    update_gitignore()
    
    # Run the appropriate command
    if args.command == 'extract':
        extract_real_lyrics(args.tarball, args.output_dir)
        
    elif args.command == 'placeholder':
        create_placeholder_lyrics(args.output_dir, args.metadata)
        
    elif args.command == 'use-real':
        use_real_lyrics(f"{args.output_dir}_real", args.output_dir)
        
    elif args.command == 'use-placeholder':
        use_placeholder_lyrics(args.output_dir, args.metadata)
        
    elif args.command == 'status':
        check_status(args.output_dir)
        
    else:
        # If no command specified, show status and help
        check_status(DEFAULT_OUTPUT_DIR)
        parser.print_help()
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 