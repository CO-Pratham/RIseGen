from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List
import os
import sys
import logging

sys.path.append('/Users/prathamgupta/Downloads/yuvanova-production')
from src.scraper.linkedin_scraper import RealJobScraper

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="YuvaNova Job Matching API",
    description="Real-time LinkedIn job scraping powered by Playwright",
    version="2.0"
)

# Initialize LinkedIn job scraper
job_scraper = RealJobScraper()
logger.info("✅ LinkedIn job scraper initialized with Playwright + Chromium")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="web"), name="static")

# Serve index.html at root
@app.get("/")
async def read_index():
    return FileResponse('web/index.html')

# Serve other static files directly if needed (e.g. app.js, style.css)
@app.get("/{filename}")
async def read_static(filename: str):
    file_path = os.path.join("web", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return JSONResponse(status_code=404, content={"message": "File not found"})



@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "source": "LinkedIn (Direct Scraping)",
        "engine": "Playwright + Chromium"
    }

def calculate_match_score(user_skills: str, job: dict) -> int:
    """Calculate a match score (0-100) based on skills overlap"""
    if not user_skills:
        return 0
        
    user_skills_list = [s.strip().lower() for s in user_skills.split(',')]
    job_title = job.get('title', '').lower()
    job_skills = [s.lower() for s in job.get('skills', [])]
    
    score = 0
    total_weight = 0
    
    # Check for skills in job title (high weight)
    for skill in user_skills_list:
        if not skill: continue
        total_weight += 2
        if skill in job_title:
            score += 2
        # Check for skills in job skills list (medium weight)
        elif any(skill in js for js in job_skills):
            score += 1
            
    # Normalize to 0-100
    if total_weight == 0:
        return 0
        
    final_score = int((score / total_weight) * 100)
    # Ensure a minimum score for relevance if it appeared in search results
    return max(final_score, 60) if final_score > 0 else 40

@app.get("/api/match")
async def match_jobs(
    skills: str = Query(..., description="Job keywords (e.g., 'React Developer', 'Python Engineer')"),
    location: str = Query("India", description="Job location"),
    max_results: int = Query(30, description="Maximum number of jobs")
):
    """
    Search for real LinkedIn jobs matching your skills
    Returns actual job listings with working application links
    """
    if not skills:
        return {
            "matched_jobs": [],
            "recommended_jobs": [],
            "skills": [],
            "error": "Please provide keywords"
        }
    
    try:
        logger.info(f"Searching LinkedIn jobs for: '{skills}' in '{location}'")
        
        # Fetch real jobs from LinkedIn
        # Fetch real jobs from LinkedIn
        all_jobs = await job_scraper.get_all_jobs(skills, location, max_results)
        
        # Calculate match scores for each job
        for job in all_jobs:
            job['match_percentage'] = calculate_match_score(skills, job)
            
        # Sort by match percentage
        all_jobs.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        if not all_jobs:
            logger.warning(f"No jobs found for: {skills}")
            return {
                "matched_jobs": [],
                "recommended_jobs": [],
                "total_jobs_found": 0,
                "skills": [s.strip() for s in skills.split(",") if s.strip()],
                "message": "No jobs found. Try different keywords or location.",
                "source": "LinkedIn"
            }
        
        # Split into matches and recommendations
        direct_matches = all_jobs[:15] if len(all_jobs) > 15 else all_jobs
        recommendations = all_jobs[15:30] if len(all_jobs) > 15 else []
        
        logger.info(f"Found {len(all_jobs)} jobs: {len(direct_matches)} matches, {len(recommendations)} recommendations")
        
        return {
            "matched_jobs": direct_matches,
            "recommended_jobs": recommendations,
            "total_jobs_found": len(all_jobs),
            "skills": [s.strip() for s in skills.split(",") if s.strip()],
            "location": location,
            "source": "LinkedIn (Real-time)",
            "message": f"Found {len(all_jobs)} real LinkedIn job openings"
        }
        
    except Exception as e:
        logger.error(f"Error in job matching: {str(e)}")
        return {
            "matched_jobs": [],
            "recommended_jobs": [],
            "skills": [],
            "error": str(e)
        }

