# %%
import pandas as pd
import random
import re
import os
import time
import json
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Import our lyrics utilities
import lyrics_utils

# Read the country songs CSV file
# df = pd.read_csv('songs/country.csv')
df = pd.read_csv('songs/liked_songs.csv')

def generate_genius_url(artist, track):
    """Generate a URL for Genius lyrics page."""
    # Split artist string on comma and take first artist only
    primary_artist = artist.split(',')[0].strip()
    return f"https://genius.com/{lyrics_utils.slugify(primary_artist)}-{lyrics_utils.slugify(track)}-lyrics"

def get_lyrics(url):
    """Fetch lyrics from a Genius URL."""
    headers = {
        'User-Agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/90.0.4430.93 Safari/537.36')
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            lyric_containers = soup.find_all("div", attrs={"data-lyrics-container": "true"})
            if not lyric_containers:
                print("Could not locate the lyrics container. The page structure may have changed.")
                return None
            lyrics = "\n".join([container.get_text(separator="\n").strip() for container in lyric_containers])
            return lyrics
        else:
            print("Error fetching the page:", response.status_code)
            return None
    except Exception as e:
        print(f"Exception during request: {e}")
        return None

def main():
    """Main function to scrape lyrics for all songs in the dataframe."""
    # Print some info to confirm the utility module is working
    print(f"Using lyrics_utils module - saving compressed lyrics by default")
    
    # Keep track of failed songs
    failed_songs = []
    
    # Process all songs in the dataframe
    for i in tqdm(range(0, len(df)), desc="Downloading lyrics", unit="song"):
        # Get artist and track
        artist_full = str(df.iloc[i]['Artist Name(s)'])
        artist = artist_full.split(',')[0].strip()  # Get primary artist
        
        # Skip rows with NaN artist
        if artist == 'nan':
            print("Skipping NaN artist")
            continue
            
        track = df.iloc[i]['Track Name']
        url = generate_genius_url(artist, track)
        
        print(f"URL: {url}")
        
        # Check if lyrics already exist (either compressed or uncompressed)
        if lyrics_utils.lyrics_exists(artist, track):
            print(f"Lyrics for {artist} - {track} already exist. Skipping.")
            continue
        
        # Get lyrics from Genius
        lyrics = get_lyrics(url)
        if lyrics:
            # Save lyrics - compressed by default
            lyrics_utils.save_lyrics(lyrics, artist, track, compress=True)
        else:
            print("Failed to get lyrics")
            failed_songs.append({
                'artist': artist,
                'track': track,
                'url': url
            })
            
        # Add delay between requests to be polite
        time.sleep(10 + random.randint(0, 10))
    
    # Save failed songs to JSON file
    failed_songs_file = os.path.join('songs', 'failed_liked_songs.json')
    with open(failed_songs_file, 'w') as f:
        json.dump(failed_songs, f, indent=4)
    print(f"\nSaved {len(failed_songs)} failed songs to {failed_songs_file}")

if __name__ == "__main__":
    main()


# %%



