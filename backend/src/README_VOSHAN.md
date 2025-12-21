# Voshan - Suspicious Behavior Detection Module

This module implements the suspicious behavior detection feature for the Reclaim project. All files are organized under the `voshan/` folder to keep changes separate from other contributors.

## Structure

```
backend/src/
├── controllers/voshan/
│   └── detectionController.js    # Handles detection requests
├── models/voshan/
│   └── alertModel.js              # MongoDB schema for alerts
├── routes/voshan/
│   └── detectionRoutes.js         # API routes
├── services/voshan/
│   └── mlService.js               # ML service client
└── middleware/voshan/
    └── errorHandler.js            # Error handling middleware
```

## API Endpoints

### Health Check
```
GET /api/voshan/detection/health
```
Check if ML service is running and healthy.

### Process Video
```
POST /api/voshan/detection/process-video
Content-Type: multipart/form-data

Body:
- video: Video file (mp4, avi, mov)
- cameraId: (optional) Camera identifier
- saveOutput: (optional) true/false - Save annotated video
```

### Process Frame (Real-time)
```
POST /api/voshan/detection/process-frame
Content-Type: multipart/form-data

Body:
- frame: Image file (jpeg, png)
- cameraId: (optional) Camera identifier
```

### Get Alerts
```
GET /api/voshan/detection/alerts?page=1&limit=50&type=BAG_UNATTENDED&severity=HIGH&cameraId=CAM_001&startDate=2024-01-01&endDate=2024-12-31
```

### Get Alert by ID
```
GET /api/voshan/detection/alerts/:id
```

### Get Alerts by Camera
```
GET /api/voshan/detection/alerts/camera/:cameraId
```

### Delete Alert
```
DELETE /api/voshan/detection/alerts/:id
```

## Environment Variables

Add to `.env`:
```
ML_SERVICE_URL=http://localhost:5001
```

## Dependencies

- `axios` - HTTP client for ML service communication
- `multer` - File upload handling
- `form-data` - Form data handling for file uploads

## Usage Example

```javascript
// Process video
const formData = new FormData();
formData.append('video', videoFile);
formData.append('cameraId', 'CAM_001');

const response = await fetch('/api/voshan/detection/process-video', {
  method: 'POST',
  body: formData
});

const result = await response.json();
console.log('Alerts:', result.data.alerts);
```

## Notes

- All uploads are stored in `backend/uploads/voshan/`
- Alerts are stored in MongoDB collection `voshan_alerts`
- ML service must be running on `ML_SERVICE_URL` (default: http://localhost:5001)

