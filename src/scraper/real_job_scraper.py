"""
Real Job Scraper - Uses LinkedIn Jobs via BrightData
Provides access to real LinkedIn job listings by keyword search
"""

from src.scraper.linkedin_job_scraper import RealJobScraper

# Export for main API
__all__ = ['RealJobScraper']
