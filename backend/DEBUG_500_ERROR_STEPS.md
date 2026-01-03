# Debugging 500 Error - Step by Step

## Current Issue
Backend is returning 500 Internal Server Error when processing video.

## Debugging Steps

### Step 1: Check Backend Terminal
Look for these log messages:
```
[requestId] ML service response: { success: ..., hasData: ... }
ML Service Request Error: { ... }
[requestId] Error in processVideo: ...
```

### Step 2: Check Python ML Service Terminal
Look for:
```
Error processing video: ...
Traceback: ...
```

### Step 3: Check ML Service Response
The backend should log the ML service response. Check for:
- `success: false` - ML service returned an error
- `hasData: false` - ML service returned no data
- Connection errors

### Step 4: Common Issues

#### Issue 1: ML Service Not Running
**Symptoms:**
- Backend logs: `ECONNREFUSED`
- Error: "Cannot connect to ML service"

**Fix:**
```powershell
cd backend\voshan\ml-service
python app.py
```

#### Issue 2: ML Service Crashed
**Symptoms:**
- Python terminal shows error/traceback
- Backend gets 500 from ML service

**Fix:**
- Check Python terminal for the actual error
- Fix the error in the ML service code
- Restart ML service

#### Issue 3: Invalid Response Format
**Symptoms:**
- ML service returns success but no data
- Backend can't parse response

**Fix:**
- Check ML service response structure
- Verify response has required fields

## What to Check Now

1. **Backend Terminal** - Look for error logs
2. **Python ML Service Terminal** - Look for Python errors
3. **Browser Console** - Check the error response details

The error response should now include more details about what went wrong.

