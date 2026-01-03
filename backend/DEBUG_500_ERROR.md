# Debugging 500 Internal Server Error

## Problem

The `/api/voshan/detection/process-video` endpoint is returning a 500 error with HTML content instead of JSON.

## Root Cause

The Python ML service (Flask) is returning a 500 error with an HTML error page, which the Node.js backend is not properly parsing.

## Fixes Applied

### 1. Improved ML Service Error Handling (`mlService.js`)
- Added `validateStatus` to axios to handle 500 responses without throwing
- Added HTML response parsing to extract error messages
- Better error message extraction from Flask error pages

### 2. Enhanced Controller Error Handling (`detectionController.js`)
- Better error logging with stack traces
- More detailed error messages
- Proper error propagation from ML service

### 3. Improved App Error Handler (`app.js`)
- Better error logging
- Check for headers already sent
- More informative error responses

## How to Debug

### Step 1: Check Backend Logs
Look for error messages in the backend terminal:
```
[requestId] Error in processVideo: ...
ML Service Request Error: { ... }
```

### Step 2: Check ML Service Logs
Check the Python ML service terminal for errors:
```
Error processing video: ...
Traceback: ...
```

### Step 3: Test ML Service Directly
```powershell
# Test ML service health
Invoke-WebRequest -Uri "http://localhost:5001/api/v1/detect/status"
```

### Step 4: Check Common Issues

1. **ML Service Not Running**
   - Error: `ECONNREFUSED`
   - Solution: Start ML service on port 5001

2. **ML Service Crashed**
   - Check Python terminal for errors
   - Look for Python tracebacks

3. **Video Processing Error**
   - Check ML service logs for specific error
   - May be related to video format or content

4. **Memory Issues**
   - Large videos may cause memory errors
   - Try with smaller video first

## Expected Behavior After Fix

1. **If ML Service Returns 500:**
   - Backend will parse the error (HTML or JSON)
   - Return proper JSON error response
   - Include error details in response

2. **Error Response Format:**
   ```json
   {
     "success": false,
     "message": "Error processing video",
     "error": "Specific error message",
     "details": {
       "status": 500,
       "message": "..."
     }
   }
   ```

## Next Steps

1. **Restart Backend Server** (if running)
2. **Check ML Service is Running** on port 5001
3. **Try Uploading Video Again**
4. **Check Backend Terminal** for detailed error logs
5. **Check ML Service Terminal** for Python errors

## Common Error Messages

- **"Cannot connect to ML service"** → ML service not running
- **"Request timed out"** → Video too large or ML service slow
- **"Internal server error"** → Check ML service logs for details
- **HTML error page** → ML service crashed, check Python logs

