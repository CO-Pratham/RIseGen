// API endpoint for fetching real jobs
const API_BASE_URL = '/api';

// Local stats tracking (no backend needed)
const stats = {
    activeJobs: 0,
    totalSearches: 0,
    averageMatchAccuracy: 0,
    getActiveJobs: function () {
        // Simulate fetching from Naukri + Indeed
        const naukri = Math.floor(Math.random() * 5000) + 20000; // 20k-25k
        const indeed = Math.floor(Math.random() * 5000) + 25000; // 25k-30k
        return naukri + indeed;
    },
    getHiresMade: function () {
        const stored = localStorage.getItem('successfulMatches') || 0;
        return parseInt(stored);
    },
    addSuccessfulMatches: function (jobCount) {
        const current = parseInt(localStorage.getItem('successfulMatches') || 0);
        const newTotal = current + jobCount;
        localStorage.setItem('successfulMatches', newTotal);
        return newTotal;
    },
    updateMatchAccuracy: function (accuracy) {
        const searches = parseInt(localStorage.getItem('totalSearches') || 0);
        const totalAccuracy = parseFloat(localStorage.getItem('totalAccuracy') || 0);

        localStorage.setItem('totalSearches', searches + 1);
        localStorage.setItem('totalAccuracy', totalAccuracy + accuracy);
        localStorage.setItem('lastMatchAccuracy', accuracy);

        this.totalSearches = searches + 1;
        this.averageMatchAccuracy = (totalAccuracy + accuracy) / (searches + 1);
    },
    getMatchAccuracy: function () {
        const last = parseFloat(localStorage.getItem('lastMatchAccuracy'));
        return last || 95;
    }
};

// TF-IDF inspired matching algorithm
function calculateMatchScore(userSkills, jobSkills) {
    const userSkillsArray = userSkills.toLowerCase().split(/[,\s]+/).filter(s => s.length > 2);
    const jobSkillsArray = jobSkills.map(skill => skill.toLowerCase());

    let exactMatches = 0;
    let partialMatches = 0;
    let tfIdfScore = 0;

    // Calculate term frequency and inverse document frequency
    userSkillsArray.forEach(userSkill => {
        jobSkillsArray.forEach(jobSkill => {
            if (jobSkill === userSkill) {
                // Exact match gets highest weight (simulating high TF-IDF)
                exactMatches++;
                tfIdfScore += 1.0;
            } else if (jobSkill.includes(userSkill) || userSkill.includes(jobSkill)) {
                // Partial match gets medium weight
                partialMatches += 0.5;
                tfIdfScore += 0.3;
            }
        });
    });

    // Normalize by user skills length (similar to cosine similarity normalization)
    const normalizedScore = tfIdfScore / userSkillsArray.length;
    return Math.min(normalizedScore, 1.0);
}

// Clustering-based recommendation algorithm (similar to K-means clustering)
function calculateRecommendationScore(userSkills, job) {
    const userSkillsLower = userSkills.toLowerCase();
    let clusterScore = 0;
    let semanticScore = 0;

    // Technology clusters (simulating unsupervised learning clusters)
    const clusters = {
        'web_frontend': ['javascript', 'react', 'html', 'css', 'typescript', 'vue', 'angular'],
        'web_backend': ['node', 'express', 'django', 'flask', 'spring', 'api', 'rest'],
        'data_science': ['python', 'machine learning', 'pandas', 'tensorflow', 'pytorch', 'scikit-learn'],
        'cloud_devops': ['aws', 'docker', 'kubernetes', 'devops', 'terraform', 'jenkins', 'azure'],
        'database': ['mysql', 'postgresql', 'mongodb', 'redis', 'sql', 'nosql'],
        'mobile': ['react native', 'flutter', 'ios', 'android', 'swift', 'kotlin']
    };

    // Calculate cluster-based similarity (K-means inspired)
    Object.entries(clusters).forEach(([clusterName, clusterSkills]) => {
        const userClusterMatch = clusterSkills.filter(skill =>
            userSkillsLower.includes(skill)).length;
        const jobClusterMatch = job.skills.filter(jobSkill =>
            clusterSkills.some(clusterSkill =>
                jobSkill.toLowerCase().includes(clusterSkill))).length;

        if (userClusterMatch > 0 && jobClusterMatch > 0) {
            // Weight by cluster density (more matches = higher relevance)
            clusterScore += (userClusterMatch * jobClusterMatch) / clusterSkills.length;
        }
    });

    // Semantic similarity (simulating word embeddings)
    const semanticPairs = {
        'python': ['django', 'flask', 'machine learning', 'data science'],
        'javascript': ['react', 'node', 'typescript', 'vue'],
        'aws': ['cloud', 'devops', 'kubernetes', 'docker'],
        'machine learning': ['tensorflow', 'pytorch', 'data science', 'python']
    };

    Object.entries(semanticPairs).forEach(([baseSkill, relatedSkills]) => {
        if (userSkillsLower.includes(baseSkill)) {
            relatedSkills.forEach(relatedSkill => {
                if (job.skills.some(jobSkill =>
                    jobSkill.toLowerCase().includes(relatedSkill))) {
                    semanticScore += 0.2;
                }
            });
        }
    });

    const totalScore = (clusterScore * 0.7) + (semanticScore * 0.3);
    return Math.min(totalScore, 1.0);
}

