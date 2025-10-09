from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import webbrowser
from threading import Timer

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def open_browser():
    print("🌐 Opening YuvaNova ML Job Matcher...")
    webbrowser.open('http://localhost:8001')

if __name__ == '__main__':
    os.chdir('web')
    server = HTTPServer(('localhost', 8001), CORSRequestHandler)
    
    print("🚀 YuvaNova ML Job Matcher UI starting...")
    print("🧠 Powered by TF-IDF + Cosine Similarity + Clustering")
    print("📱 Open http://localhost:8001 in your browser")
    print("🔬 ML Algorithms: TF-IDF Vectorization, Cosine Similarity, K-means Clustering")
    
    # Auto-open browser after 1 second
    Timer(1, open_browser).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
        server.shutdown()