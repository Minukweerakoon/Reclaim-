# Verification Guide: Suspicious Bag Detection

This guide helps you verify that the suspicious bag detection system is working correctly.

## System Overview

The system detects suspicious interactions with bags using:
1. **YOLO Model** - Detects bags (class 0) and people (class 1) in video frames
2. **Object Tracking** - Tracks objects across frames to maintain identity
3. **Behavior Detection** - Analyzes tracked objects to detect:
   - **BAG_UNATTENDED**: Bag left without owner nearby for 20+ seconds
   - **LOITER_NEAR_UNATTENDED**: Person loitering near unattended bag for 20+ seconds
   - **RUNNING**: Person running (speed > 260 pixels/second)
   - **OWNER_RETURNED**: Owner returns to unattended bag

## Prerequisites Check

### 1. Python ML Service Running
```powershell
# Check if service is running
Invoke-WebRequest -Uri "http://localhost:5001/api/v1/detect/status"
```

Expected response:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "gpu_available": false,
  "model_info": {...}
}
```

If not running:
```powershell
cd backend\voshan\ml-service
python app.py
```

### 2. Node.js Backend Running
```powershell
# Check backend health
Invoke-WebRequest -Uri "http://localhost:5000/api/health"
```

Expected response:
```json
{
  "status": "OK",
  "message": "Server is running"
}
```

### 3. MongoDB Connected
Check backend terminal for:
```
✅ MongoDB Connected: ...
   Database: reclaim
```

### 4. Frontend Running
Open browser: `http://localhost:3000`

## Testing the Detection Flow

### Step 1: Upload a Test Video

1. Go to `http://localhost:3000/voshan/upload`
2. Upload a video file containing:
   - At least one bag
   - At least one person
   - Person should leave the bag unattended for 20+ seconds

### Step 2: Monitor Processing

Watch the backend terminal for:
```
[req-xxxxx] Starting video processing...
[req-xxxxx] ML service response: { success: true, ... }
[req-xxxxx] Processing X alerts from ML service
[req-xxxxx] Sending success response with: { totalAlerts: X }
```

### Step 3: Check Results

After processing completes, you should see:
- **Total Frames**: Number of frames processed
- **Total Detections**: Number of objects detected
- **Total Alerts**: Number of suspicious behaviors detected

### Step 4: Verify Alerts

Check the alerts section for:
- **BAG_UNATTENDED** alerts (if bag left alone)
- **LOITER_NEAR_UNATTENDED** alerts (if person loiters near bag)
- **RUNNING** alerts (if person runs)
- **OWNER_RETURNED** alerts (if owner comes back)

## Expected Behavior Detection Logic

### Unattended Bag Detection
- **Trigger**: Bag detected without any person within 120 pixels for 20+ seconds
- **Alert Type**: `BAG_UNATTENDED`
- **Severity**: `MEDIUM`
- **Details**: `bag_id`, `bag_bbox`, `duration_seconds`

### Loitering Detection
- **Trigger**: Person stays within 70 pixels of an unattended bag for 20+ seconds
- **Alert Type**: `LOITER_NEAR_UNATTENDED`
- **Severity**: `HIGH`
- **Details**: `person_id`, `bag_id`, `dwell_time_seconds`

### Running Detection
- **Trigger**: Person moves faster than 260 pixels/second
- **Alert Type**: `RUNNING`
- **Severity**: `LOW`
- **Details**: `person_id`, `speed`

### Owner Returned
- **Trigger**: Person comes within 120 pixels of an unattended bag
- **Alert Type**: `OWNER_RETURNED`
- **Severity**: `INFO`
- **Details**: `bag_id`, `person_id`, `distance_px`

## Troubleshooting

### No Alerts Generated

1. **Check video content**:
   - Does the video contain bags? (YOLO class 0)
   - Does the video contain people? (YOLO class 1)
   - Is the video quality good enough for detection?

2. **Check detection thresholds**:
   - Model confidence: 0.25 (in `config.yaml`)
   - Owner max distance: 120 pixels
   - Owner absent time: 20 seconds
   - Loiter radius: 70 pixels
   - Loiter time: 20 seconds

3. **Check ML service logs**:
   - Look for "Processed X/Y frames" messages
   - Check for any error messages

### Alerts Not Saving to Database

1. **Check MongoDB connection**:
   - Verify MongoDB is running
   - Check `MONGODB_URI` in `backend/.env`
   - Look for connection errors in backend logs

2. **Check alert format**:
   - Backend expects `alert_id` field
   - Python service generates: `{type}_{frame}_{timestamp}`
   - Verify alerts have required fields: `type`, `severity`, `timestamp`, `frame`

### Connection Errors

1. **ML Service not reachable**:
   - Error: "Cannot connect to ML service"
   - Solution: Start Python ML service on port 5001

2. **Backend not reachable**:
   - Error: "Cannot connect to backend server"
   - Solution: Start Node.js backend on port 5000

## Configuration Parameters

Edit `backend/voshan/ml-service/config.yaml` to adjust detection sensitivity:

```yaml
behavior:
  owner_max_dist: 120      # Increase to detect bags as "attended" from farther away
  owner_absent_sec: 20    # Decrease to detect unattended bags faster
  loiter_near_radius: 70  # Increase to detect loitering from farther away
  loiter_near_sec: 20     # Decrease to detect loitering faster
  running_speed: 260      # Decrease to detect slower movement as "running"
```

## Verification Checklist

- [ ] Python ML service is running on port 5001
- [ ] Node.js backend is running on port 5000
- [ ] MongoDB is connected
- [ ] Frontend is accessible at localhost:3000
- [ ] Video upload page loads correctly
- [ ] Video uploads successfully
- [ ] Processing completes without errors
- [ ] Alerts are generated (if video contains suspicious behavior)
- [ ] Alerts are saved to database
- [ ] Alerts appear in Alert History page
- [ ] Real-time alerts work (if WebSocket enabled)

## Next Steps

If everything is working:
1. Test with different videos
2. Adjust detection thresholds if needed
3. Monitor alert accuracy
4. Check Alert History page for saved alerts

If issues persist:
1. Check all service logs
2. Verify all dependencies are installed
3. Test ML service health endpoint directly
4. Test backend health endpoint directly