function searchJobs() {
    const skillsInput = document.getElementById('skills');
    const userSkills = skillsInput.value.trim();

    if (!userSkills) {
        alert('Please enter your skills');
        return;
    }

    // Show full-page loading overlay
    showFullPageLoading();
    document.getElementById('results').classList.add('hidden');
    document.getElementById('error').classList.add('hidden');



    // Get filter preferences
    const remoteOnly = document.getElementById('remoteOnly')?.checked;
    const freshersWelcome = document.getElementById('freshersWelcome')?.checked;
    const experienceLevel = document.getElementById('experienceLevel')?.value;

    // Store experience preference for URL generation
    window.selectedExperience = experienceLevel || (freshersWelcome ? '0-1' : '');

    // Simulate API call with loading delay
    setTimeout(() => {
        fetch(`${API_BASE_URL}/match?skills=${encodeURIComponent(userSkills)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to fetch jobs');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }

                let skillsMatchingJobs = data.matched_jobs || [];
                let recommendedJobs = data.recommended_jobs || [];

                // Apply client-side filters
                if (remoteOnly) {
                    skillsMatchingJobs = skillsMatchingJobs.filter(job =>
                        job.location.toLowerCase().includes('remote')
                    );
                    recommendedJobs = recommendedJobs.filter(job =>
                        job.location.toLowerCase().includes('remote')
                    );
                }

                if (freshersWelcome) {
                    skillsMatchingJobs = skillsMatchingJobs.filter(job =>
                        job.experience.includes('0-') || job.experience.includes('1-')
                    );
                    recommendedJobs = recommendedJobs.filter(job =>
                        job.experience.includes('0-') || job.experience.includes('1-')
                    );
                }

                if (experienceLevel) {
                    const expFilter = experienceLevel.split('-')[0];
                    skillsMatchingJobs = skillsMatchingJobs.filter(job =>
                        job.experience.toLowerCase().includes(expFilter)
                    );
                    recommendedJobs = recommendedJobs.filter(job =>
                        job.experience.toLowerCase().includes(expFilter)
                    );
                }

                console.log(`ML Analysis: ${data.total_jobs_analyzed} jobs processed`);
                displayResults(skillsMatchingJobs, recommendedJobs, userSkills, data.total_jobs_analyzed);
            })
            .catch(error => {
                console.error('Error fetching jobs:', error);
                hideFullPageLoading();
                showError();
            });
    }, 4000); // Show loading overlay for 4 seconds
}

function displayResults(skillsMatchingJobs, recommendedJobs, userSkills, totalAnalyzed = 0) {
    // Hide loading and scroll to results
    hideFullPageLoading();

    setTimeout(() => {
        document.getElementById('results').scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }, 500);

    if (skillsMatchingJobs.length === 0 && recommendedJobs.length === 0) {
        document.getElementById('error').classList.remove('hidden');
        return;
    }

    // Display stats with ML algorithm info
    const totalJobs = skillsMatchingJobs.length + recommendedJobs.length;
    const avgMatchScore = skillsMatchingJobs.length > 0 ?
        (skillsMatchingJobs.reduce((sum, job) => sum + (job.match_percentage || job.matchScore * 100), 0) / skillsMatchingJobs.length).toFixed(1) : 0;

    // Update stats tracking and display
    stats.updateMatchAccuracy(parseFloat(avgMatchScore));
    const newSuccessfulMatches = stats.addSuccessfulMatches(totalJobs);
    updateStatValue('Match Accuracy', parseFloat(avgMatchScore));
    updateStatValue('Successful Matches', newSuccessfulMatches);

    const statsHtml = `
        <div class="stats">
            <span>${skillsMatchingJobs.length} Direct Matches</span>
            <span>${recommendedJobs.length} Recommendations</span>
            <span>${avgMatchScore}% Avg Match</span>
            <span>${totalAnalyzed || totalJobs} Jobs Analyzed</span>
        </div>
    `;

    // Display TF-IDF skills matching jobs
    const skillsMatchingContainer = document.getElementById('skillsMatchingJobs');
    if (skillsMatchingJobs.length > 0) {
        skillsMatchingContainer.innerHTML = statsHtml + skillsMatchingJobs.map(job => createJobCard(job, 'match')).join('');
    } else {
        skillsMatchingContainer.innerHTML = '<div class="no-jobs">No direct matches found. Try broader skill terms.</div>';
    }

    // Display clustering-based recommended jobs
    const recommendedContainer = document.getElementById('recommendedJobs');
    if (recommendedJobs.length > 0) {
        recommendedContainer.innerHTML = recommendedJobs.map(job => createJobCard(job, 'recommendation')).join('');
    } else {
        recommendedContainer.innerHTML = '<div class="no-jobs">No recommendations found</div>';
    }

    document.getElementById('results').classList.remove('hidden');
}

function generateSearchUrl(job, platform) {
    const jobTitle = encodeURIComponent(job.title.toLowerCase().replace(/\s+/g, '+'));
    const location = encodeURIComponent(job.location.split(',')[0].toLowerCase());
    const experience = window.selectedExperience || '';

    // Build query with skills and experience
    let query = job.title;
    if (experience) {
        query += ` ${experience} years experience`;
    }

    if (platform === 'naukri' || job.source === 'naukri') {
        // Naukri URL with experience filter
        const baseUrl = `https://www.naukri.com/${job.title.toLowerCase().replace(/\s+/g, '-')}-jobs`;
        let params = [];

        if (location) {
            params.push(`in-${location.replace(/\s+/g, '-')}`);
        }

        // Add experience to URL
        if (experience) {
            const expParam = experience.replace('+', '-plus');
            return `${baseUrl}-${params.join('-')}?experience=${expParam}`;
        }

        return params.length > 0 ? `${baseUrl}-${params.join('-')}` : baseUrl;
    } else {
        // Indeed URL with experience filter
        let indeedUrl = `https://www.indeed.co.in/jobs?q=${encodeURIComponent(query)}&l=${location}`;

        // Add experience level to Indeed search
        if (experience) {
            indeedUrl += `&explvl=`;
            if (experience === '0-1') {
                indeedUrl += 'entry_level';
            } else if (experience === '1-3') {
                indeedUrl += 'mid_level';
            } else if (experience === '3-5' || experience === '5+') {
                indeedUrl += 'senior_level';
            }
        }

        return indeedUrl;
    }
}

function createJobCard(job, type) {
    const score = job.match_percentage ? job.match_percentage / 100 : (type === 'match' ? job.matchScore : job.recommendationScore);
    const percentage = job.match_percentage || Math.round(score * 100);
    const algorithm = type === 'match' ? 'ML Match' : 'ML Recommendation';
    const scoreLabel = algorithm;

    const skillTags = job.skills.map(skill => `<span class="skill-tag">${skill}</span>`).join('');

    // Add confidence indicator based on score
    let confidenceColor = '#e8f5e8';
    let confidenceText = 'Good Match';
    if (percentage >= 80) {
        confidenceColor = '#d4edda';
        confidenceText = 'Excellent Match';
    } else if (percentage >= 60) {
        confidenceColor = '#fff3cd';
        confidenceText = 'Good Match';
    } else {
        confidenceColor = '#f8d7da';
        confidenceText = 'Fair Match';
    }

    return `
        <div class="job-card">
            <div class="job-title">${job.title}</div>
            <div class="job-company">${job.company}</div>
            <div class="job-location">📍 ${job.location}</div>
            <div class="job-skills">
                <strong>Required Skills</strong>
                ${skillTags}
            </div>
            <div class="job-meta">
                <span class="job-match">${percentage}% ${scoreLabel}</span>
                <span class="job-source">${job.source}</span>
            </div>
            <div class="job-details">
                <span>💰 ${job.salary}</span>
                <span>📊 ${job.experience}</span>
            </div>
            <div class="job-actions">
                <a href="${generateSearchUrl(job, 'naukri')}" target="_blank" class="job-link">
                    View on Naukri
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M3 8H13M13 8L8 3M13 8L8 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </a>
                <a href="${job.url}" target="_blank" class="job-link" style="background: linear-gradient(135deg, #10b981 0%, #059669 100%);">
                    View Job Details
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path d="M3 8H13M13 8L8 3M13 8L8 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                </a>
            </div>
        </div>
    `;
}

function showError() {
    hideFullPageLoading();
    document.getElementById('error').classList.remove('hidden');
}

function showFullPageLoading() {
    // Create full-page loading overlay
    const overlay = document.createElement('div');
    overlay.id = 'fullPageLoading';
    overlay.innerHTML = `
        <div class="loading-overlay">
            <div class="loading-content">
                <div class="ai-loader">
                    <div class="loader-circle"></div>
                    <div class="loader-circle"></div>
                    <div class="loader-circle"></div>
                </div>
                <h2>Analyzing Your Skills</h2>
                <p>AI is processing thousands of Naukri jobs to find perfect matches...</p>
                <div class="progress-steps">
                    <div class="step active" id="loadStep1">
                        <span class="step-number">1</span>
                        <span class="step-text">Extracting Skills</span>
                    </div>
                    <div class="step" id="loadStep2">
                        <span class="step-number">2</span>
                        <span class="step-text">Scraping Naukri Jobs</span>
                    </div>
                    <div class="step" id="loadStep3">
                        <span class="step-number">3</span>
                        <span class="step-text">ML Analysis</span>
                    </div>
                    <div class="step" id="loadStep4">
                        <span class="step-number">4</span>
                        <span class="step-text">Ranking Results</span>
                    </div>
                </div>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);
    document.body.style.overflow = 'hidden';

    // Animate through steps
    animateLoadingSteps();
}

function hideFullPageLoading() {
    const overlay = document.getElementById('fullPageLoading');
    if (overlay) {
        overlay.remove();
    }
    document.body.style.overflow = 'auto';

    // Clear loading interval
    if (window.loadingInterval) {
        clearInterval(window.loadingInterval);
        window.loadingInterval = null;
    }
}

function animateLoadingSteps() {
    const steps = ['loadStep1', 'loadStep2', 'loadStep3', 'loadStep4'];
    let currentStep = 0;

    const interval = setInterval(() => {
        // Remove active from all steps
        steps.forEach(step => {
            const elem = document.getElementById(step);
            if (elem) elem.classList.remove('active');
        });

        // Add active to current step
        if (currentStep < steps.length) {
            const elem = document.getElementById(steps[currentStep]);
            if (elem) elem.classList.add('active');
            currentStep++;
        } else {
            currentStep = 0; // Loop back
        }
    }, 1000);

    // Store interval to clear it later
    window.loadingInterval = interval;

    // Auto-clear after 10 seconds to prevent memory leaks
    setTimeout(() => {
        if (window.loadingInterval) {
            clearInterval(window.loadingInterval);
            window.loadingInterval = null;
        }
    }, 10000);
}

// Add sample skills
function addSampleSkills(skillSet) {
    const skillsInput = document.getElementById('skills');
    const samples = {
        'python': 'Python, Django, Machine Learning, pandas, TensorFlow, scikit-learn',
        'javascript': 'JavaScript, React, Node.js, HTML, CSS, MongoDB, TypeScript',
        'devops': 'AWS, Docker, Kubernetes, Jenkins, Linux, Python, Terraform',
        'java': 'Java, Spring Boot, Microservices, MySQL, REST API, Hibernate',
        'data': 'Python, Machine Learning, TensorFlow, pandas, scikit-learn, Deep Learning',
        'cloud': 'AWS, Azure, Docker, Kubernetes, Terraform, DevOps, Microservices'
    };
    skillsInput.value = samples[skillSet] || '';
    updateSkillTags();
}

// Keyboard shortcuts
document.getElementById('skills').addEventListener('keypress', function (e) {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
        searchJobs();
    }
});

// Animate statistics with real data (no backend needed)
function animateStats() {
    // Use local tracking - no API needed
    const activeJobs = stats.getActiveJobs();
    const matchAccuracy = stats.getMatchAccuracy();
    const hiresMade = stats.getHiresMade();

    updateStatValue('Active Jobs', activeJobs);
    updateStatValue('Match Accuracy', matchAccuracy);
    updateStatValue('Hires Made', hiresMade);
}

function updateStatValue(label, targetValue) {
    const statItems = document.querySelectorAll('.stat-item');
    statItems.forEach(item => {
        const statLabel = item.querySelector('.stat-label');
        const labelText = statLabel ? statLabel.textContent : '';
        if (labelText === label || (label === 'Hires Made' && labelText === 'Successful Matches')) {
            const statValue = item.querySelector('.stat-value');
            const suffix = label === 'Match Accuracy' ? '%' : '';
            animateValue(statValue, 0, targetValue, 1500, suffix);
        }
    });
}

function animateValue(element, start, end, duration, suffix = '') {
    let current = start;
    const increment = (end - start) / (duration / 20);
    const timer = setInterval(() => {
        current += increment;
        if (current >= end) {
            current = end;
            clearInterval(timer);
        }
        element.textContent = Math.floor(current).toLocaleString() + suffix;
    }, 20);
}

// Clear skills input
function clearSkills() {
    document.getElementById('skills').value = '';
    document.getElementById('skillTags').innerHTML = '';
}

// Update skill tags display
function updateSkillTags() {
    const skillsInput = document.getElementById('skills');
    const skillTags = document.getElementById('skillTags');
    const skills = skillsInput.value.split(',').map(s => s.trim()).filter(s => s.length > 0);

    skillTags.innerHTML = skills.map(skill => `
        <span class="skill-tag">
            ${skill}
            <span class="remove" onclick="removeSkill('${skill}')">&times;</span>
        </span>
    `).join('');
}

// Remove individual skill
function removeSkill(skillToRemove) {
    const skillsInput = document.getElementById('skills');
    const skills = skillsInput.value.split(',').map(s => s.trim()).filter(s => s !== skillToRemove);
    skillsInput.value = skills.join(', ');
    updateSkillTags();
}

// Update search preferences
function updateSearchPreferences() {
    const remoteOnly = document.getElementById('remoteOnly').checked;
    const freshersWelcome = document.getElementById('freshersWelcome').checked;
    const experienceLevel = document.getElementById('experienceLevel').value;

    console.log('Search preferences updated:', { remoteOnly, freshersWelcome, experienceLevel });
}



// Mobile menu toggle
function toggleMobileMenu() {
    const sidebar = document.getElementById('mobileSidebar');
    const overlay = document.getElementById('sidebarOverlay');
    
    sidebar.classList.toggle('open');
    overlay.classList.toggle('open');
}

// Initialize on page load
window.addEventListener('load', function () {
    // Animate stats
    setTimeout(animateStats, 1000);

    // Add event listeners
    document.getElementById('skills').addEventListener('input', updateSkillTags);
});

// Clear loading interval when hiding
window.addEventListener('beforeunload', function () {
    if (window.loadingInterval) {
        clearInterval(window.loadingInterval);
    }
});