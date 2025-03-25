#!/usr/bin/env python3

import http.server
import socketserver
import webbrowser
import os
import sys

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
Handler = http.server.SimpleHTTPRequestHandler
Handler.extensions_map = {
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
if not os.path.exists('data.json'):
    print("data.json not found! Running prepare_data.py to generate it...")
    try:
        import prepare_data
        prepare_data.main()
    except Exception as e:
        print(f"Error generating data.json: {e}")
        print("Please run prepare_data.py manually before starting the server.")
        sys.exit(1)

# Start the server
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at http://localhost:{PORT}")
    
    # Open the browser
    webbrowser.open(f"http://localhost:{PORT}")
    
    try:
        # Keep the server running until interrupted
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down the server...")
        httpd.shutdown() 