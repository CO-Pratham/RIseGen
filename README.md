# YuvaNova Production Job Scraping & Matching System

## Architecture Overview

### Data Flow
1. **Cloud Scheduler** triggers scraping jobs every 6 hours
2. **Cloud Run Scraper Service** scrapes job boards asynchronously
3. **Pub/Sub** decouples scraping from processing
4. **Cloud Function** processes messages and stores in BigQuery
5. **Cloud Run API Service** serves job matching endpoints
6. **Cloud Storage** stores trained ML models

### Key Components

#### Scraper Service (`src/scraper/`)
- Asynchronous web scraping with rate limiting
- Modular design supporting multiple job boards
- Publishes to Pub/Sub for decoupled processing

#### Data Processor (`src/processor/`)
- Data validation and cleaning
- Duplicate detection using content hashing
- Cloud Function for BigQuery integration

#### Job Matcher (`src/matcher/`)
- TF-IDF vectorization for job descriptions
- Cosine similarity for matching user skills
- Model persistence to Google Cloud Storage

#### API Service (`src/api/`)
- FastAPI REST endpoints
- Automatic model loading from GCS
- Health checks and monitoring

### Deployment

```bash
# Deploy using Cloud Build
gcloud builds submit --config deployment/cloudbuild.yaml

# Set up Cloud Scheduler
gcloud scheduler jobs create http scraper-job \
  --schedule="0 */6 * * *" \
  --uri="https://yuvanova-scraper-url/scrape" \
  --http-method=POST
```

### Monitoring Metrics
- `jobs_scraped_per_source`: Jobs scraped by source
- `scraper_error_rate`: Scraping failure rate  
- `api_latency`: API response times
- `matching_accuracy`: Job matching quality

### Environment Variables
- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `PUBSUB_TOPIC`: Pub/Sub topic name
- `GCS_BUCKET`: Storage bucket for models
- `MODEL_PATH`: Path to trained model file