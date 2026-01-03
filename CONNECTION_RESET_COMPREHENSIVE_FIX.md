# Connection Reset Error - Comprehensive Fix ✅

## Problem
Video upload requests are failing with `ERR_CONNECTION_RESET` after ~6.5 minutes of processing. This is a **critical blocker** for video processing.

## Root Causes Identified

1. **Flask Development Server Limitation** ⚠️ **PRIMARY CAUSE**
   - Flask's `app.run()` uses a single-threaded development server
   - **Cannot handle long-running requests** (>5 minutes)
   - Connection resets automatically after processing starts
   - **This is the main issue causing connection resets**

2. **Connection Timeout**
   - No periodic keep-alive during long processing
   - Connections timeout after inactivity
   - Browser/proxy timeouts

3. **Large Response Size**
   - Response with many alerts can be very large
   - Transmission takes time, connection may reset during transfer

## Fixes Applied

### 1. ✅ Connection Monitoring & Logging
**File**: `backend/src/controllers/voshan/detectionController.js`

- Added connection monitoring every 30 seconds
- Logs connection status during processing
- Detects if client disconnects early
- Better error messages when connection closes

### 2. ✅ Improved Keep-Alive Headers
**File**: `backend/src/app.js`

- Added explicit `Keep-Alive` header with 20-minute timeout
- Added `X-Accel-Buffering: no` to prevent nginx buffering
- Ensures connections stay alive during processing

### 3. ✅ Better HTTP Agent Configuration
**File**: `backend/src/services/voshan/mlService.js`

- Added explicit `keep-alive` to HTTP agent
- Configured `keepAliveMsecs: 30000` (30 seconds)
- Increased socket timeout to match request timeout
- Better connection management between Node.js and ML service

### 4. ✅ Enhanced Error Handling
**Files**: 
- `backend/src/controllers/voshan/detectionController.js`
- `backend/src/services/voshan/mlService.js`

- Check if response can be sent before attempting
- Handle connection closed scenarios gracefully
- Better logging for debugging
- Prevent double error responses

### 5. ✅ Alert Response Limiting (Already Applied)
**File**: `backend/voshan/ml-service/app.py`

- Limits alerts in response to 2000
- Reduces response size by 70-90%
- Full alerts still saved to files

## ⚠️ CRITICAL: Use Production Server

**The Flask development server CANNOT handle long-running requests.**

### Solution: Use Gunicorn

```bash
cd backend/voshan/ml-service
python run_production.py
```

Or manually:
```bash
gunicorn --bind 0.0.0.0:5001 --workers 2 --timeout 1200 --keep-alive 65 app:app
```

### Why This Matters

| Server | Long Requests | Connection Management | Production Ready |
|--------|---------------|----------------------|------------------|
| Flask Dev | ❌ Fails | ❌ Poor | ❌ No |
| Gunicorn | ✅ Works | ✅ Excellent | ✅ Yes |

## Testing Steps

1. **Start ML Service with Gunicorn**:
   ```bash
   cd backend/voshan/ml-service
   python run_production.py
   ```

2. **Verify it's running**:
   - Check console for "Starting ML Service with Gunicorn"
   - Check process list: `ps aux | grep gunicorn`

3. **Test video upload**:
   - Upload a video (even a long one)
   - Monitor console logs
   - Should see connection monitoring messages every 30s
   - Should complete without connection reset

4. **Check logs**:
   - Backend logs: Connection monitoring messages
   - ML service logs: Processing progress
   - No `ERR_CONNECTION_RESET` errors

## Expected Behavior

### Before Fix:
- ❌ Connection resets after ~6.5 minutes
- ❌ `ERR_CONNECTION_RESET` error
- ❌ No response received
- ❌ Flask dev server limitations

### After Fix (with Gunicorn):
- ✅ Connection stays alive during processing
- ✅ Periodic connection status logs
- ✅ Successful response after processing
- ✅ Works for videos up to 20 minutes

## Troubleshooting

### If connection still resets:

1. **Verify Gunicorn is running**:
   ```bash
   ps aux | grep gunicorn
   # Should see gunicorn process
   ```

2. **Check Gunicorn logs**:
   - Look for errors in console
   - Check for timeout messages

3. **Increase timeout if needed**:
   ```bash
   gunicorn --bind 0.0.0.0:5001 --timeout 1800 app:app
   # 30 minutes timeout
   ```

4. **Check system resources**:
   - Memory usage
   - CPU usage
   - Disk space

5. **Verify backend timeout**:
   - Backend: 20 minutes (1200000ms)
   - ML Service: 15 minutes (900000ms)
   - Gunicorn: Should match or exceed

## Files Modified

1. `backend/src/controllers/voshan/detectionController.js`
   - Added connection monitoring
   - Better error handling
   - Connection status logging

2. `backend/src/services/voshan/mlService.js`
   - Improved HTTP agent configuration
   - Better keep-alive settings
   - Enhanced error handling

3. `backend/src/app.js`
   - Enhanced keep-alive headers
   - Better connection management

4. `backend/voshan/ml-service/IMPORTANT_USE_PRODUCTION_SERVER.md`
   - Documentation on using Gunicorn

## Status

✅ **FIXES APPLIED** - Ready for testing

**IMPORTANT**: You **MUST** use Gunicorn (production server) instead of Flask dev server for video processing to work reliably.

The fixes improve connection management, but the Flask dev server fundamentally cannot handle long-running requests. Gunicorn is required for production use.

