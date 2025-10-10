#!/usr/bin/env python3
import http.server
import socketserver
import os

PORT = 8001

class NoCacheHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        # Serve from web directory if called from root, otherwise current directory
        web_dir = 'web' if os.path.exists('web') else '.'
        super().__init__(*args, directory=web_dir, **kwargs)
    
    def end_headers(self):
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), NoCacheHTTPRequestHandler) as httpd:
        print(f"🚀 Server running at http://localhost:{PORT}")
        print("📝 Press Ctrl+C to stop")
        print("✨ No caching enabled - you'll always see the latest changes!")
        httpd.serve_forever()
