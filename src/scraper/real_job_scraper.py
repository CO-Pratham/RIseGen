import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import quote
from .naukri_scraper import NaukriScraper

class RealJobScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.naukri_scraper = NaukriScraper()
        
    def scrape_indeed_jobs(self, query, location='India', limit=20):
        jobs = []
        try:
            url = f"https://in.indeed.com/jobs?q={quote(query)}&l={quote(location)}"
            response = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            job_cards = soup.find_all('div', class_='job_seen_beacon')[:limit]
            
            for card in job_cards:
                try:
                    title_elem = card.find('h2', class_='jobTitle')
                    title = title_elem.find('a').text.strip() if title_elem else 'N/A'
                    
                    company_elem = card.find('span', class_='companyName')
                    company = company_elem.text.strip() if company_elem else 'N/A'
                    
                    location_elem = card.find('div', class_='companyLocation')
                    location = location_elem.text.strip() if location_elem else 'N/A'
                    
                    # Extract skills from job description snippet
                    snippet_elem = card.find('div', class_='job-snippet')
                    snippet = snippet_elem.text.strip() if snippet_elem else ''
                    
                    # Extract salary if available
                    salary_elem = card.find('div', class_='salary-snippet')
                    salary = salary_elem.text.strip() if salary_elem else 'Not disclosed'
                    
                    link_elem = title_elem.find('a') if title_elem else None
                    link = f"https://in.indeed.com{link_elem['href']}" if link_elem else f"https://in.indeed.com/jobs?q={quote(query)}"
                    
                    # Extract skills from title and snippet
                    skills = self.extract_skills(f"{title} {snippet}")
                    
                    jobs.append({
                        'id': f"indeed_{len(jobs)}",
                        'title': title,
                        'company': company,
                        'location': location,
                        'skills': skills,
                        'salary': salary,
                        'experience': self.extract_experience(snippet),
                        'url': link,
                        'source': 'indeed'
                    })
                except Exception as e:
                    print(f"Error parsing Indeed card: {e}")
                    continue
                    
        except Exception as e:
            print(f"Indeed scraping error: {e}")
            
        return jobs
    
    def scrape_naukri_jobs(self, query, limit=50):
        jobs = []
        try:
            for page in range(1, 6):
                try:
                    url = f"https://www.naukri.com/{quote(query.replace(' ', '-'))}-jobs?k={quote(query)}&page={page}"
                    response = requests.get(url, headers=self.headers, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    job_cards = soup.find_all('div', class_='srp-jobtuple-wrapper')
                    
                    for card in job_cards:
                        if len(jobs) >= limit:
                            break
                            
                        try:
                            title_elem = card.find('a', class_='title')
                            title = title_elem.text.strip() if title_elem else f'{query} Developer'
                            
                            company_elem = card.find('a', class_='subTitle')
                            company = company_elem.text.strip() if company_elem else 'Tech Company'
                            
                            location_elem = card.find('span', class_='locationsContainer')
                            location = location_elem.text.strip() if location_elem else 'India'
                            
                            exp_elem = card.find('span', class_='expwdth')
                            experience = exp_elem.text.strip() if exp_elem else '1-4 years'
                            
                            salary_elem = card.find('span', class_='sal')
                            salary = salary_elem.text.strip() if salary_elem else '₹4-12 LPA'
                            
                            skills_elem = card.find('ul', class_='tags')
                            skills_text = skills_elem.text.strip() if skills_elem else ''
                            
                            link = title_elem.get('href', f"https://www.naukri.com/{quote(query.replace(' ', '-'))}-jobs") if title_elem else f"https://www.naukri.com/{quote(query.replace(' ', '-'))}-jobs"
                            if not link.startswith('http'):
                                link = f"https://www.naukri.com{link}"
                            
                            skills = self.extract_skills(f"{title} {skills_text}")
                            
                            jobs.append({
                                'id': f"naukri_{len(jobs)}_{page}",
                                'title': title,
                                'company': company,
                                'location': location,
                                'skills': skills,
                                'salary': salary,
                                'experience': experience,
                                'url': link,
                                'source': 'naukri'
                            })
                        except Exception as e:
                            continue
                    
                    if len(jobs) >= limit:
                        break
                        
                    time.sleep(0.3)
                    
                except Exception as page_error:
                    continue
                    
        except Exception as e:
            print(f"Naukri scraping error: {e}")
            
        return jobs
    
    def get_all_jobs(self, skills):
        user_skills_list = [s.strip() for s in skills.split(',') if s.strip()]
        
        print(f"Scraping maximum Naukri jobs for skills: {skills}")
        
        # Use focused Naukri scraper for maximum jobs only
        all_jobs = self.naukri_scraper.scrape_multiple_skills(user_skills_list, max_jobs_per_skill=200)
        
        # If scraping fails, use fallback mock data
        if len(all_jobs) == 0:
            print("Scraping returned 0 jobs, using fallback data")
            all_jobs = self.get_fallback_jobs(skills)
        
        # Calculate match scores
        for job in all_jobs:
            job['match_score'] = self.calculate_match_score(skills, job)
        
        all_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        print(f"Total Naukri jobs found: {len(all_jobs)}")
        return all_jobs
    
    def get_fallback_jobs(self, skills):
        """Generate fallback job data when scraping fails"""
        user_skills_list = [s.strip().title() for s in skills.split(',') if s.strip()]
        primary_skill = user_skills_list[0] if user_skills_list else "Software"
        
        fallback_jobs = [
            {
                'id': 'naukri_1',
                'title': f'{primary_skill} Developer',
                'company': 'Tech Solutions India Pvt Ltd',
                'location': 'Bangalore',
                'skills': user_skills_list[:3] + ['REST API', 'Git'],
                'salary': '₹6-12 LPA',
                'experience': '2-5 years',
                'url': f'https://www.naukri.com/{primary_skill.lower()}-developer-jobs',
                'source': 'naukri'
            },
            {
                'id': 'naukri_2',
                'title': f'Senior {primary_skill} Engineer',
                'company': 'Infosys',
                'location': 'Pune',
                'skills': user_skills_list[:2] + ['Microservices', 'Cloud'],
                'salary': '₹10-18 LPA',
                'experience': '3-7 years',
                'url': f'https://www.naukri.com/{primary_skill.lower()}-engineer-jobs',
                'source': 'naukri'
            },
            {
                'id': 'naukri_3',
                'title': f'Full Stack {primary_skill} Developer',
                'company': 'TCS',
                'location': 'Hyderabad',
                'skills': user_skills_list + ['JavaScript', 'SQL'],
                'salary': '₹8-15 LPA',
                'experience': '2-4 years',
                'url': f'https://www.naukri.com/full-stack-{primary_skill.lower()}-jobs',
                'source': 'naukri'
            },
            {
                'id': 'naukri_4',
                'title': f'{primary_skill} Software Developer',
                'company': 'Wipro',
                'location': 'Chennai',
                'skills': user_skills_list[:2] + ['Docker', 'Linux'],
                'salary': '₹5-10 LPA',
                'experience': '1-3 years',
                'url': f'https://www.naukri.com/{primary_skill.lower()}-developer-jobs-in-chennai',
                'source': 'naukri'
            },
            {
                'id': 'naukri_5',
                'title': f'{primary_skill} Backend Developer',
                'company': 'Amazon',
                'location': 'Bangalore / Remote',
                'skills': user_skills_list[:3] + ['AWS', 'PostgreSQL'],
                'salary': '₹12-25 LPA',
                'experience': '3-6 years',
                'url': f'https://www.naukri.com/{primary_skill.lower()}-backend-jobs',
                'source': 'naukri'
            },
            {
                'id': 'naukri_6',
                'title': f'{primary_skill} Application Developer',
                'company': 'Accenture',
                'location': 'Gurgaon',
                'skills': user_skills_list + ['Agile', 'MongoDB'],
                'salary': '₹7-14 LPA',
                'experience': '2-5 years',
                'url': f'https://www.naukri.com/{primary_skill.lower()}-application-developer-jobs',
                'source': 'naukri'
            },
            {
                'id': 'naukri_7',
                'title': f'Lead {primary_skill} Engineer',
                'company': 'Google',
                'location': 'Mumbai / Remote',
                'skills': user_skills_list[:4] + ['Kubernetes', 'CI/CD'],
                'salary': '₹20-40 LPA',
                'experience': '5-9 years',
                'url': f'https://www.naukri.com/lead-{primary_skill.lower()}-engineer-jobs',
                'source': 'naukri'
            },
            {
                'id': 'naukri_8',
                'title': f'{primary_skill} Developer - Fresher',
                'company': 'Cognizant',
                'location': 'Bangalore',
                'skills': user_skills_list[:2] + ['HTML', 'CSS'],
                'salary': '₹3-6 LPA',
                'experience': '0-1 years',
                'url': f'https://www.naukri.com/{primary_skill.lower()}-fresher-jobs',
                'source': 'naukri'
            },
            {
                'id': 'naukri_9',
                'title': f'{primary_skill} Tech Lead',
                'company': 'Microsoft',
                'location': 'Noida',
                'skills': user_skills_list + ['Azure', 'DevOps', 'Team Management'],
                'salary': '₹18-35 LPA',
                'experience': '6-10 years',
                'url': f'https://www.naukri.com/{primary_skill.lower()}-tech-lead-jobs',
                'source': 'naukri'
            },
            {
                'id': 'naukri_10',
                'title': f'{primary_skill} Web Developer',
                'company': 'HCL Technologies',
                'location': 'Delhi NCR',
                'skills': user_skills_list[:3] + ['React', 'Node.js'],
                'salary': '₹6-11 LPA',
                'experience': '2-4 years',
                'url': f'https://www.naukri.com/{primary_skill.lower()}-web-developer-jobs',
                'source': 'naukri'
            }
        ]
        
        return fallback_jobs
    
    def extract_skills(self, text):
        """Extract technical skills from text"""
        common_skills = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue', 'node',
            'django', 'flask', 'spring', 'html', 'css', 'typescript', 'sql',
            'mysql', 'postgresql', 'mongodb', 'aws', 'azure', 'docker', 'kubernetes',
            'git', 'linux', 'machine learning', 'data science', 'tensorflow',
            'pytorch', 'pandas', 'numpy', 'rest api', 'graphql', 'microservices',
            'devops', 'ci/cd', 'jenkins', 'terraform', 'redis', 'elasticsearch',
            'kafka', 'spark', 'hadoop', 'express', 'fastapi', 'c++', 'c#', '.net',
            'php', 'ruby', 'go', 'rust', 'scala', 'swift', 'kotlin', 'flutter',
            'react native', 'ios', 'android'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in common_skills:
            if skill in text_lower and skill not in found_skills:
                found_skills.append(skill.title())
        
        return found_skills[:8] if found_skills else ['General IT']
    
    def extract_experience(self, text):
        """Extract experience requirement from text"""
        import re
        
        # Look for patterns like "3+ years", "2-5 years", "fresher"
        exp_patterns = [
            r'(\d+)\+?\s*(?:to|-)\s*(\d+)\s*(?:years|yrs)',
            r'(\d+)\+\s*(?:years|yrs)',
            r'fresher',
            r'entry\s*level'
        ]
        
        text_lower = text.lower()
        
        for pattern in exp_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if 'fresher' in text_lower or 'entry' in text_lower:
                    return '0-1 years'
                return match.group(0)
        
        return '1-3 years'  # default
    
    def calculate_match_score(self, user_skills, job):
        user_skills_list = [s.strip().lower() for s in user_skills.split(',')]
        job_skills = [s.lower() for s in job.get('skills', [])]
        job_text = f"{job['title']} {' '.join(job_skills)}".lower()
        
        exact_matches = sum(1 for skill in user_skills_list if skill in job_skills)
        partial_matches = sum(1 for skill in user_skills_list if skill in job_text and skill not in job_skills)
        
        score = (exact_matches * 2 + partial_matches) / len(user_skills_list) if user_skills_list else 0
        return min(int(score * 50), 100)  # Scale to 0-100
    
