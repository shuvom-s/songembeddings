# Song Lyrics Embeddings Visualization

This is a web application that visualizes song lyrics embeddings in a 2D space. The embeddings were created using OpenAI's text-embedding-3-small model and projected into 2D using DensMAP, a variant of UMAP that preserves both local and global structure.

## Features

- Interactive 2D visualization of song lyrics embeddings
- Hover over points to see song titles and artists
- Click on points to see detailed song information, including lyrics preview
- Filter by genre or artist to explore specific subsets of songs
- Songs are colored by genre to identify patterns in the embedding space
- Sparse Autoencoder (SAE) support for exploring neuron activations (optional)
- Support for compressed lyrics files to save disk space
- Copyright-compliant lyrics management system

## Directory Structure

```
.
├── README.md                       # This file
├── data/                           # Data directory
│   ├── embeddings/                 # Embedding files
│   │   ├── liked_songs_embeddings_openai-small.npy     # Raw embeddings
│   │   └── liked_songs_with_lyrics_openai-small.csv    # Song metadata
│   └── songs.tar.gz                # Archived real lyrics (not distributed)
├── songs/                          # Lyrics directory (real or placeholder)
├── src/                            # Source code
│   ├── lyrics_manager.py           # Combined lyrics management tool
│   ├── lyrics_utils.py             # Utilities for lyrics handling
│   ├── prepare_data.py             # Data preparation for visualization
│   └── sparse_autoencoder.py       # SAE implementation
└── web/                            # Web visualization
    ├── data.json                   # Generated visualization data
    ├── index.html                  # HTML template
    ├── server.py                   # Simple web server
    ├── scripts.js                  # JavaScript for visualization
    └── styles.css                  # CSS styles
```

## Setup & Running

### Prerequisites

- Python 3.6+
- Required Python packages: numpy, pandas, umap-learn, scikit-learn, gzip, tqdm

### Setup

1. Install the required packages:
   ```
   pip install numpy pandas umap-learn scikit-learn tqdm
   ```

2. Set up lyrics (choose one option):
   ```
   # Option A: Use placeholder lyrics (safe for sharing/copyright compliant)
   python src/lyrics_manager.py use-placeholder
   
   # Option B: Extract and use real lyrics from tarball (for local use only)
   python src/lyrics_manager.py extract
   python src/lyrics_manager.py use-real
   
   # Interactive setup wizard (recommended for first-time setup)
   python src/lyrics_manager.py setup
   ```

3. Prepare the data for visualization:
   ```
   python src/prepare_data.py
   ```
   This will generate a `web/data.json` file that contains the song metadata and 2D embeddings.

4. Serve the website:
   ```
   python web/server.py
   ```
   This will start a server at http://localhost:8000/ and open the visualization in your browser.

## Lyrics Management

### Copyright Considerations

Song lyrics are protected by copyright, and distributing them without permission could infringe on copyright holders' rights. To address this, we've implemented a system that:

1. Allows you to use real lyrics locally for development and personal use
2. Prevents sharing or distributing copyrighted lyrics when sharing the codebase
3. Keeps the application functional even when actual lyrics aren't included

### Real vs. Placeholder Lyrics

The system lets you switch between two modes:

1. **Real Lyrics Mode**: Uses actual song lyrics from your `data/songs.tar.gz` archive (for local use only)
2. **Placeholder Lyrics Mode**: Creates placeholder text files that maintain the same structure but don't contain actual copyrighted content (safe for sharing)

### Lyrics Manager Tool

The `src/lyrics_manager.py` script provides all functionality for managing lyrics:

```bash
# Check current status
python src/lyrics_manager.py status

# Extract lyrics from tarball
python src/lyrics_manager.py extract

# Switch to real lyrics (local use only)
python src/lyrics_manager.py use-real

# Switch to placeholder lyrics (before committing/sharing)
python src/lyrics_manager.py use-placeholder

# Compress lyrics to save space
python src/lyrics_manager.py compress

# Decompress lyrics
python src/lyrics_manager.py decompress

# Run interactive setup wizard
python src/lyrics_manager.py setup
```

### Example Workflow

Here's a typical workflow:

1. **Initial Setup**:
   ```bash
   # Run the setup wizard for guided setup
   python src/lyrics_manager.py setup
   
   # Generate visualization data
   python src/prepare_data.py
   
   # Start the server
   python web/server.py
   ```

2. **Before Sharing/Committing**:
   ```bash
   # Switch to placeholder lyrics
   python src/lyrics_manager.py use-placeholder
   
   # Check that we're using placeholders
   python src/lyrics_manager.py status
   
   # Now safe to commit
   git add .
   git commit -m "Update with placeholder lyrics"
   git push
   ```

3. **After Pulling on Another Machine**:
   ```bash
   # Extract your local tarball
   python src/lyrics_manager.py extract
   
   # Switch to real lyrics if desired
   python src/lyrics_manager.py use-real
   ```

## Compression Features

To save disk space, lyrics files can be compressed using gzip. The compression functionality is integrated into the lyrics manager:

```bash
# Compress lyrics files
python src/lyrics_manager.py compress

# Decompress lyrics files
python src/lyrics_manager.py decompress
```

All scripts automatically handle both compressed (`.txt.gz`) and uncompressed (`.txt`) lyrics files.

## Sparse Autoencoder (SAE) Features

The visualization includes optional support for exploring lyrics with a Sparse Autoencoder (SAE). If you have an SAE model, you can include it when preparing the data:

```bash
python src/prepare_data.py --sae-model models/sparse_autoencoder/model.pth
```

This will add SAE controls to the visualization interface, allowing you to:
- Select specific neurons to highlight songs that activate them
- See the top songs for each neuron
- Adjust activation thresholds to focus on strongly activating songs

To train a new SAE model, you can use the `create_sae.py` script (not included in the clean directory structure).

## How It Works

1. **Data Loading**: The embedding and metadata files are loaded and processed.
2. **Dimensionality Reduction**: The high-dimensional embeddings (1536 dimensions) are reduced to 2D using DensMAP.
3. **Visualization**: The 2D coordinates are used to create an interactive scatterplot, with each point representing a song.
4. **Filtering**: Users can filter the visualization by genre or artist to explore specific subsets of songs.
5. **Lyrics Access**: The system can read lyrics from both compressed and uncompressed files as needed.
6. **Copyright Management**: The system works with either real or placeholder lyrics through the lyrics manager.

## Implementation Details

- **Frontend**: HTML, CSS, JavaScript with Plotly.js for visualization
- **Data Processing**: Python with numpy, pandas, and umap-learn
- **Lyrics Storage**: Support for both plain text and gzip compressed files
- **Static Website**: No backend required, all data is loaded at startup
- **Copyright Compliance**: Tools for managing real vs. placeholder lyrics

## Legal Considerations

This approach helps you comply with copyright law while still being able to use your visualization tool, but please note:

1. Even when using real lyrics locally, you should ensure your use is personal and non-commercial
2. Different countries have different copyright laws
3. If you're uncertain about legal implications, consult with a legal professional

## Troubleshooting

- **Missing data.json**: Run `python src/prepare_data.py` to generate it
- **Port conflict**: Specify a different port with `python web/server.py 8080`
- **Module import errors**: Make sure you're running commands from the project root directory
- **Tarball extraction issues**: Check that `data/songs.tar.gz` exists and is a valid tar.gz archive 