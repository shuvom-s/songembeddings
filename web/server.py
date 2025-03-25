#!/usr/bin/env python3
"""
Simple web server for the song lyrics visualization.

This server serves static files from the web directory and will 
automatically generate data.json if it doesn't exist.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
import subprocess

# Add the parent directory to the Python path for importing modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Check if port is provided as command line argument
if len(sys.argv) > 1:
    try:
        PORT = int(sys.argv[1])
    except ValueError:
        print(f"Invalid port number: {sys.argv[1]}")
        PORT = 8000
else:
    PORT = 8000

# Set up the server
class MyHandler(http.server.SimpleHTTPRequestHandler):
    """Custom request handler that serves from the web directory."""
    
    def __init__(self, *args, **kwargs):
        self.directory = os.path.dirname(os.path.abspath(__file__))
        super().__init__(*args, **kwargs)
    
    def translate_path(self, path):
        """Translate URL paths to local file system paths."""
        # Map '/' to index.html
        if path == '/':
            return os.path.join(self.directory, 'index.html')
        return super().translate_path(path)

# Set up MIME types
MyHandler.extensions_map = {
    '.html': 'text/html',
    '.css': 'text/css',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.svg': 'image/svg+xml',
    '': 'application/octet-stream'
}

# Ensure data.json exists
data_json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data.json')
if not os.path.exists(data_json_path):
    print("data.json not found! Running prepare_data.py to generate it...")
    try:
        # Get the path to prepare_data.py relative to this script
        prepare_data_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            'src', 
            'prepare_data.py'
        )
        
        if not os.path.exists(prepare_data_path):
            print(f"Error: {prepare_data_path} not found.")
            print("Please make sure the file exists and run it manually.")
            sys.exit(1)
        
        result = subprocess.run([sys.executable, prepare_data_path, '--output-file', data_json_path])
        if result.returncode != 0:
            print("Error generating data.json.")
            print("Please run prepare_data.py manually before starting the server.")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error generating data.json: {e}")
        print("Please run prepare_data.py manually before starting the server.")
        sys.exit(1)

# Start the server
with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Serving at http://localhost:{PORT}")
    print(f"Press Ctrl+C to stop the server")
    
    # Open the browser
    webbrowser.open(f"http://localhost:{PORT}")
    
    try:
        # Keep the server running until interrupted
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down the server...")
        httpd.shutdown() 