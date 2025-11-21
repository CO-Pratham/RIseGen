#!/usr/bin/env python3
"""
Test the Playwright LinkedIn scraper directly
"""

import asyncio
import sys
sys.path.append('/Users/prathamgupta/Downloads/yuvanova-production')

from src.scraper.linkedin_scraper import LinkedInJobScraper

async def test_scraper():
    scraper = LinkedInJobScraper()
    print("🔍 Testing LinkedIn scraper with Playwright...")
    print("-" * 60)
    
    keywords = "python developer"
    location = "India"
    max_results = 5
    
    print(f"Keywords: {keywords}")
    print(f"Location: {location}")
    print(f"Max Results: {max_results}")
    print("-" * 60)
    
    jobs = await scraper.scrape_jobs(keywords, location, max_results)
    
    print(f"\n✅ Found {len(jobs)} jobs")
    print("-" * 60)
    
    for i, job in enumerate(jobs, 1):
        print(f"\n{i}. {job['title']}")
        print(f"   Company: {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Link: {job['apply_link'][:80]}...")
        print(f"   Posted: {job['posted_date']}")

if __name__ == "__main__":
    asyncio.run(test_scraper())

