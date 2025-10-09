import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import re

class MLJobMatcher:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            lowercase=True
        )
        self.skill_clusters = None
        self.job_vectors = None
        self.jobs_data = []
        
    def preprocess_text(self, text):
        """Clean and preprocess text data"""
        if not text:
            return ""
        
        text = re.sub(r'[^\w\s]', ' ', str(text))
        text = re.sub(r'\s+', ' ', text)
        return text.lower().strip()
    
    def extract_skills_from_text(self, text):
        """Extract technical skills using pattern matching"""
        skill_patterns = {
            'programming': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 
                'ruby', 'go', 'rust', 'scala', 'kotlin', 'swift', 'dart'
            ],
            'web_frontend': [
                'react', 'angular', 'vue', 'html', 'css', 'sass', 'less',
                'bootstrap', 'tailwind', 'jquery', 'webpack', 'babel'
            ],
            'web_backend': [
                'node.js', 'express', 'django', 'flask', 'spring', 'laravel',
                'rails', 'asp.net', 'fastapi', 'nestjs'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
                'cassandra', 'dynamodb', 'sqlite', 'oracle', 'sql server'
            ],
            'cloud_devops': [
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins',
                'terraform', 'ansible', 'chef', 'puppet', 'gitlab ci', 'github actions'
            ],
            'data_science': [
                'machine learning', 'deep learning', 'tensorflow', 'pytorch',
                'pandas', 'numpy', 'scikit-learn', 'keras', 'opencv', 'nltk'
            ],
            'mobile': [
                'react native', 'flutter', 'ios', 'android', 'xamarin',
                'ionic', 'cordova', 'swift', 'objective-c'
            ]
        }
        
        text_lower = text.lower()
        extracted_skills = []
        
        for category, skills in skill_patterns.items():
            for skill in skills:
                if skill in text_lower and skill not in extracted_skills:
                    extracted_skills.append(skill)
        
        return extracted_skills
    
    def create_job_profile(self, job):
        """Create a comprehensive job profile for ML processing"""
        title = self.preprocess_text(job.get('title', ''))
        company = self.preprocess_text(job.get('company', ''))
        location = self.preprocess_text(job.get('location', ''))
        skills = ' '.join(job.get('skills', []))
        description = self.preprocess_text(job.get('description', ''))
        
        job_text = f"{title} {company} {skills} {description}"
        return job_text
    
    def train_model(self, jobs):
        """Train TF-IDF model on job data"""
        self.jobs_data = jobs
        
        job_profiles = [self.create_job_profile(job) for job in jobs]
        
        self.job_vectors = self.tfidf_vectorizer.fit_transform(job_profiles)
        
        if len(jobs) > 10:
            n_clusters = min(8, len(jobs) // 5)
            self.skill_clusters = KMeans(n_clusters=n_clusters, random_state=42)
            self.skill_clusters.fit(self.job_vectors)
        
        return True
    
    def calculate_similarity_score(self, user_skills, job):
        """Calculate similarity using TF-IDF and cosine similarity"""
        user_profile = self.preprocess_text(' '.join(user_skills))
        
        try:
            user_vector = self.tfidf_vectorizer.transform([user_profile])
            job_profile = self.create_job_profile(job)
            job_vector = self.tfidf_vectorizer.transform([job_profile])
            
            similarity = cosine_similarity(user_vector, job_vector)[0][0]
            
            job_skills_lower = [s.lower() for s in job.get('skills', [])]
            user_skills_lower = [s.lower().strip() for s in user_skills]
            
            exact_matches = len(set(user_skills_lower) & set(job_skills_lower))
            skill_boost = exact_matches * 0.2
            
            final_score = min(similarity + skill_boost, 1.0)
            return final_score
            
        except Exception as e:
            return self.simple_skill_match(user_skills, job)
    
    def simple_skill_match(self, user_skills, job):
        """Fallback simple skill matching"""
        user_skills_lower = [s.lower().strip() for s in user_skills]
        job_text = f"{job.get('title', '')} {' '.join(job.get('skills', []))}".lower()
        
        matches = sum(1 for skill in user_skills_lower if skill in job_text)
        return matches / len(user_skills_lower) if user_skills_lower else 0
    
    def get_cluster_recommendations(self, user_skills, jobs, top_k=10):
        """Get recommendations using clustering"""
        if not self.skill_clusters or not jobs:
            return []
        
        user_profile = self.preprocess_text(' '.join(user_skills))
        user_vector = self.tfidf_vectorizer.transform([user_profile])
        
        user_cluster = self.skill_clusters.predict(user_vector)[0]
        
        cluster_jobs = []
        for i, job in enumerate(jobs):
            if i < len(self.job_vectors.toarray()):
                job_cluster = self.skill_clusters.predict([self.job_vectors[i]])[0]
                if job_cluster == user_cluster:
                    similarity = self.calculate_similarity_score(user_skills, job)
                    cluster_jobs.append((job, similarity))
        
        cluster_jobs.sort(key=lambda x: x[1], reverse=True)
        return [job for job, _ in cluster_jobs[:top_k]]
    
    def rank_jobs(self, user_skills_text, jobs):
        """Main function to rank jobs using ML algorithms"""
        if not jobs:
            return [], []
        
        user_skills = [s.strip() for s in user_skills_text.split(',') if s.strip()]
        
        self.train_model(jobs)
        
        scored_jobs = []
        for job in jobs:
            similarity = self.calculate_similarity_score(user_skills, job)
            job_copy = job.copy()
            job_copy['match_score'] = similarity
            job_copy['match_percentage'] = int(similarity * 100)
            scored_jobs.append(job_copy)
        
        scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        direct_matches = [job for job in scored_jobs if job['match_score'] > 0.3][:15]
        
        cluster_recommendations = self.get_cluster_recommendations(user_skills, jobs, top_k=10)
        
        direct_match_ids = {job.get('id', f"{job['title']}_{job['company']}") for job in direct_matches}
        recommendations = []
        
        for job in cluster_recommendations:
            job_id = job.get('id', f"{job['title']}_{job['company']}")
            if job_id not in direct_match_ids:
                job_copy = job.copy()
                job_copy['match_score'] = self.calculate_similarity_score(user_skills, job)
                job_copy['match_percentage'] = int(job_copy['match_score'] * 100)
                recommendations.append(job_copy)
        
        return direct_matches, recommendations[:10]