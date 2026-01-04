# API Connection Reset Error - Fix Guide

## Problem
Getting `ERR_CONNECTION_RESET` error when processing videos:
```
POST http://localhost:5000/api/voshan/detection/process-video net::ERR_CONNECTION_RESET
```

## Root Cause
The Python ML service is likely running with Flask's development server (`python app.py`), which **cannot handle long-running requests**. Flask dev server resets connections after a few minutes.

## Solution: Use Gunicorn (Production Server)

### Step 1: Stop Flask Dev Server
If you're running `python app.py`, stop it (Ctrl+C).

### Step 2: Start ML Service with Gunicorn

**Option A: Use the production script (Recommended)**
```bash
cd backend/voshan/ml-service
python run_production.py
```

**Option B: Start Gunicorn manually**
```bash
cd backend/voshan/ml-service
gunicorn --bind 0.0.0.0:5001 --workers 2 --timeout 1200 --keep-alive 65 app:app
```

### Step 3: Verify It's Running
Check the output - you should see Gunicorn starting with workers:
```
[INFO] Starting gunicorn 21.x.x with 2 workers
```

### Step 4: Test Video Upload
Try uploading a video again. The connection reset error should be gone.

## Why Gunicorn?
- **Flask Dev Server**: Single-threaded, not production-ready, resets connections
- **Gunicorn**: Production-ready, handles long requests properly, manages connections correctly

## Troubleshooting

### Gunicorn not installed?
```bash
pip install gunicorn
```
Or install all requirements:
```bash
pip install -r requirements.txt
```

### Port 5001 already in use?
- Check what's using it: `netstat -ano | findstr :5001` (Windows) or `lsof -i :5001` (Linux/Mac)
- Stop the Flask dev server first
- Or change port in the command

### Still getting connection resets?
1. **Increase timeout** for very long videos:
   ```bash
   gunicorn --bind 0.0.0.0:5001 --workers 2 --timeout 1800 --keep-alive 65 app:app
   ```
   (1800 seconds = 30 minutes)

2. **Check system resources**: Long videos need memory and CPU
3. **Check Gunicorn logs** for any errors
4. **Verify backend timeout** in `backend/server.js` (should be 20 minutes)

## Quick Check
- ✅ Backend server running: `http://localhost:5000`
- ✅ ML service running: `http://localhost:5001/api/v1/detect/status`
- ✅ Using Gunicorn (not Flask dev server)

## Status
✅ **FIXED** - After starting ML service with Gunicorn, connection reset errors should be resolved.

