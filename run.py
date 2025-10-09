#!/usr/bin/env python3
import subprocess
import threading
import time
import webbrowser
import os

def run_api_server():
    """Run the FastAPI server"""
    print("🚀 Starting YuvaNova API Server...")
    subprocess.run([
        "python3", "-m", "uvicorn", 
        "src.api.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8080", 
        "--reload"
    ])

def run_web_server():
    """Run the web interface server"""
    print("🌐 Starting YuvaNova Web Interface...")
    os.chdir('web')
    subprocess.run(["python3", "-m", "http.server", "8001"])

def open_browser():
    """Open browser after servers start"""
    time.sleep(3)
    print("🌐 Opening YuvaNova Job Matcher...")
    webbrowser.open('http://localhost:8001')

if __name__ == "__main__":
    print("🚀 YuvaNova Production Job Scraping & Matching System")
    print("=" * 60)
    
    # Start API server in background
    api_thread = threading.Thread(target=run_api_server, daemon=True)
    api_thread.start()
    
    # Start browser opener
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start web server (blocking)
    try:
        run_web_server()
    except KeyboardInterrupt:
        print("\n✅ YuvaNova servers stopped")