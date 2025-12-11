# Step 4: Node.js Integration - Complete ✅

## Overview

Node.js backend integration for suspicious behavior detection has been completed. All files are organized under `voshan/` folders to keep changes separate from other contributors.

## Structure Created

```
backend/src/
├── controllers/voshan/
│   └── detectionController.js    ✅ Handles all detection requests
├── models/voshan/
│   └── alertModel.js              ✅ MongoDB schema for alerts
├── routes/voshan/
│   └── detectionRoutes.js         ✅ API routes with file upload
├── services/voshan/
│   └── mlService.js               ✅ ML service HTTP client
└── middleware/voshan/
    └── errorHandler.js            ✅ Error handling middleware
```

## Files Created

### 1. ML Service Client (`services/voshan/mlService.js`)
- Communicates with Python ML service
- Methods:
  - `checkHealth()` - Check ML service status
  - `processVideo()` - Process video files
  - `processFrame()` - Process single frames
  - `processUploadedVideo()` - Handle uploaded videos

### 2. Detection Controller (`controllers/voshan/detectionController.js`)
- Handles all detection-related requests
- Methods:
  - `checkMLServiceHealth()` - Health check endpoint
  - `processVideo()` - Process uploaded video
  - `processFrame()` - Process single frame
  - `getAlerts()` - Get all alerts with filtering
  - `getAlertById()` - Get specific alert
  - `getAlertsByCamera()` - Get alerts by camera
  - `deleteAlert()` - Delete alert

### 3. Alert Model (`models/voshan/alertModel.js`)
- MongoDB schema for alerts
- Fields:
  - `alertId` - Unique alert identifier
  - `type` - Alert type (BAG_UNATTENDED, LOITER_NEAR_UNATTENDED, etc.)
  - `severity` - Alert severity (LOW, MEDIUM, HIGH, INFO)
  - `timestamp` - When alert occurred
  - `frame` - Frame number
  - `cameraId` - Camera identifier
  - `details` - Alert-specific details
  - `videoInfo` - Video evidence paths
  - `acknowledged` - Acknowledgment status

### 4. Detection Routes (`routes/voshan/detectionRoutes.js`)
- API endpoints:
  - `GET /api/voshan/detection/health` - Health check
  - `POST /api/voshan/detection/process-video` - Process video
  - `POST /api/voshan/detection/process-frame` - Process frame
  - `GET /api/voshan/detection/alerts` - Get all alerts
  - `GET /api/voshan/detection/alerts/:id` - Get alert by ID
  - `GET /api/voshan/detection/alerts/camera/:cameraId` - Get alerts by camera
  - `DELETE /api/voshan/detection/alerts/:id` - Delete alert

### 5. Error Handler (`middleware/voshan/errorHandler.js`)
- Handles multer file upload errors
- Handles other route-specific errors

## Dependencies Added

Updated `package.json` with:
- `axios` - HTTP client for ML service
- `multer` - File upload handling
- `form-data` - Form data handling

## Configuration

### Environment Variables

Added to `env.example.txt`:
```
ML_SERVICE_URL=http://localhost:5001
```

### Routes Integration

Updated `src/app.js` to include:
```javascript
app.use('/api/voshan/detection', require('./routes/voshan/detectionRoutes'));
```

## API Usage Examples

### Process Video
```bash
curl -X POST http://localhost:5000/api/voshan/detection/process-video \
  -F "video=@test_video.mp4" \
  -F "cameraId=CAM_001" \
  -F "saveOutput=true"
```

### Get Alerts
```bash
curl http://localhost:5000/api/voshan/detection/alerts?page=1&limit=50&type=BAG_UNATTENDED
```

### Health Check
```bash
curl http://localhost:5000/api/voshan/detection/health
```

## Database

- Collection: `voshan_alerts`
- Indexes created for efficient querying:
  - `timestamp` (descending)
  - `cameraId` + `timestamp`
  - `type` + `timestamp`
  - `severity` + `timestamp`

## File Storage

- Upload directory: `backend/uploads/voshan/`
- Automatically created if doesn't exist
- Temporary files cleaned up after processing

## Next Steps

1. **Install Dependencies:**
   ```bash
   cd backend
   npm install
   ```

2. **Set Environment Variables:**
   - Copy `env.example.txt` to `.env`
   - Set `ML_SERVICE_URL` to your Python ML service URL

3. **Start Services:**
   - Start Python ML service: `cd backend/ml-service && python app.py`
   - Start Node.js backend: `cd backend && npm run dev`

4. **Test Integration:**
   - Check health: `GET /api/voshan/detection/health`
   - Upload test video: `POST /api/voshan/detection/process-video`

## Notes

- All files are in `voshan/` folders to keep changes separate
- No impact on existing project structure
- All scenarios and processes remain unchanged
- Ready for frontend integration

