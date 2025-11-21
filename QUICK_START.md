# 🚀 Quick Start Guide - LinkedIn Job Scraper

## ✅ Setup Complete!

Your LinkedIn job scraper using BrightData API is ready to use.

---

## 📋 How to Run

### Step 1: Start the Backend API (Terminal 1)

```bash
cd /Users/prathamgupta/Downloads/yuvanova-production
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**You should see:**

```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 2: Start the Frontend (Terminal 2)

```bash
cd /Users/prathamgupta/Downloads/yuvanova-production/web
python3 -m http.server 8001
```

**Or use the serve.py:**

```bash
python3 serve.py
```

### Step 3: Open in Browser

Navigate to: **http://localhost:8001**

---

## 🎯 How It Works

1. **Enter Skills**: Type job keywords (e.g., "React Developer", "Python Engineer")
2. **Click Search**: The system will show a loading screen
3. **Wait 60-90 seconds**: BrightData scrapes REAL LinkedIn jobs
4. **View Results**: Real LinkedIn jobs with working "Apply on LinkedIn" links

---

## 🔑 API Configuration

**BrightData API Key** (Already configured):

```
68b93d508001fa3ec3c6c7cf1d383cdcf9f535e4bf363fe263acc7d44fd03c8b
```

Located in: `src/scraper/linkedin_job_scraper.py`

---

## 📊 API Endpoints

### Main Endpoint (Frontend uses this):

```
GET http://localhost:8000/api/match?skills=React%20Developer&location=India
```

### Test Endpoints:

```bash
# Health Check
curl http://localhost:8000/health

# Get API Stats
curl http://localhost:8000/api/stats

# Get Available Sources
curl http://localhost:8000/api/sources

# Search Jobs
curl "http://localhost:8000/api/search?query=Python%20Developer&location=Bangalore"
```

---

## ⚙️ What Was Fixed

### ✅ Backend (Python)

- **LinkedIn Scraper** using BrightData API
- Real-time job scraping (60-90 second wait)
- Proper error handling and logging
- Working LinkedIn job URLs

### ✅ Frontend (JavaScript)

- Fixed syntax error (extra `}`)
- Added 120-second timeout for API calls
- Loading screen with progress bar
- Real-time status updates
- Proper LinkedIn link handling

### ✅ Features

- **Real LinkedIn Jobs**: All jobs come from LinkedIn via BrightData
- **Working Links**: "Apply on LinkedIn" buttons go to actual LinkedIn job pages
- **Loading Screen**: Shows progress during 60-90 second scraping
- **Error Handling**: Fallback data if API times out

---

## 🐛 Troubleshooting

### "API Server NOT running" error:

Start the backend server (Step 1 above)

### "Connection refused" error:

Make sure port 8000 is not in use:

```bash
lsof -ti:8000 | xargs kill -9  # Kill process on port 8000
```

### No jobs returned:

- Check console logs for API errors
- Verify BrightData API key is valid
- Wait full 90 seconds for scraping to complete

### Jobs show but wrong links:

- Clear browser cache (Cmd+Shift+R)
- Check console for job data structure

---

## 📝 Console Logs to Watch

### Browser Console (F12):

```
🔍 searchJobs() called
🌐 API Base URL: http://localhost:8000/api
🚀 Full API URL: http://localhost:8000/api/match?skills=...
📡 API Response received: 200
✅ API Data: {...}
✅ Displaying X REAL LinkedIn jobs
```

### Backend Terminal:

```
INFO: Searching LinkedIn jobs for: 'React Developer'
INFO: Starting to poll for results. Snapshot ID: ...
INFO: Poll attempt #1 - Elapsed time: 5s
INFO: Response status: processing
INFO: Scraping complete! Found X raw jobs
INFO: Successfully parsed X jobs
```

---

## 🎨 UI Features

- **Loading Screen**: Animated progress bar (0-100%)
- **Step Indicators**: Shows current scraping step
- **Job Cards**: Company logos, LinkedIn badges
- **Apply Buttons**: Direct LinkedIn links with icons

---

## 📂 File Structure

```
yuvanova-production/
├── src/
│   ├── api/
│   │   └── main.py              # FastAPI backend
│   └── scraper/
│       ├── linkedin_job_scraper.py   # BrightData scraper
│       └── real_job_scraper.py       # Wrapper
├── web/
│   ├── index.html               # Frontend
│   ├── app.js                   # JavaScript (FIXED)
│   ├── style.css                # Styles
│   └── serve.py                 # Web server
└── QUICK_START.md              # This file
```

---

## 🔄 Development Workflow

1. Make changes to Python files → Backend auto-reloads
2. Make changes to HTML/JS/CSS → Refresh browser
3. Check logs in both terminals
4. Test with different keywords

---

## 💡 Tips

- **Be Patient**: Real LinkedIn scraping takes 60-90 seconds
- **Check Logs**: Console shows detailed progress
- **Use Real Keywords**: Try "Software Engineer", "Data Scientist", etc.
- **Different Locations**: Try "Bangalore", "Mumbai", "Remote"

---

## 🎉 You're All Set!

Your LinkedIn job scraper is ready. Start both servers and visit http://localhost:8001

**Happy Job Hunting! 🚀**
