"""
LinkedIn Job Scraper using Playwright with stealth techniques
Direct scraping from LinkedIn with JavaScript rendering
"""

import asyncio
import logging
import re
import random
from typing import List, Dict, Optional
from datetime import datetime
from urllib.parse import quote_plus
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LinkedInJobScraper:
    """Direct LinkedIn job scraper using Playwright with stealth"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    
    async def scrape_jobs(
        self, 
        keywords: str, 
        location: str = "India", 
        max_results: int = 50
    ) -> List[Dict]:
        """
        Scrape jobs directly from LinkedIn using the guest API
        
        Args:
            keywords: Job search keywords
            location: Job location
            max_results: Maximum number of jobs to return
            
        Returns:
            List of real LinkedIn job postings
        """
        try:
            self.logger.info(f"🔍 Scraping LinkedIn for: '{keywords}' in '{location}'")
            
            # Use LinkedIn's guest API for better reliability
            jobs = await self._scrape_with_guest_api(keywords, location, max_results)
            
            self.logger.info(f"✅ Successfully scraped {len(jobs)} jobs from LinkedIn")
            return jobs[:max_results]
            
        except Exception as e:
            self.logger.error(f"❌ Error scraping LinkedIn: {str(e)}")
            # Return fallback jobs
            # Return empty list if scraping fails
            return []
    
    async def _scrape_with_guest_api(self, keywords: str, location: str, max_results: int) -> List[Dict]:
        """
        Scrape using LinkedIn guest API (more reliable)
        """
        jobs = []
        
        async with async_playwright() as p:
            try:
                self.logger.info("🌐 Launching browser with stealth mode...")
                
                # Launch with extra stealth options
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox'
                    ]
                )
                
                user_agents = [
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
                ]
                
                context = await browser.new_context(
                    user_agent=random.choice(user_agents),
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                    timezone_id='America/New_York'
                )
                
                # Add extra headers to look more human
                await context.set_extra_http_headers({
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1'
                })
                
                page = await context.new_page()
                
                # Remove webdriver property
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                """)
                
                # Build search URL (guest mode)
                keywords_encoded = quote_plus(keywords)
                location_encoded = quote_plus(location)
                
                start = 0
                while len(jobs) < max_results:
                    url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={keywords_encoded}&location={location_encoded}&start={start}"
                    
                    self.logger.info(f"📄 Loading jobs from: {url}")
                    
                    # Navigate with longer timeout
                    response = await page.goto(url, wait_until='domcontentloaded', timeout=60000)
                    
                    if response.status != 200:
                        self.logger.warning(f"⚠️  Got status {response.status} from LinkedIn")
                        break
                    
                    # Wait a bit for content to load
                    await asyncio.sleep(random.uniform(2, 4))
                    
                    # Parse job cards from the HTML
                    new_jobs = await self._parse_jobs_from_html(page, keywords)
                    
                    if not new_jobs:
                        self.logger.info("No more jobs found.")
                        break
                        
                    for job in new_jobs:
                        # Avoid duplicates
                        if not any(j['job_id'] == job['job_id'] for j in jobs):
                            jobs.append(job)
                            
                    self.logger.info(f"Found {len(new_jobs)} new jobs. Total: {len(jobs)}")
                    
                    if len(jobs) >= max_results:
                        break
                        
                    start += 25
                    
                    # Random delay between pages
                    await asyncio.sleep(random.uniform(1, 3))
                
                await browser.close()
                
                if not jobs:
                    self.logger.warning("⚠️  No jobs found, returning fallback data")
                    self.logger.warning("⚠️  No jobs found, returning empty list")
                    return []
                
                self.logger.info(f"✓ Successfully parsed {len(jobs)} jobs")
                return jobs[:max_results]
                
            except PlaywrightTimeout:
                self.logger.error("⏱️  Timeout while loading LinkedIn")
                if 'browser' in locals():
                    await browser.close()
                if 'browser' in locals():
                    await browser.close()
                return []
            except Exception as e:
                self.logger.error(f"Browser error: {str(e)}")
                if 'browser' in locals():
                    await browser.close()
                if 'browser' in locals():
                    await browser.close()
                return []
    
    async def _parse_jobs_from_html(self, page, keywords: str) -> List[Dict]:
        """Parse jobs from LinkedIn HTML"""
        jobs = []
        
        try:
            # Wait for job cards
            await page.wait_for_selector('li', timeout=10000)
            
            # Find all job list items
            job_cards = await page.query_selector_all('li')
            
            self.logger.info(f"Found {len(job_cards)} list items")
            
            for idx, card in enumerate(job_cards[:50]):  # Limit to first 50
                try:
                    # Extract job data
                    job = await self._extract_job_from_card(card, page)
                    if job and job.get('title') and job.get('apply_link'):
                        jobs.append(job)
                        if len(jobs) >= 30:  # Stop after 30 valid jobs
                            break
                except Exception as e:
                    self.logger.debug(f"Error parsing job {idx}: {str(e)}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error parsing HTML: {str(e)}")
        
        return jobs
    
    async def _extract_job_from_card(self, card, page) -> Optional[Dict]:
        """Extract job details from a job card element"""
        try:
            # Extract title
            title_elem = await card.query_selector('.base-search-card__title, h3, .job-card-list__title')
            if not title_elem:
                return None
            title = (await title_elem.inner_text()).strip()
            
            if not title or len(title) < 3:
                return None
            
            # Extract company
            company_elem = await card.query_selector('.base-search-card__subtitle, h4, .job-card-container__company-name')
            company = (await company_elem.inner_text()).strip() if company_elem else 'Company'
            
            # Extract location
            location_elem = await card.query_selector('.job-search-card__location, .job-card-container__metadata-item')
            location = (await location_elem.inner_text()).strip() if location_elem else 'India'
            
            # Extract job link
            link_elem = await card.query_selector('a')
            job_url = await link_elem.get_attribute('href') if link_elem else ''
            
            if not job_url:
                return None
            
            # Clean URL
            if '?' in job_url:
                job_url = job_url.split('?')[0]
            
            if not job_url.startswith('http'):
                job_url = f"https://www.linkedin.com{job_url}"
            
            # Extract company logo
            logo_elem = await card.query_selector('img')
            logo_url = await logo_elem.get_attribute('src') if logo_elem else ''
            
            # Extract posted date
            date_elem = await card.query_selector('.job-search-card__listdate, .job-search-card__listdate--new, time')
            posted_date = (await date_elem.inner_text()).strip() if date_elem else "Recently"
            
            # Extract salary if available
            salary_elem = await card.query_selector('.job-search-card__salary-info')
            salary = (await salary_elem.inner_text()).strip() if salary_elem else "Competitive"
            
            # Build job object
            job = {
                "job_id": self._extract_job_id(job_url),
                "title": title,
                "company": company,
                "location": location,
                "apply_link": job_url,
                "url": job_url,
                "apply_source": "LinkedIn",
                "source": "LinkedIn",
                "posted_date": posted_date,
                "thumbnail": logo_url,
                "company_logo": logo_url,
                "description": f"Apply for {title} at {company}",
                "salary": salary,
                "schedule_type": "Full-time",
                "is_remote": self._check_remote(location),
                "experience_level": "All levels",
                "applicants": "N/A",
                "skills": self._extract_skills_from_title(title),
                "qualifications": [],
                "requirements": [],
                "experience": "Varies",
                "benefits": [],
                "responsibilities": [],
                "scraped_at": datetime.now().isoformat()
            }
            
            return job
            
        except Exception as e:
            return None
    
    def _generate_fallback_jobs(self, keywords: str, location: str, count: int = 10) -> List[Dict]:
        """Generate realistic fallback jobs when scraping fails"""
        self.logger.info(f"📝 Generating {count} fallback jobs for '{keywords}'")
        
        companies = [
            ("TCS", "https://logo.clearbit.com/tcs.com"),
            ("Infosys", "https://logo.clearbit.com/infosys.com"),
            ("Wipro", "https://logo.clearbit.com/wipro.com"),
            ("Tech Mahindra", "https://logo.clearbit.com/techmahindra.com"),
            ("HCL Technologies", "https://logo.clearbit.com/hcltech.com"),
            ("Accenture", "https://logo.clearbit.com/accenture.com"),
            ("Cognizant", "https://logo.clearbit.com/cognizant.com"),
            ("Capgemini", "https://logo.clearbit.com/capgemini.com"),
            ("IBM India", "https://logo.clearbit.com/ibm.com"),
            ("Microsoft India", "https://logo.clearbit.com/microsoft.com")
        ]
        
        locations_list = [
            "Bangalore, Karnataka, India",
            "Pune, Maharashtra, India",
            "Hyderabad, Telangana, India",
            "Chennai, Tamil Nadu, India",
            "Mumbai, Maharashtra, India",
            "Gurgaon, Haryana, India",
            "Noida, Uttar Pradesh, India",
            "Remote"
        ]
        
        jobs = []
        for i in range(min(count, 10)):
            company, logo = companies[i % len(companies)]
            loc = location if location != "India" else locations_list[i % len(locations_list)]
            
            job = {
                "job_id": f"fallback_{i}_{hash(keywords) % 100000}",
                "title": f"{keywords.title()} - {company}",
                "company": company,
                "location": loc,
                "apply_link": f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keywords)}&location={quote_plus(location)}",
                "url": f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keywords)}",
                "apply_source": "LinkedIn",
                "source": "LinkedIn",
                "posted_date": ["1 day ago", "2 days ago", "3 days ago", "1 week ago"][i % 4],
                "thumbnail": logo,
                "company_logo": logo,
                "description": f"Join {company} as a {keywords}. Apply on LinkedIn.",
                "salary": ["₹6-12 LPA", "₹8-15 LPA", "₹10-18 LPA", "Competitive"][i % 4],
                "schedule_type": "Full-time",
                "is_remote": "Remote" in loc,
                "experience_level": ["Entry level", "Mid-Senior level", "Associate"][i % 3],
                "applicants": f"{random.randint(10, 200)} applicants",
                "skills": self._extract_skills_from_title(keywords),
                "qualifications": [],
                "requirements": [],
                "experience": ["0-2 years", "2-5 years", "5+ years"][i % 3],
                "benefits": ["Health insurance", "Work from home", "Flexible hours"],
                "responsibilities": [],
                "scraped_at": datetime.now().isoformat()
            }
            jobs.append(job)
        
        return jobs
    
    def _extract_job_id(self, url: str) -> str:
        """Extract job ID from LinkedIn URL"""
        match = re.search(r'/jobs/view/(\d+)', url)
        if match:
            return match.group(1)
        match = re.search(r'currentJobId=(\d+)', url)
        if match:
            return match.group(1)
        return str(hash(url) % 1000000)
    
    def _check_remote(self, location: str) -> bool:
        """Check if job is remote"""
        location_lower = location.lower()
        return any(term in location_lower for term in ['remote', 'work from home', 'anywhere', 'hybrid'])
    
    def _extract_skills_from_title(self, title: str) -> List[str]:
        """Extract potential skills from job title"""
        skills = []
        title_lower = title.lower()
        
        skill_keywords = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node', 'nodejs',
            'django', 'flask', 'spring', 'sql', 'mongodb', 'postgresql', 'mysql',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'devops', 'ci/cd',
            'machine learning', 'data science', 'ai', 'ml', 'deep learning',
            'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn',
            'html', 'css', 'typescript', 'git', 'rest api', 'graphql'
        ]
        
        for skill in skill_keywords:
            if skill in title_lower:
                skills.append(skill.title())
        
        return skills[:5] if skills else ['Software Development']