@app.get("/api/jobs")
async def get_jobs(
    skills: str = Query(..., description="Search keywords"),
    location: str = Query("India", description="Job location"),
    max_results: int = Query(50, description="Maximum results"),
    remote: bool = Query(False, description="Filter for remote jobs"),
    entry_level: bool = Query(False, description="Filter for entry-level positions")
):
    """
    Get all jobs with optional filters
    Returns real LinkedIn job listings
    """
    if not skills:
        return {"jobs": [], "total": 0, "error": "Keywords required"}
    
    try:
        logger.info(f"Fetching LinkedIn jobs for: '{skills}'")
        
        # Fetch all jobs
        # Fetch all jobs
        jobs = await job_scraper.get_all_jobs(skills, location, max_results)
        logger.info(f"Found {len(jobs)} jobs before filtering")
        
        # Apply filters
        filtered_jobs = jobs
        
        if remote:
            filtered_jobs = [
                job for job in filtered_jobs 
                if job.get('is_remote', False) or 
                'remote' in job.get('location', '').lower()
            ]
            logger.info(f"After remote filter: {len(filtered_jobs)} jobs")
        
        if entry_level:
            filtered_jobs = [
                job for job in filtered_jobs 
                if 'entry' in job.get('experience_level', '').lower() or 
                'internship' in job.get('experience_level', '').lower()
            ]
            logger.info(f"After entry-level filter: {len(filtered_jobs)} jobs")
        
        logger.info(f"Returning {len(filtered_jobs)} filtered jobs")
        
        return {
            "jobs": filtered_jobs,
            "total": len(filtered_jobs),
            "filters_applied": {
                "remote": remote,
                "entry_level": entry_level
            },
            "source": "LinkedIn"
        }
        
    except Exception as e:
        logger.error(f"Error fetching jobs: {str(e)}")
        return {"jobs": [], "total": 0, "error": str(e)}

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    try:
        return {
            "system_status": "operational",
            "api_version": "3.0",
            "job_sources": ["LinkedIn"],
            "active_jobs_estimate": 100000,
            "features": [
                "Real-time LinkedIn job search",
                "Working application links",
                "Keyword-based search",
                "Advanced filtering",
                "Company information"
            ],
            "scraping_technology": "Playwright + Chromium",
            "scraping_method": "Direct web scraping"
        }
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return {
            "system_status": "operational",
            "api_version": "3.0",
            "error": str(e)
        }

@app.get("/api/search")
async def search_jobs(
    query: str = Query(..., description="Job search keywords"),
    location: str = Query("India", description="Job location"),
    max_results: int = Query(50, description="Maximum results")
):
    """
    General job search endpoint
    Returns comprehensive LinkedIn job data
    """
    try:
        logger.info(f"Job search: '{query}' in '{location}'")
        
        jobs = await job_scraper.get_all_jobs(query, location, max_results)
        
        return {
            "status": "success",
            "query": query,
            "location": location,
            "total_results": len(jobs),
            "jobs": jobs,
            "message": f"Found {len(jobs)} LinkedIn job openings",
            "source": "LinkedIn"
        }
        
    except Exception as e:
        logger.error(f"Error searching jobs: {str(e)}")
        return {
            "status": "error",
            "query": query,
            "location": location,
            "total_results": 0,
            "jobs": [],
            "error": str(e)
        }

@app.get("/api/job/{job_id}")
async def get_job_details(job_id: str):
    """Get detailed information for a specific job"""
    return {
        "status": "info",
        "message": "Job details endpoint - coming soon",
        "job_id": job_id
    }

@app.get("/api/sources")
async def get_sources():
    """Get information about available job sources"""
    return {
        "available_sources": ["LinkedIn"],
        "description": "Real-time job scraping from LinkedIn using Playwright",
        "features": [
            "Real LinkedIn job listings",
            "Working application links",
            "Keyword-based search",
            "Company logos and information",
            "Applicant counts",
            "Experience level filtering",
            "Remote job filtering"
        ],
        "technology": "Scrapy + Playwright + Chromium",
        "method": "Direct web scraping (no API)"
    }
