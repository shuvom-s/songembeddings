# Project Cleanup Plan

## Files to Remove
- `extract_songs.py` (functionality merged into lyrics_manager.py)
- `COMPRESSION_README.md` (will be consolidated into main README)
- `setup_lyrics.py` (simplify to a single command in lyrics_manager.py)
- `full_scraper.ipynb` (redundant with full_scraper.py)
- `genius_scraper.ipynb` (can be deleted if not needed)
- `stock_simulation.ipynb` (unrelated to the project)
- `songs.txt` (redundant with songs.tar.gz)
- `__pycache__/` (generated files)
- `website/` (empty directory)
- `.git/` (keep, but not part of cleanup)

## Files to Consolidate
- Consolidate `LYRICS_COPYRIGHT_README.md` into `README.md`
- Merge `compress_songs.py` functionality into `lyrics_manager.py`
- Keep `lyrics_utils.py` as a core module but simplify

## Directories to Clean
- `embeddings/`: Keep only the latest embeddings files (liked_songs_*)
- `models/`: Keep only necessary SAE models
- `wandb/`: Can be removed if not needed for tracking

## Files to Retain (Core Functionality)
- `README.md` (updated with all consolidated information)
- `lyrics_manager.py` (updated with merged functionality)
- `lyrics_utils.py` (core utility module)
- `prepare_data.py` (essential for visualization)
- `server.py` (needed to run the application)
- `index.html`, `styles.css`, `scripts.js` (frontend)
- `data.json` (visualization data)
- `sparse_autoencoder.py` (for SAE features)
- `songs.tar.gz` (real lyrics data)

## Organization Structure
```
lyrics/
├── README.md                 # Main documentation with all information
├── data/                     # Data directory
│   ├── embeddings/           # Embedding files
│   └── songs.tar.gz          # Archived real lyrics
├── models/                   # Model files for SAE
├── src/                      # Source code
│   ├── lyrics_manager.py     # Combined lyrics management (extraction, placeholder, compression)
│   ├── lyrics_utils.py       # Utilities for lyrics handling
│   ├── prepare_data.py       # Data preparation for visualization
│   └── sparse_autoencoder.py # SAE implementation
└── web/                      # Web visualization
    ├── index.html            # HTML template
    ├── styles.css            # CSS styles
    ├── scripts.js            # JavaScript for visualization
    └── server.py             # Simple web server
``` 