class RealJobScraper:
    """Main scraper class using direct LinkedIn scraping"""
    
    def __init__(self):
        self.linkedin_scraper = LinkedInJobScraper()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def get_all_jobs(
        self, 
        skills: str, 
        location: str = "India", 
        max_results: int = 50
    ) -> List[Dict]:
        """
        Get all jobs by scraping LinkedIn directly
        
        Args:
            skills: Job keywords
            location: Job location
            max_results: Maximum number of results
            
        Returns:
            List of real LinkedIn job postings
        """
        try:
            self.logger.info(f"Fetching LinkedIn jobs for: {skills}")
            
            # Run async scraper directly
            jobs = await self.linkedin_scraper.scrape_jobs(skills, location, max_results)
            
            self.logger.info(f"Found {len(jobs)} total jobs from LinkedIn")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error fetching jobs: {str(e)}")
            # Return fallback jobs on error
            # Return empty list on error
            return []
    
    def scrape_naukri_jobs(self, query: str, max_results: int = 10) -> List[Dict]:
        """Use LinkedIn scraper"""
        return self.get_all_jobs(query, max_results=max_results)
    
    def scrape_indeed_jobs(self, query: str, max_results: int = 10) -> List[Dict]:
        """Use LinkedIn scraper"""
        return self.get_all_jobs(query, max_results=max_results)
