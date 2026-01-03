# Connection Reset Error - Fixed ✅

## Problem
The frontend was getting `ERR_NETWORK` / `ERR_CONNECTION_RESET` errors when uploading videos, even though the ML service was processing successfully.

## Root Cause
The HTTP server had default timeouts that were too short for long-running video processing requests. When processing took longer than the server timeout, the connection was reset.

## Fixes Applied

### 1. Server Timeout Configuration (`backend/server.js`)
- **Added server timeout**: 20 minutes (1,200,000ms) - enough for large video processing
- **Added keep-alive timeout**: 65 seconds
- **Added headers timeout**: 66 seconds (must be > keep-alive)

```javascript
server.timeout = 1200000; // 20 minutes
server.keepAliveTimeout = 65000; // 65 seconds
server.headersTimeout = 66000; // 66 seconds
```

### 2. Express Body Size Limits (`backend/src/app.js`)
- **Increased JSON body limit**: 500MB (for large video metadata)
- **Increased URL-encoded body limit**: 500MB
- **Added keep-alive headers**: To maintain connections during long processing

### 3. Controller Headers (`backend/src/controllers/voshan/detectionController.js`)
- **Added keep-alive headers**: Before processing starts
- **Added cache-control headers**: To prevent caching issues

### 4. Frontend Error Handling (`frontend/src/pages/voshan/VideoUpload.jsx`)
- **Added ERR_NETWORK detection**: Better error messages for connection resets
- **Added ERR_CONNECTION_RESET handling**: Specific guidance for this error

### 5. Frontend Timeout (`frontend/src/services/voshan/detectionApi.js`)
- **Increased timeout**: 15 minutes (900,000ms) - matches backend ML service timeout

## Timeout Summary

| Component | Timeout | Purpose |
|-----------|---------|---------|
| Frontend → Backend | 15 minutes | Axios request timeout |
| Backend HTTP Server | 20 minutes | Server connection timeout |
| Backend → ML Service | 15 minutes | ML service request timeout |
| ML Service Processing | No limit | Processes until complete |

## Testing

1. **Restart the backend server** to apply the new timeout settings:
   ```bash
   cd backend
   npm start
   # or
   node server.js
   ```

2. **Verify the timeout is set** - you should see in the console:
   ```
   ⏱️  Server timeout: 20 minutes
   ```

3. **Try uploading a video again** - the connection should no longer reset

## If Issues Persist

1. **Check both services are running**:
   - Backend: `http://localhost:5000`
   - ML Service: `http://localhost:5001`

2. **Check server logs** for any errors during processing

3. **For very large videos** (>10 minutes), consider:
   - Splitting into smaller segments
   - Increasing `SERVER_TIMEOUT` in `.env`:
     ```env
     SERVER_TIMEOUT=1800000  # 30 minutes
     ```

## Status
✅ **FIXED** - Connection reset errors should no longer occur for videos that process within 20 minutes.

