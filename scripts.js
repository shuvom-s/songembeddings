// Global variables
let visualizationData = null;
let filteredSongs = [];
let currentPlot = null;
let currentNeuron = -1;
let activationThreshold = 0.2;
let currentNeuronData = null;
let allNeuronSongs = null;
let originalSongs = []; // Store original songs for proper reset

// Color palette for different genres
const genreColors = {
    'hip hop': '#FF5733',
    'rap': '#C70039',
    'r&b': '#900C3F',
    'pop': '#FFC300',
    'country': '#5DADE2',
    'rock': '#2E4053',
    'electronic': '#58D68D',
    'dance': '#F1C40F',
    'trap': '#E74C3C',
    'punk': '#9B59B6',
    'metal': '#7D3C98',
    'folk': '#1ABC9C',
    'indie': '#3498DB',
    'soul': '#E67E22',
    'jazz': '#D35400',
    'blues': '#2980B9',
    'reggae': '#27AE60',
    'alternative rock': '#8E44AD',
    'post-punk': '#34495E',
    'progressive rock': '#16A085',
    'grunge': '#2C3E50',
    'hard rock': '#E74C3C'
};

// Default color for genres not in the palette
const defaultColor = '#95A5A6';

// Base color for neuron activations (blue)
const neuronBaseColor = '#3498DB';
// Color for non-activated points when showing neuron activations (gray)
const nonActivatedColor = '#E0E0E0';

// Function to get color based on genres
function getColor(genres) {
    if (!genres || genres.length === 0) {
        return defaultColor;
    }
    
    // Try to find a color for the first genre that has a predefined color
    for (const genre of genres) {
        const genreLower = genre.trim().toLowerCase();
        for (const [key, value] of Object.entries(genreColors)) {
            if (genreLower.includes(key)) {
                return value;
            }
        }
    }
    
    // If no matching genre found, return default color
    return defaultColor;
}

