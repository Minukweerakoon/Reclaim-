# How to Check ML Service Errors

## The Problem

You're getting a 500 Internal Server Error with HTML response instead of JSON. This guide helps you identify the actual error.

## Step 1: Check Python ML Service Terminal

The ML service terminal will show the actual error. Look for:
- `Error processing video: ...`
- `Traceback: ...`
- Any Python exceptions

## Step 2: Check Backend Terminal

The Node.js backend terminal will show:
- `ML Service Request Error: { ... }`
- Connection errors
- Response status codes

## Step 3: Enable Debug Mode

Edit `backend/voshan/ml-service/config.yaml`:
```yaml
api:
  debug: true  # Change from false to true
```

Then restart the ML service. This will:
- Show detailed error messages
- Include tracebacks in error responses
- Log more information

## Step 4: Test Directly

Test the ML service directly (bypassing Node.js backend):

```powershell
cd backend\voshan\ml-service
python test_video_upload.py <path_to_video>
```

This will show the exact error from Flask.

## Common Errors

### 1. Services Not Initialized
**Error**: "Services not initialized"
**Fix**: Check if model file exists: `models/best.pt`

### 2. Video File Error
**Error**: "Cannot open video" or "Cannot read video"
**Fix**: Video file may be corrupted or unsupported format

### 3. Optical Flow Error
**Error**: "prevPyr" or "lkpyramid"
**Fix**: Already handled - frames are resized automatically

### 4. Memory Error
**Error**: Out of memory
**Fix**: Video too large, try smaller video

## Next Steps

1. **Restart ML Service** with debug mode enabled
2. **Check Python terminal** for error messages
3. **Try uploading video again**
4. **Check the error message** in the response

The error handlers are now configured to return JSON instead of HTML, so you should see the actual error message in the response.

