# ⚠️ IMPORTANT: Use Production Server for Video Processing

## Critical Issue
The Flask development server (`python app.py`) **CANNOT handle long-running requests properly**. It will reset connections after a few minutes, causing `ERR_CONNECTION_RESET` errors.

## Solution: Use Gunicorn (Production Server)

### Quick Start
```bash
cd backend/voshan/ml-service
python run_production.py
```

Or manually:
```bash
gunicorn --bind 0.0.0.0:5001 --workers 2 --timeout 1200 --keep-alive 65 app:app
```

### Why This Matters
- **Flask Dev Server**: Single-threaded, not production-ready, resets connections
- **Gunicorn**: Production-ready, handles long requests, proper connection management

### Installation
If gunicorn is not installed:
```bash
pip install gunicorn
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

## Current Status
- ✅ Backend (Node.js) is configured for long requests (20 min timeout)
- ✅ Frontend timeout is set to 15 minutes
- ⚠️ **ML Service MUST use Gunicorn for videos >2 minutes**

## Testing
After starting with Gunicorn, test with a video upload. You should see:
- No connection reset errors
- Successful processing even for long videos
- Proper response returned

## Troubleshooting
If you still see connection resets:
1. Verify Gunicorn is running: Check process list
2. Check Gunicorn logs for errors
3. Increase timeout if needed: `--timeout 1800` (30 minutes)
4. Check system resources (memory, CPU)