// Load data and initialize the visualization
document.addEventListener('DOMContentLoaded', function() {
    console.log("Document loaded, initializing visualization...");
    fetch('data.json')
        .then(response => {
            if (!response.ok) {
                throw new Error(`Network response was not ok: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Data loaded successfully");
            visualizationData = data;
            
            // Create a deep copy of the songs for safe reset functionality
            console.log(`Found ${data.songs.length} songs in the dataset`);
            
            try {
                originalSongs = JSON.parse(JSON.stringify(data.songs));
                filteredSongs = JSON.parse(JSON.stringify(data.songs));
                console.log("Successfully copied original song data");
            } catch (error) {
                console.error("Error creating deep copy of songs:", error);
                // Fallback to array spread (less safe but better than nothing)
                originalSongs = [...data.songs];
                filteredSongs = [...data.songs];
            }
            
            // Initialize filter selections
            initializeFilters();
            
            // Initialize SAE features if available
            if (visualizationData.sae) {
                console.log("SAE data found, initializing SAE controls");
                initializeSAEControls();
                prepareAllNeuronSongs();
            }
            
            // Create initial visualization
            createVisualization();
            
            // Add event listeners for filter buttons
            document.getElementById('apply-filters').addEventListener('click', filterData);
            
            // Add a direct event listener for reset button to ensure it's properly connected
            const resetButton = document.getElementById('reset-filters');
            resetButton.addEventListener('click', function(event) {
                console.log("Reset button clicked");
                resetFilters();
                event.preventDefault(); // Prevent any default form submission
            });

            // Add event listener for "View All Top Songs" button
            const viewMoreButton = document.getElementById('view-more-songs');
            if (viewMoreButton) {
                viewMoreButton.addEventListener('click', showNeuronSongsModal);
            }
            
            console.log(`Visualization initialized with ${filteredSongs.length} songs.`);
        })
        .catch(error => {
            console.error('Error loading the data:', error);
            document.getElementById('embedding-plot').innerHTML = 
                '<div class="alert alert-danger">Error loading data. Please check the console for details.</div>';
        });
});

// Process and prepare all neuron songs data for later use
function prepareAllNeuronSongs() {
    if (!visualizationData.sae) return;
    
    allNeuronSongs = [];
    
    // For each neuron, calculate the top songs based on activation values
    for (let neuronIdx = 0; neuronIdx < visualizationData.sae.neurons.length; neuronIdx++) {
        // Create an array of [songIndex, activationValue] pairs
        const songActivations = visualizationData.sae.activations.map((activations, songIndex) => [songIndex, activations[neuronIdx]]);
        
        // Sort by activation value (descending)
        songActivations.sort((a, b) => b[1] - a[1]);
        
        // Take the top 10 songs
        const topSongs = songActivations.slice(0, 10).map(([songIndex, activation]) => {
            const song = visualizationData.songs[songIndex];
            return {
                index: songIndex,
                title: song.title,
                artist: song.artist,
                activation: activation
            };
        });
        
        allNeuronSongs[neuronIdx] = topSongs;
    }
}

// Initialize filter options
function initializeFilters() {
    const genreFilter = document.getElementById('genre-filter');
    const artistFilter = document.getElementById('artist-filter');
    
    // Add genre options with counts
    visualizationData.filters.genres.forEach(([genre, count]) => {
        const option = document.createElement('option');
        option.value = genre;
        option.textContent = `${genre} (${count})`;
        genreFilter.appendChild(option);
    });
    
    // Add artist options with counts
    visualizationData.filters.artists.forEach(([artist, count]) => {
        const option = document.createElement('option');
        option.value = artist;
        option.textContent = `${artist} (${count})`;
        artistFilter.appendChild(option);
    });
}

// Initialize SAE controls if SAE data is available
function initializeSAEControls() {
    // Show SAE controls
    document.getElementById('sae-controls').style.display = 'block';
    document.getElementById('sae-description').style.display = 'block';
    
    const neuronFilter = document.getElementById('neuron-filter');
    const thresholdSlider = document.getElementById('threshold-slider');
    
    // Add neuron options
    const numNeurons = visualizationData.sae.neurons.length;
    for (let i = 0; i < numNeurons; i++) {
        const option = document.createElement('option');
        option.value = i;
        option.textContent = `Neuron ${i}`;
        neuronFilter.appendChild(option);
    }
    
    // Add event listeners
    neuronFilter.addEventListener('change', function() {
        currentNeuron = parseInt(this.value);
        currentNeuronData = currentNeuron >= 0 ? visualizationData.sae.neurons[currentNeuron] : null;
        
        // Show or hide the "View All Top Songs" button
        document.getElementById('view-more-songs').style.display = currentNeuron >= 0 ? 'block' : 'none';
        
        updateNeuronInfo();
        createVisualization();
    });
    
    thresholdSlider.addEventListener('input', function() {
        activationThreshold = parseFloat(this.value);
        document.getElementById('threshold-value').textContent = activationThreshold.toFixed(2);
        if (currentNeuron >= 0) {
            createVisualization();
        }
    });
}

// Update the displayed information about the selected neuron
function updateNeuronInfo() {
    const neuronTopSongsElement = document.getElementById('neuron-top-songs');
    const viewMoreButton = document.getElementById('view-more-songs');
    
    if (currentNeuron < 0) {
        neuronTopSongsElement.innerHTML = '<p class="text-muted">Select a neuron to see its top activations</p>';
        viewMoreButton.style.display = 'none';
        return;
    }
    
    viewMoreButton.style.display = 'block';
    
    const neuronData = visualizationData.sae.neurons[currentNeuron];
    let html = '<ol class="mb-0">';
    
    // Show top 5 songs in the main UI
    neuronData.top_songs.forEach(song => {
        html += `<li>
            <strong>${song.title}</strong> - ${song.artist}
            <div class="activation-bar-container">
                <div class="activation-bar" style="width: ${Math.min(100, song.activation * 100)}%;"></div>
                <span class="activation-value">${song.activation.toFixed(3)}</span>
            </div>
        </li>`;
    });
    
    html += '</ol>';
    neuronTopSongsElement.innerHTML = html;
}

// Show the modal with top songs for the current neuron
function showNeuronSongsModal() {
    if (currentNeuron < 0 || !allNeuronSongs) return;
    
    // Set the modal title
    document.getElementById('neuron-songs-modal-label').textContent = `Top Songs for Neuron ${currentNeuron}`;
    
    // Get the top songs for this neuron
    const topSongs = allNeuronSongs[currentNeuron];
    
    // Generate info about this neuron
    const modalNeuronInfo = document.getElementById('modal-neuron-info');
    modalNeuronInfo.innerHTML = `
        <p>This neuron appears to respond to songs with similar lyrical themes or patterns. 
        The songs below have the highest activation values for Neuron ${currentNeuron}.</p>
    `;
    
    // Generate the table rows
    const songsTable = document.getElementById('modal-songs-table');
    songsTable.innerHTML = '';
    
    topSongs.forEach((song, index) => {
        const row = document.createElement('tr');
        
        // Calculate relative activation for visualization (as percentage of highest activation)
        const maxActivation = topSongs[0].activation;
        const relativeActivation = (song.activation / maxActivation) * 100;
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>${song.title}</td>
            <td>${song.artist}</td>
            <td>
                <div class="activation-bar-container">
                    <div class="activation-bar" style="width: ${relativeActivation}%;"></div>
                    <span class="activation-value">${song.activation.toFixed(4)}</span>
                </div>
            </td>
            <td>
                <button class="btn btn-sm btn-primary show-song-details" data-song-index="${song.index}">
                    View Details
                </button>
            </td>
        `;
        
        songsTable.appendChild(row);
    });
    
    // Add event listeners to the "View Details" buttons
    document.querySelectorAll('.show-song-details').forEach(button => {
        button.addEventListener('click', function() {
            const songIndex = parseInt(this.getAttribute('data-song-index'));
            displaySongDetails(visualizationData.songs[songIndex]);
            
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('neuron-songs-modal'));
            modal.hide();
        });
    });
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('neuron-songs-modal'));
    modal.show();
}

// Reset all filters
function resetFilters() {
    console.log("Reset filters called - reloading initial state");
    
    // Simple but effective approach: reload the page data and reinitialize
    if (visualizationData) {
        // Clear the current plot to force a full redraw
        const embeddingPlot = document.getElementById('embedding-plot');
        embeddingPlot.innerHTML = '';
        currentPlot = null;
        
        // Reset filters to initial state
        const genreFilter = document.getElementById('genre-filter');
        const artistFilter = document.getElementById('artist-filter');
        
        // Select only "All" options
        for (let i = 0; i < genreFilter.options.length; i++) {
            genreFilter.options[i].selected = (i === 0);
        }
        
        for (let i = 0; i < artistFilter.options.length; i++) {
            artistFilter.options[i].selected = (i === 0);
        }
        
        // Reset neuron filter if it exists
        if (document.getElementById('neuron-filter')) {
            document.getElementById('neuron-filter').value = -1;
            currentNeuron = -1;
            currentNeuronData = null;
            
            // Reset neuron UI elements
            if (document.getElementById('view-more-songs')) {
                document.getElementById('view-more-songs').style.display = 'none';
            }
            
            if (document.getElementById('neuron-top-songs')) {
                document.getElementById('neuron-top-songs').innerHTML = 
                    '<p class="text-muted">Select a neuron to see its top activations</p>';
            }
            
            // Reset activation threshold
            activationThreshold = 0.2;
            if (document.getElementById('threshold-slider')) {
                document.getElementById('threshold-slider').value = 0.2;
                document.getElementById('threshold-value').textContent = '0.20';
            }
        }
        
        // Restore all songs from our backup
        filteredSongs = JSON.parse(JSON.stringify(originalSongs));
        
        // Re-create visualization
        createVisualization();
        
        console.log(`Reset complete. Showing all ${filteredSongs.length} songs.`);
    }
}

// Helper to get multiple selected values from a select element
function getSelectedValues(selectElement) {
    const result = [];
    const options = selectElement && selectElement.options;
    
    if (!options) return result;
    
    for (let i = 0; i < options.length; i++) {
        if (options[i].selected) {
            result.push(options[i].value);
        }
    }
    
    return result;
}

// Filter data based on selected filters
function filterData() {
    console.log("Filtering data...");
    
    // Get all selected genres and artists
    const selectedGenres = getSelectedValues(document.getElementById('genre-filter'));
    const selectedArtists = getSelectedValues(document.getElementById('artist-filter'));
    
    console.log("Selected genres:", selectedGenres);
    console.log("Selected artists:", selectedArtists);
    
    // Check if "All" is selected or no selection
    const includeAllGenres = selectedGenres.includes('all') || selectedGenres.length === 0;
    const includeAllArtists = selectedArtists.includes('all') || selectedArtists.length === 0;
    
    console.log("Include all genres:", includeAllGenres);
    console.log("Include all artists:", includeAllArtists);
    
    // If both "All" options are selected, just reset to all songs
    if (includeAllGenres && includeAllArtists) {
        filteredSongs = JSON.parse(JSON.stringify(originalSongs));
        console.log(`Using all ${filteredSongs.length} songs (no filters active)`);
        
        // Force recreation of the plot
        currentPlot = null;
        const embeddingPlot = document.getElementById('embedding-plot');
        embeddingPlot.innerHTML = '';
        
        createVisualization();
        return;
    }
    
    // Apply filters
    const previousLength = filteredSongs.length;
    
    // Start with all original songs and apply filters
    const allSongs = JSON.parse(JSON.stringify(originalSongs));
    
    filteredSongs = allSongs.filter(song => {
        // Genre filter logic
        let genreMatch = includeAllGenres;
        
        // If not including all genres, check if any selected genre matches any of the song's genres
        if (!includeAllGenres && song.genres) {
            for (const songGenre of song.genres) {
                if (selectedGenres.includes(songGenre)) {
                    genreMatch = true;
                    break;
                }
            }
        }
        
        // Artist filter logic
        let artistMatch = includeAllArtists;
        
        // If not including all artists, check if the primary artist matches any selected artist
        if (!includeAllArtists) {
            artistMatch = selectedArtists.includes(song.primary_artist);
        }
        
        return genreMatch && artistMatch;
    });
    
    console.log(`Filtered to ${filteredSongs.length} songs (from ${allSongs.length} total)`);
    
    // If no songs match, show a message
    if (filteredSongs.length === 0) {
        const embeddingPlot = document.getElementById('embedding-plot');
        embeddingPlot.innerHTML = `
            <div class="alert alert-warning">
                <strong>No songs match the selected filters.</strong> 
                <p>Try selecting different genres or artists, or click "Reset Filters" to see all songs.</p>
            </div>
        `;
        // Hide the legend when there are no songs
        document.getElementById('legend-container').style.display = 'none';
    } else {
        // Force recreation of the plot
        currentPlot = null;
        const embeddingPlot = document.getElementById('embedding-plot');
        embeddingPlot.innerHTML = '';
        
        createVisualization();
    }
}

// Create legend for genre colors
function createGenreLegend() {
    const legendContainer = document.getElementById('genre-legend');
    legendContainer.innerHTML = '';  // Clear any existing content
    
    // Create entries for each genre that appears in the data
    const usedGenres = new Set();
    
    // If showing neuron activations, use a different legend
    if (currentNeuron >= 0 && visualizationData.sae) {
        // Create legend for neuron activation colors
        const highActivationEntry = document.createElement('div');
        highActivationEntry.className = 'legend-entry';
        highActivationEntry.innerHTML = `
            <span class="legend-color" style="background-color: ${neuronBaseColor};"></span>
            <span class="legend-label">High Activation</span>
        `;
        
        const lowActivationEntry = document.createElement('div');
        lowActivationEntry.className = 'legend-entry';
        lowActivationEntry.innerHTML = `
            <span class="legend-color" style="background-color: ${nonActivatedColor};"></span>
            <span class="legend-label">Low/No Activation</span>
        `;
        
        legendContainer.appendChild(highActivationEntry);
        legendContainer.appendChild(lowActivationEntry);
        
        // Show the legend
        document.getElementById('legend-container').style.display = 'block';
        return;
    }
    
    // Collect genres that actually appear in the filtered data
    filteredSongs.forEach(song => {
        if (song.genres && song.genres.length > 0) {
            // Find the first genre that has a predefined color
            for (const genre of song.genres) {
                const genreLower = genre.trim().toLowerCase();
                for (const key of Object.keys(genreColors)) {
                    if (genreLower.includes(key) && !usedGenres.has(key)) {
                        usedGenres.add(key);
                        break;
                    }
                }
            }
        }
    });
    
    // Add legend entries for used genres
    Array.from(usedGenres).sort().forEach(genre => {
        const entry = document.createElement('div');
        entry.className = 'legend-entry';
        entry.innerHTML = `
            <span class="legend-color" style="background-color: ${genreColors[genre]};"></span>
            <span class="legend-label">${genre.charAt(0).toUpperCase() + genre.slice(1)}</span>
        `;
        legendContainer.appendChild(entry);
    });
    
    // Add entry for Other/Unknown
    const otherEntry = document.createElement('div');
    otherEntry.className = 'legend-entry';
    otherEntry.innerHTML = `
        <span class="legend-color" style="background-color: ${defaultColor};"></span>
        <span class="legend-label">Other/Unknown</span>
    `;
    legendContainer.appendChild(otherEntry);
    
    // Show the legend
    document.getElementById('legend-container').style.display = 'block';
}

// Create the visualization with filtered data
function createVisualization() {
    console.log(`Creating visualization with ${filteredSongs ? filteredSongs.length : 0} songs`);
    const embeddingPlot = document.getElementById('embedding-plot');
    
    // Safety check for empty data
    if (!filteredSongs || filteredSongs.length === 0) {
        embeddingPlot.innerHTML = '<div class="alert alert-info">No songs match the current filters. Click "Reset Filters" to restore all songs.</div>';
        // Hide the legend when there are no songs
        document.getElementById('legend-container').style.display = 'none';
        return;
    }
    
    // Prepare data for the plot
    let plotData = [];
    
    try {
        plotData = filteredSongs.map((song, index) => {
            // Make sure the song has valid embeddings
            if (!visualizationData.embeddings[song.id]) {
                console.warn(`Missing embedding for song ID ${song.id}: "${song.title}"`);
                return null;
            }
            
            const embedXY = visualizationData.embeddings[song.id];
            let color, opacity, size;
            
            // If a neuron is selected, color points based on activation
            if (currentNeuron >= 0 && visualizationData.sae) {
                const activation = visualizationData.sae.activations[song.id][currentNeuron];
                
                // If activation is above threshold, color by intensity
                if (activation >= activationThreshold) {
                    // Scale color based on activation (higher activation = more intense color)
                    const intensity = Math.min(1, activation);
                    color = neuronBaseColor;
                    opacity = 0.4 + (0.6 * intensity);
                    size = 8 + (8 * intensity);
                } else {
                    // Non-activated points are gray and smaller
                    color = nonActivatedColor;
                    opacity = 0.3;
                    size = 6;
                }
            } else {
                // Default coloring by genre
                color = getColor(song.genres);
                opacity = 0.8;
                size = 8;
            }
            
            return {
                x: embedXY[0],
                y: embedXY[1],
                text: `${song.title} - ${song.primary_artist}`,
                marker: {
                    color: color,
                    size: size,
                    opacity: opacity
                },
                songIndex: index,
                activation: currentNeuron >= 0 && visualizationData.sae ? 
                            visualizationData.sae.activations[song.id][currentNeuron] : 0
            };
        }).filter(item => item !== null); // Remove any null items
        
        // Make sure we still have valid data after filtering nulls
        if (plotData.length === 0) {
            throw new Error("No valid plot data after filtering");
        }
    } catch (error) {
        console.error("Error preparing plot data:", error);
        embeddingPlot.innerHTML = '<div class="alert alert-danger">Error preparing plot data. Check console for details.</div>';
        document.getElementById('legend-container').style.display = 'none';
        return;
    }
    
    // Extract x and y coordinates for the plot
    const x = plotData.map(d => d.x);
    const y = plotData.map(d => d.y);
    const text = plotData.map(d => d.text);
    const colors = plotData.map(d => d.marker.color);
    const sizes = plotData.map(d => d.marker.size);
    const opacities = plotData.map(d => d.marker.opacity);
    const songIndices = plotData.map(d => d.songIndex);
    
    // For SAE visualization, include activation info in hover text
    const hoverTexts = plotData.map(d => {
        const baseText = d.text;
        if (currentNeuron >= 0 && visualizationData.sae) {
            return `${baseText}<br>Neuron ${currentNeuron} Activation: ${d.activation.toFixed(3)}`;
        }
        return baseText;
    });
    
    // Title with neuron info if applicable
    let title = `Song Lyrics Embeddings (${plotData.length} songs)`;
    if (currentNeuron >= 0 && visualizationData.sae) {
        title += ` - Highlighting Neuron ${currentNeuron}`;
    }
    
    // Create the scatterplot
    const trace = {
        x: x,
        y: y,
        mode: 'markers',
        type: 'scatter',
        text: hoverTexts,
        hoverinfo: 'text',
        marker: {
            color: colors,
            size: sizes,
            opacity: opacities
        },
        customdata: songIndices
    };
    
    const layout = {
        title: title,
        hovermode: 'closest',
        margin: { l: 40, r: 40, b: 40, t: 60 },
        xaxis: { 
            title: 'DensMAP Dimension 1',
            range: [-8, 1] // Set default x range
        },
        yaxis: { 
            title: 'DensMAP Dimension 2',
            range: [-1, 8] // Set default y range
        }
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        modeBarButtonsToRemove: ['lasso2d', 'select2d'],
        scrollZoom: true // Enable scroll zoom
    };
    
    try {
        // If the plot element is empty, we need to create a new plot even if currentPlot is true
        const needsNewPlot = embeddingPlot.innerHTML.trim() === '' || !currentPlot;
        
        // Create or update the plot
        if (needsNewPlot) {
            console.log("Creating new plot");
            Plotly.newPlot(embeddingPlot, [trace], layout, config);
            
            // Add click event
            embeddingPlot.on('plotly_click', function(data) {
                if (data.points && data.points.length > 0) {
                    const point = data.points[0];
                    const songIndex = point.customdata;
                    if (songIndex !== undefined && filteredSongs[songIndex]) {
                        displaySongDetails(filteredSongs[songIndex]);
                    }
                }
            });
            
            currentPlot = true;
        } else {
            console.log("Updating existing plot");
            Plotly.react(embeddingPlot, [trace], layout, config);
        }
        
        // Create the genre legend
        createGenreLegend();
    } catch (error) {
        console.error("Error creating plot:", error);
        embeddingPlot.innerHTML = '<div class="alert alert-danger">Error creating visualization. Check console for details.</div>';
        document.getElementById('legend-container').style.display = 'none';
    }
}

// Display song details in the sidebar
function displaySongDetails(song) {
    const songDetails = document.getElementById('song-details');
    
    // Truncate lyrics for preview (first 10 lines or so)
    const lyricsPreview = song.lyrics_preview;
    
    // Generate genre tags HTML
    let genreTagsHtml = '';
    if (song.genres && song.genres.length > 0) {
        genreTagsHtml = song.genres.map(genre => 
            `<span class="genre-tag" style="background-color: ${getColor([genre])}33">${genre}</span>`
        ).join('');
    }
    
    // Add SAE activation info if a neuron is selected
    let neuronActivationHtml = '';
    if (currentNeuron >= 0 && visualizationData.sae) {
        const activation = visualizationData.sae.activations[song.id][currentNeuron];
        
        // Create a more visual representation of the activation
        neuronActivationHtml = `
            <div class="neuron-activation">
                <p><strong>Neuron ${currentNeuron} Activation:</strong> ${activation.toFixed(4)}</p>
                <div class="activation-bar-container">
                    <div class="activation-bar" style="width: ${Math.min(100, activation * 100)}%;"></div>
                    <span class="activation-value">${activation.toFixed(3)}</span>
                </div>
            </div>
        `;
    }
    
    // Create HTML for song details
    songDetails.innerHTML = `
        <h3 class="song-title">${song.title}</h3>
        <p class="song-artist">by ${song.artist}</p>
        <p>Album: ${song.album || 'Unknown'}</p>
        <p>Released: ${song.release_date || 'Unknown'}</p>
        <p>Popularity: ${song.popularity || 'N/A'}/100</p>
        <div class="genre-tags">${genreTagsHtml}</div>
        ${neuronActivationHtml}
        <div class="lyrics-preview">
            <strong>Lyrics Preview:</strong>
            ${lyricsPreview || 'No lyrics available'}
        </div>
    `;
} 