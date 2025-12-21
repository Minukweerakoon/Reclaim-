# ML Service - Suspicious Behavior Detection

Python microservice for real-time suspicious behavior detection using YOLOv11.

## Features

- **Object Detection**: Detects bags and persons using YOLOv11
- **Multi-Object Tracking**: Uses BoTSORT for consistent object IDs
- **Behavior Detection**:
  - Unattended bag detection
  - Loitering near unattended bags
  - Running detection (future)
- **Video Processing**: Process video files and generate annotated outputs
- **Real-time Processing**: Process individual frames for streaming

## Setup

### 1. Install Dependencies

```bash
cd backend/voshan/ml-service
pip install -r requirements.txt
```

### 2. Configure

Edit `config.yaml` to adjust:
- Model path
- Detection confidence threshold
- Behavior detection parameters
- API host/port

### 3. Run Service

```bash
python app.py
```

Or with gunicorn (production):
```bash
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

## API Endpoints

### Health Check
```
GET /api/v1/detect/status
```

### Process Video
```
POST /api/v1/detect/process-video
Content-Type: multipart/form-data

Parameters:
- video_file: Video file
- save_output: true/false (default: true)
```

### Process Frame (Real-time)
```
POST /api/v1/detect/process-frame
Content-Type: multipart/form-data

Parameters:
- frame: Image file
- camera_id: Optional camera identifier
```

## Directory Structure

```
ml-service/
├── app.py                 # Flask server
├── config.yaml            # Configuration
├── requirements.txt       # Python dependencies
├── models/
│   └── best.pt            # YOLOv11 trained model
├── services/
│   ├── detector.py        # YOLO detection
│   ├── tracker.py         # BoTSORT tracking
│   └── behavior.py        # Behavior detection
├── utils/
│   ├── video.py           # Video processing
│   └── alerts.py         # Alert management
├── uploads/               # Temporary uploads
└── outputs/              # Processed videos and alerts
```

## Usage Example

```python
import requests

# Process video
with open('video.mp4', 'rb') as f:
    response = requests.post(
        'http://localhost:5001/api/v1/detect/process-video',
        files={'video_file': f},
        data={'save_output': 'true'}
    )

result = response.json()
print(f"Found {result['total_alerts']} alerts")
```

## Notes

- Ensure GPU is available for best performance (set `device: "cuda:0"` in config.yaml)
- For CPU-only, set `device: "cpu"` in config.yaml
- Model file (`best.pt`) must be present in `models/` directory

