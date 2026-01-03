# Troubleshooting Video Upload Errors

## Common Error: "Error processing video"

This error occurs when the backend cannot successfully communicate with the Python ML service. Here are the most common causes and solutions:

### 1. Python ML Service Not Running

**Symptom:** Error message includes "ECONNREFUSED" or "Cannot connect to ML service"

**Solution:**
1. Navigate to `backend/ml-service/`
2. Start the Python ML service:
   ```bash
   python app.py
   ```
3. Verify it's running on port 5001:
   - You should see: `🚀 Starting ML Service on 0.0.0.0:5001`
4. Test the service directly:
   ```powershell
   Invoke-WebRequest -Uri "http://localhost:5001/api/v1/detect/status"
   ```

### 2. ML Service Missing Required Files

**Symptom:** ML service starts but crashes or returns errors

**Required Files:**
- `backend/ml-service/app.py` - Main Flask application
- `backend/ml-service/config.yaml` - Configuration file
- `backend/ml-service/requirements.txt` - Python dependencies
- `backend/ml-service/models/best.pt` - Trained YOLO model
- `backend/ml-service/services/detector.py` - YOLO wrapper
- `backend/ml-service/services/tracker.py` - Object tracking
- `backend/ml-service/services/behavior.py` - Behavior detection

**Solution:**
1. Check if all files exist
2. Install Python dependencies:
   ```bash
   cd backend/ml-service
   pip install -r requirements.txt
   ```
3. Ensure `best.pt` model file is in `backend/ml-service/models/`

### 3. Model File Missing

**Symptom:** ML service starts but fails when processing video

**Solution:**
1. Place your trained YOLO model at: `backend/ml-service/models/best.pt`
2. Verify the file exists and is not corrupted
3. Check `config.yaml` to ensure model path is correct

### 4. Port Conflict

**Symptom:** ML service fails to start or connection refused

**Solution:**
1. Check if port 5001 is already in use:
   ```powershell
   netstat -ano | findstr :5001
   ```
2. If port is in use, either:
   - Stop the other service using port 5001
   - Change ML service port in `app.py` and update `ML_SERVICE_URL` in backend `.env`

### 5. Connection Timeout

**Symptom:** Error message includes "timeout" or "ETIMEDOUT"

**Possible Causes:**
- Video file is too large
- ML service is processing slowly
- Network issues

**Solution:**
1. Try with a smaller video file first
2. Check ML service logs for processing errors
3. Increase timeout in `backend/src/services/voshan/mlService.js` (currently 5 minutes)

### 6. Incorrect ML Service URL

**Symptom:** Connection errors even when service is running

**Solution:**
1. Check `backend/.env` file:
   ```
   ML_SERVICE_URL=http://localhost:5001
   ```
2. Verify the URL matches where your ML service is running
3. Restart the Node.js backend after changing `.env`

## Quick Diagnostic Steps

### Step 1: Check ML Service Status
```powershell
# Test ML service directly
Invoke-WebRequest -Uri "http://localhost:5001/api/v1/detect/status"
```

**Expected Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": false
}
```

### Step 2: Check Backend Connection
```powershell
# Test backend's connection to ML service
Invoke-WebRequest -Uri "http://localhost:5000/api/voshan/detection/health"
```

**Expected Response:**
```json
{
  "healthy": true,
  "modelLoaded": true
}
```

### Step 3: Check Backend Logs
Look at your Node.js backend terminal for error messages:
- Connection errors
- Timeout errors
- File path errors

### Step 4: Check ML Service Logs
Look at your Python ML service terminal for:
- Model loading errors
- Processing errors
- Import errors

## Complete Setup Checklist

- [ ] Python ML service is running on port 5001
- [ ] Node.js backend is running on port 5000
- [ ] React frontend is running on port 3000
- [ ] `backend/ml-service/models/best.pt` exists
- [ ] All Python dependencies installed (`pip install -r requirements.txt`)
- [ ] `ML_SERVICE_URL` is set correctly in `backend/.env`
- [ ] ML service health check returns "healthy"
- [ ] Backend can connect to ML service (check `/api/voshan/detection/health`)

## Still Having Issues?

1. **Check browser console** (F12) for detailed error messages
2. **Check backend terminal** for server-side errors
3. **Check ML service terminal** for Python errors
4. **Try a small test video** first to rule out file size issues
5. **Verify all services are running** before uploading

## Example Error Messages and Solutions

| Error Message | Likely Cause | Solution |
|--------------|--------------|----------|
| "Cannot connect to ML service" | ML service not running | Start Python ML service |
| "ECONNREFUSED" | Port 5001 not accessible | Check ML service is running |
| "Request timed out" | Video too large or slow processing | Try smaller video or increase timeout |
| "Model not found" | Missing best.pt file | Place model in `backend/ml-service/models/` |
| "Module not found" | Missing Python dependencies | Run `pip install -r requirements.txt` |

