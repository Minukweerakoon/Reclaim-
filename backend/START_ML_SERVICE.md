# How to Start the ML Service

## Quick Start

The ML service files are located in: `backend/voshan/ml-service/`

### Step 1: Navigate to ML Service Directory
```powershell
cd backend\voshan\ml-service
```

### Step 2: Install Python Dependencies (First Time Only)
```powershell
pip install -r requirements.txt
```

### Step 3: Start the ML Service
```powershell
python app.py
```

You should see:
```
🚀 Starting ML Service on 0.0.0.0:5001
✅ Services initialized successfully
```

### Step 4: Verify It's Running
Open a new terminal and test:
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/api/v1/detect/status"
```

You should get a JSON response with `"status": "healthy"`

## Keep It Running

**Important:** Keep the ML service terminal window open while using the video upload feature. The service must be running for video processing to work.

## Troubleshooting

### "Module not found" error
- Install dependencies: `pip install -r requirements.txt`

### "Model not found" error
- Ensure `models/best.pt` exists in `backend/voshan/ml-service/models/`
- ✅ Already confirmed: Model file exists (18.32 MB)

### Port 5001 already in use
- Check what's using the port: `netstat -ano | findstr :5001`
- Stop the other service or change the port in `app.py`

### Connection refused
- Make sure the service is running
- Check firewall settings
- Verify `ML_SERVICE_URL` in `backend/.env` is `http://localhost:5001`

