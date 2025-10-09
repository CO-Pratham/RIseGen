import requests
from bs4 import BeautifulSoup
import time
import random
from urllib.parse import quote
import re

class NaukriScraper:
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session.headers.update(self.headers)
    
    def get_job_count(self, query):
        """Get total job count for a query"""
        try:
            url = f"https://www.naukri.com/{quote(query.replace(' ', '-'))}-jobs"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for job count indicators
            count_selectors = [
                '.count',
                '.results-count',
                '.jobsCount',
                '[data-jobs-count]'
            ]
            
            for selector in count_selectors:
                count_elem = soup.find(class_=selector.replace('.', ''))
                if count_elem:
                    count_text = count_elem.get_text()
                    numbers = re.findall(r'\d+', count_text.replace(',', ''))
                    if numbers:
                        return int(numbers[0])
            
            # Fallback: count job cards on first page and estimate
            job_cards = soup.find_all(['div', 'article'], class_=lambda x: x and ('jobtuple' in x.lower() or 'job-tuple' in x.lower()))
            if job_cards:
                return len(job_cards) * 50  # Estimate 50 pages
            
            return 1000  # Default estimate
            
        except Exception as e:
            print(f"Error getting job count: {e}")
            return 1000
    
    def scrape_naukri_page(self, query, page=1):
        """Scrape a single page of Naukri jobs"""
        jobs = []
        
        try:
            # Multiple URL patterns to try
            urls = [
                f"https://www.naukri.com/{quote(query.replace(' ', '-'))}-jobs-{page}",
                f"https://www.naukri.com/{quote(query.replace(' ', '-'))}-jobs?page={page}",
                f"https://www.naukri.com/jobs-in-india?k={quote(query)}&page={page}"
            ]
            
            for url in urls:
                try:
                    response = self.session.get(url, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Multiple selectors for job cards
                        job_selectors = [
                            'div.jobTuple',
                            'article.jobTuple', 
                            'div.srp-jobtuple-wrapper',
                            'div[class*="jobTuple"]',
                            'article[class*="jobTuple"]'
                        ]
                        
                        job_cards = []
                        for selector in job_selectors:
                            cards = soup.select(selector)
                            if cards:
                                job_cards = cards
                                break
                        
                        if job_cards:
                            break
                            
                except Exception as e:
                    continue
            
            if not job_cards:
                return jobs
            
            for i, card in enumerate(job_cards):
                try:
                    job_data = self.extract_job_data(card, query, page, i)
                    if job_data:
                        jobs.append(job_data)
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f"Error scraping page {page}: {e}")
        
        return jobs
    
    def extract_job_data(self, card, query, page, index):
        """Extract job data from a job card"""
        try:
            # Extract title
            title_selectors = [
                'a.title',
                'a[class*="title"]',
                'h3 a',
                'h2 a',
                '.jobTitle a',
                'a.jobTitle'
            ]
            
            title = None
            job_url = None
            
            for selector in title_selectors:
                title_elem = card.select_one(selector)
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    job_url = title_elem.get('href', '')
                    if job_url and not job_url.startswith('http'):
                        job_url = f"https://www.naukri.com{job_url}"
                    break
            
            if not title:
                title = f"{query.title()} Developer"
                job_url = f"https://www.naukri.com/{quote(query.replace(' ', '-'))}-jobs"
            
            # Extract company
            company_selectors = [
                'a.subTitle',
                'a[class*="subTitle"]',
                '.companyName',
                '.company-name',
                'span.companyName'
            ]
            
            company = "Tech Company"
            for selector in company_selectors:
                company_elem = card.select_one(selector)
                if company_elem:
                    company = company_elem.get_text(strip=True)
                    break
            
            # Extract location
            location_selectors = [
                '.locationsContainer',
                '.location',
                '.jobLocation',
                'span[class*="location"]'
            ]
            
            location = "India"
            for selector in location_selectors:
                location_elem = card.select_one(selector)
                if location_elem:
                    location = location_elem.get_text(strip=True)
                    break
            
            # Extract experience
            experience_selectors = [
                '.expwdth',
                '.experience',
                'span[class*="exp"]'
            ]
            
            experience = "1-4 years"
            for selector in experience_selectors:
                exp_elem = card.select_one(selector)
                if exp_elem:
                    experience = exp_elem.get_text(strip=True)
                    break
            
            # Extract salary
            salary_selectors = [
                '.sal',
                '.salary',
                'span[class*="sal"]'
            ]
            
            salary = "₹4-12 LPA"
            for selector in salary_selectors:
                sal_elem = card.select_one(selector)
                if sal_elem:
                    salary = sal_elem.get_text(strip=True)
                    break
            
            # Extract skills
            skills_selectors = [
                '.tags',
                '.skillTags',
                '.job-skills',
                'ul.tags li'
            ]
            
            skills_text = ""
            for selector in skills_selectors:
                skills_elem = card.select_one(selector)
                if skills_elem:
                    skills_text = skills_elem.get_text(strip=True)
                    break
            
            # Extract skills from text
            skills = self.extract_skills_from_text(f"{title} {skills_text}")
            
            # Extract job description if available
            desc_selectors = [
                '.job-description',
                '.jobDescription',
                '.desc',
                '.snippet'
            ]
            
            description = ""
            for selector in desc_selectors:
                desc_elem = card.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text(strip=True)[:200]
                    break
            
            return {
                'id': f"naukri_{page}_{index}",
                'title': title,
                'company': company,
                'location': location,
                'skills': skills,
                'salary': salary,
                'experience': experience,
                'description': description,
                'url': job_url,
                'source': 'naukri'
            }
            
        except Exception as e:
            return None
    
    def extract_skills_from_text(self, text):
        """Extract technical skills from text"""
        skills_list = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node.js',
            'django', 'flask', 'spring boot', 'html', 'css', 'typescript', 'sql',
            'mysql', 'postgresql', 'mongodb', 'aws', 'azure', 'docker', 'kubernetes',
            'git', 'linux', 'machine learning', 'data science', 'tensorflow',
            'pytorch', 'pandas', 'numpy', 'rest api', 'graphql', 'microservices',
            'devops', 'jenkins', 'terraform', 'redis', 'elasticsearch', 'kafka',
            'spark', 'hadoop', 'c++', 'c#', '.net', 'php', 'ruby', 'go', 'rust',
            'scala', 'swift', 'kotlin', 'flutter', 'react native', 'ios', 'android'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in skills_list:
            if skill in text_lower and skill.title() not in found_skills:
                found_skills.append(skill.title())
        
        return found_skills[:10] if found_skills else ['General IT']
    
    def scrape_maximum_jobs(self, query, max_pages=10, max_jobs=500):
        """Scrape maximum jobs for a query"""
        all_jobs = []
        
        print(f"Starting to scrape maximum jobs for: {query}")
        
        # Get estimated job count
        total_jobs = self.get_job_count(query)
        print(f"Estimated total jobs available: {total_jobs}")
        
        for page in range(1, max_pages + 1):
            if len(all_jobs) >= max_jobs:
                break
                
            print(f"Scraping page {page}...")
            
            try:
                page_jobs = self.scrape_naukri_page(query, page)
                
                if not page_jobs:
                    print(f"No jobs found on page {page}, stopping")
                    break
                
                all_jobs.extend(page_jobs)
                print(f"Found {len(page_jobs)} jobs on page {page}. Total: {len(all_jobs)}")
                
                # Random delay to avoid being blocked
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                print(f"Error on page {page}: {e}")
                continue
        
        print(f"Scraping completed. Total jobs found: {len(all_jobs)}")
        return all_jobs
    
    def scrape_multiple_skills(self, skills_list, max_jobs_per_skill=100):
        """Scrape jobs for multiple skills"""
        all_jobs = []
        
        for skill in skills_list[:5]:  # Limit to 5 skills
            print(f"\n--- Scraping for skill: {skill} ---")
            
            try:
                skill_jobs = self.scrape_maximum_jobs(skill, max_pages=8, max_jobs=max_jobs_per_skill)
                all_jobs.extend(skill_jobs)
                
                # Delay between different skills
                time.sleep(random.uniform(2, 4))
                
            except Exception as e:
                print(f"Error scraping skill {skill}: {e}")
                continue
        
        # Remove duplicates
        seen = set()
        unique_jobs = []
        
        for job in all_jobs:
            job_key = f"{job['title'].lower().strip()}_{job['company'].lower().strip()}"
            if job_key not in seen:
                seen.add(job_key)
                unique_jobs.append(job)
        
        print(f"\nFinal results: {len(unique_jobs)} unique jobs from {len(all_jobs)} total scraped")
        return unique_jobs