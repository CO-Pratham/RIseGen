"""
LinkedIn Job Scraper using BrightData API
Fetches real LinkedIn job listings by keywords
"""

import requests
import logging
import time
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInJobScraper:
    """Scraper for LinkedIn jobs using BrightData API"""
    
    def __init__(self, api_key: str = "68b93d508001fa3ec3c6c7cf1d383cdcf9f535e4bf363fe263acc7d44fd03c8b"):
        self.api_key = api_key
        self.base_url = "https://api.brightdata.com/datasets/v3/trigger"
        self.dataset_id = "gd_l7q7dkf244hwjntr0"  # LinkedIn Jobs dataset
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def search_jobs(
        self, 
        keywords: str, 
        location: str = "India",
        max_results: int = 50
    ) -> List[Dict]:
        """
        Search for jobs on LinkedIn by keywords
        
        Args:
            keywords: Search keywords (e.g., "React Developer", "Python Engineer")
            location: Job location
            max_results: Maximum number of jobs to return
            
        Returns:
            List of real LinkedIn job postings
        """
        try:
            self.logger.info(f"Searching LinkedIn jobs for: '{keywords}' in '{location}'")
            
            # Prepare request parameters for BrightData
            params = [
                {
                    "keyword": keywords,
                    "geo": location,
                    "limit": min(max_results, 100)
                }
            ]
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            # Trigger the scraping job
            trigger_response = requests.post(
                f"{self.base_url}?dataset_id={self.dataset_id}&include_errors=true",
                headers=headers,
                json=params,
                timeout=30
            )
            
            if trigger_response.status_code != 200:
                self.logger.error(f"BrightData API error: {trigger_response.text}")
                return []
            
            snapshot_id = trigger_response.json().get("snapshot_id")
            
            if not snapshot_id:
                self.logger.error("No snapshot_id received from BrightData")
                return []
            
            self.logger.info(f"Scraping job triggered. Snapshot ID: {snapshot_id}")
            
            # Poll for results (wait for scraping to complete)
            jobs = self._get_snapshot_results(snapshot_id)
            
            self.logger.info(f"Successfully fetched {len(jobs)} jobs from LinkedIn")
            return jobs[:max_results]
            
        except Exception as e:
            self.logger.error(f"Error searching LinkedIn jobs: {str(e)}")
            return []
    
    def _get_snapshot_results(self, snapshot_id: str, max_wait_time: int = 90) -> List[Dict]:
        """
        Poll BrightData API to get scraping results
        
        Args:
            snapshot_id: Snapshot ID from trigger response
            max_wait_time: Maximum time to wait for results (seconds)
            
        Returns:
            List of job results
        """
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        result_url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}"
        
        start_time = time.time()
        poll_count = 0
        
        self.logger.info(f"Starting to poll for results. Snapshot ID: {snapshot_id}")
        
        while time.time() - start_time < max_wait_time:
            try:
                poll_count += 1
                self.logger.info(f"Poll attempt #{poll_count} - Elapsed time: {int(time.time() - start_time)}s")
                
                response = requests.get(result_url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown")
                    
                    self.logger.info(f"Response status: {status}")
                    
                    # Check if scraping is complete
                    if status == "ready":
                        job_data = data.get("data", [])
                        self.logger.info(f"Scraping complete! Found {len(job_data)} raw jobs")
                        
                        if job_data:
                            jobs = self._parse_linkedin_jobs(job_data)
                            self.logger.info(f"Successfully parsed {len(jobs)} jobs")
                            return jobs
                        else:
                            self.logger.warning("No job data in response")
                            return []
                    
                    self.logger.info(f"Still processing... Status: {status}")
                
                elif response.status_code == 404:
                    self.logger.error("Snapshot not found - may have expired")
                    return []
                else:
                    self.logger.error(f"API returned status code: {response.status_code}")
                
                # Wait 5 seconds before next poll (BrightData recommendation)
                time.sleep(5)
                
            except Exception as e:
                self.logger.error(f"Error polling results: {str(e)}")
                time.sleep(5)
        
        self.logger.warning(f"Timeout after {max_wait_time}s waiting for scraping results")
        return []
    
    def _parse_linkedin_jobs(self, raw_jobs: List[Dict]) -> List[Dict]:
        """
        Parse and format LinkedIn job data from BrightData
        
        Args:
            raw_jobs: Raw job data from BrightData API
            
        Returns:
            List of formatted job dictionaries with real LinkedIn data
        """
        formatted_jobs = []
        
        self.logger.info(f"Parsing {len(raw_jobs)} raw job entries")
        
        for idx, job_data in enumerate(raw_jobs):
            try:
                self.logger.info(f"Parsing job #{idx + 1}: {job_data.get('title', 'Unknown')}")
                
                # Extract job URL (most important field!)
                job_url = (
                    job_data.get("job_url") or 
                    job_data.get("url") or 
                    job_data.get("link") or 
                    job_data.get("job_link") or
                    ""
                )
                
                if not job_url:
                    self.logger.warning(f"Job #{idx + 1} has no URL, skipping")
                    continue
                
                # Build job object with real LinkedIn data
                job = {
                    "job_id": job_data.get("job_id", f"linkedin_{idx}"),
                    "title": job_data.get("title", "N/A"),
                    "company": job_data.get("company_name") or job_data.get("company", "N/A"),
                    "location": job_data.get("location", "N/A"),
                    "description": job_data.get("description", "")[:500],  # Truncate for display
                    "apply_link": job_url,  # Real LinkedIn job URL
                    "url": job_url,  # Duplicate for compatibility
                    "apply_source": "LinkedIn",
                    "source": "LinkedIn",
                    "salary": job_data.get("salary") or job_data.get("salary_range", "Not disclosed"),
                    "posted_date": job_data.get("posted_time") or job_data.get("posted_date") or job_data.get("posted_at", "Recently"),
                    "schedule_type": job_data.get("employment_type") or job_data.get("job_type", "Full-time"),
                    "is_remote": self._check_if_remote(job_data),
                    "experience_level": job_data.get("seniority_level") or job_data.get("experience_level", "N/A"),
                    "company_logo": job_data.get("company_logo") or job_data.get("logo_url", ""),
                    "applicants": job_data.get("applicants_count") or job_data.get("applicants", "N/A"),
                    "industry": job_data.get("industries") or job_data.get("industry", "N/A"),
                    "thumbnail": job_data.get("company_logo") or job_data.get("logo_url", "")
                }
                
                # Extract skills from various possible fields
                skills = self._extract_skills(job_data)
                job["skills"] = skills
                job["qualifications"] = skills
                job["requirements"] = skills
                job["experience"] = job_data.get("experience_level", "N/A")
                
                # Extract benefits
                benefits = job_data.get("benefits", [])
                if isinstance(benefits, str):
                    benefits = [b.strip() for b in benefits.split(",") if b.strip()]
                job["benefits"] = benefits if isinstance(benefits, list) else []
                
                # Extract responsibilities
                responsibilities = job_data.get("responsibilities", [])
                if isinstance(responsibilities, str):
                    responsibilities = [r.strip() for r in responsibilities.split(".") if r.strip()]
                job["responsibilities"] = responsibilities if isinstance(responsibilities, list) else []
                
                formatted_jobs.append(job)
                self.logger.info(f"Successfully parsed job: {job['title']} at {job['company']}")
                
            except Exception as e:
                self.logger.error(f"Error parsing job #{idx + 1}: {str(e)}")
                self.logger.error(f"Job data keys: {list(job_data.keys())}")
                continue
        
        self.logger.info(f"Successfully formatted {len(formatted_jobs)} jobs")
        return formatted_jobs
    
    def _check_if_remote(self, job_data: Dict) -> bool:
        """Check if job is remote from various fields"""
        location = str(job_data.get("location", "")).lower()
        remote_flag = job_data.get("remote", False)
        work_type = str(job_data.get("workplace_type", "")).lower()
        
        return (
            remote_flag or 
            "remote" in location or 
            "work from home" in location or
            "remote" in work_type
        )
    
    def _extract_skills(self, job_data: Dict) -> List[str]:
        """Extract skills from various possible fields"""
        skills = []
        
        # Try different field names
        skills_data = (
            job_data.get("skills") or 
            job_data.get("required_skills") or 
            job_data.get("qualifications") or
            []
        )
        
        if isinstance(skills_data, str):
            skills = [s.strip() for s in skills_data.split(",") if s.strip()]
        elif isinstance(skills_data, list):
            skills = [str(s).strip() for s in skills_data if s]
        
        return skills[:10]  # Limit to 10 skills


class RealJobScraper:
    """Main scraper class that uses LinkedIn job scraper"""
    
    def __init__(self):
        self.linkedin_scraper = LinkedInJobScraper()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def get_all_jobs(
        self, 
        skills: str, 
        location: str = "India", 
        max_results: int = 50
    ) -> List[Dict]:
        """
        Get all jobs matching the skills from LinkedIn
        
        Args:
            skills: Comma-separated skills or job title
            location: Job location
            max_results: Maximum number of results
            
        Returns:
            List of real LinkedIn job postings
        """
        try:
            self.logger.info(f"Fetching LinkedIn jobs for: {skills}")
            
            # Search using LinkedIn via BrightData
            jobs = self.linkedin_scraper.search_jobs(skills, location, max_results)
            
            self.logger.info(f"Found {len(jobs)} total jobs from LinkedIn")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error fetching jobs: {str(e)}")
            return []
    
    def scrape_naukri_jobs(self, query: str, max_results: int = 10) -> List[Dict]:
        """Use LinkedIn scraper for now"""
        return self.linkedin_scraper.search_jobs(query, max_results=max_results)
    
    def scrape_indeed_jobs(self, query: str, max_results: int = 10) -> List[Dict]:
        """Use LinkedIn scraper for now"""
        return self.linkedin_scraper.search_jobs(query, max_results=max_results)

