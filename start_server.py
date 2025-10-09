#!/usr/bin/env python3
import uvicorn
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Starting YuvaNova Job Matching API...")
    print("📍 API will be available at: http://localhost:8080")
    print("📊 Frontend: Open web/index.html in your browser")
    print("\n⚡ Scraping jobs from Naukri.com and Indeed.co.in\n")
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )
