# Reclaim - Voshan: AI-Powered Real-Time Suspicious Behavior Detection System

## 📋 Project Overview

Voshan is an AI-powered real-time suspicious behavior detection system that analyzes video feeds to identify potential security threats. The system can detect:

- **Unattended Bags**: Detects bags left unattended for extended periods
- **Loitering**: Identifies people loitering near unattended items
- **Running/Suspicious Movement**: Detects rapid movement patterns
- **Owner Return**: Tracks when bag owners return to their items

### Key Features

- 🎥 **Video Upload & Processing**: Upload videos for offline batch analysis
- 🔴 **Real-time Detection**: Live camera feed processing with instant alerts
- 📊 **Alert Management**: View, filter, and manage detected alerts
- 🔔 **WebSocket Notifications**: Real-time alert broadcasting
- 🎯 **YOLO Object Detection**: State-of-the-art object detection using YOLOv11
- 📈 **Behavioral Analysis**: Advanced tracking and behavior pattern recognition

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              React Frontend (Port 3000)                   │  │
│  │  • Video Upload Interface                                 │  │
│  │  • Real-time Dashboard                                    │  │
│  │  • Alert History & Management                            │  │
│  │  • WebSocket Client (Socket.IO)                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              │ WebSocket (Socket.IO)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │        Node.js/Express Backend (Port 5000)               │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  API Routes                                        │  │  │
│  │  │  • /api/voshan/detection/process-video            │  │  │
│  │  │  • /api/voshan/detection/process-frame            │  │  │
│  │  │  • /api/voshan/detection/alerts                   │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Controllers                                        │  │  │
│  │  │  • Video Processing Controller                     │  │  │
│  │  │  • Alert Management Controller                     │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Services                                          │  │  │
│  │  │  • ML Service Client (HTTP)                        │  │  │
│  │  │  • WebSocket Service                               │  │  │
│  │  │  • Notification Service                            │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP (Axios)
                              │ FormData (Video Upload)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        ML SERVICE LAYER                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │      Python Flask/Gunicorn ML Service (Port 5001)        │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  YOLO Detector (YOLOv11)                          │  │  │
│  │  │  • Object Detection (Person, Bag)                   │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Object Tracker (BoTSORT)                         │  │  │
│  │  │  • Multi-object Tracking                          │  │  │
│  │  │  • Optical Flow Tracking                          │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Behavior Detector                                 │  │  │
│  │  │  • Unattended Bag Detection                       │  │  │
│  │  │  • Loitering Detection                            │  │  │
│  │  │  • Running Detection                              │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  │  ┌────────────────────────────────────────────────────┐  │  │
│  │  │  Video Processor                                   │  │  │
│  │  │  • Frame Extraction                                │  │  │
│  │  │  • Annotation & Visualization                      │  │  │
│  │  └────────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Mongoose ODM
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              MongoDB Database                            │  │
│  │  • voshan_alerts Collection                             │  │
│  │  • Alert Documents (with metadata)                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Components

1. **Frontend (React)**
   - React 18 with Vite
   - React Router for navigation
   - Socket.IO Client for real-time updates
   - Axios for HTTP requests

2. **Backend (Node.js/Express)**
   - RESTful API server
   - WebSocket server (Socket.IO)
   - File upload handling (Multer)
   - MongoDB integration (Mongoose)

3. **ML Service (Python/Flask)**
   - Flask/Gunicorn server
   - YOLOv11 object detection
   - BoTSORT object tracking
   - Behavioral analysis engine

4. **Database (MongoDB)**
   - Document-based storage
   - Alert metadata and history
   - Indexed queries for performance

---

## 🎯 Problem Statement & Solution Approach

### Problem Statement
Security threats in public spaces, such as unattended bags and suspicious activities, require immediate detection and response to prevent potential incidents.

### Solution Approach
- **Real-Time Video Analysis**: Processes live camera feeds and uploaded videos using advanced AI models to detect suspicious behaviors instantly
- **Multi-Behavior Detection**: Identifies four critical security scenarios:
  - Unattended bags left for extended periods
  - Loitering near unattended items
  - Running and rapid suspicious movements
  - Owner return tracking to distinguish threats from normal behavior
- **Prototype Implementation**: Full-stack system with React frontend, Node.js/Express backend, Python ML service, and MongoDB database
- **Automated Alert System**: Generates real-time alerts with severity levels and detailed metadata for security personnel

---

## 📦 Project Structure

```
Reclaim/
├── backend/                    # Node.js/Express Backend
│   ├── src/
│   │   ├── config/            # Configuration files
│   │   ├── controllers/       # Route controllers
│   │   │   └── voshan/        # Voshan detection controllers
│   │   ├── models/            # Database models
│   │   │   └── voshan/        # Voshan alert models
│   │   ├── routes/            # API routes
│   │   │   └── voshan/        # Voshan detection routes
│   │   ├── services/          # Business logic services
│   │   │   └── voshan/        # ML service client, WebSocket, notifications
│   │   ├── middleware/        # Custom middleware
│   │   │   └── voshan/        # Voshan error handlers
│   │   └── app.js             # Express app setup
│   ├── voshan/
│   │   └── ml-service/        # Python ML Service
│   │       ├── app.py         # Flask server
│   │       ├── config.yaml    # Configuration
│   │       ├── services/      # Detection, tracking, behavior logic
│   │       ├── utils/         # Video processing utilities
│   │       └── models/        # YOLO model files
│   └── server.js              # Server entry point
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── components/        # Reusable React components
│   │   │   └── voshan/        # Voshan-specific components
│   │   ├── pages/             # Page components
│   │   │   └── voshan/        # Voshan pages (Dashboard, Alert History)
│   │   ├── hooks/             # Custom React hooks
│   │   │   └── voshan/        # WebSocket hook
│   │   ├── services/          # API service functions
│   │   │   └── voshan/        # Detection API client
│   │   └── utils/             # Utility functions
│   └── public/                # Static files
│
└── RESEARCH_COMPONENT_DOCUMENTATION.md  # This file
```

---

## 🔧 Setup & Installation

### Prerequisites
- Node.js (v18 or higher)
- Python 3.8+
- MongoDB (local or MongoDB Atlas)
- npm or yarn
- pip (Python package manager)

### Backend Setup

1. **Install Dependencies**
```bash
cd backend
npm install
```

2. **Create `.env` file**
```env
PORT=5000
NODE_ENV=development
MONGODB_URI=mongodb://localhost:27017/reclaim
JWT_SECRET=your_jwt_secret_key_here
JWT_EXPIRE=7d
CORS_ORIGIN=http://localhost:3000
ML_SERVICE_URL=http://localhost:5001
NOTIFICATIONS_ENABLED=false
```

3. **Start Backend Server**
```bash
npm run dev  # Development mode with nodemon
# or
npm start    # Production mode
```

### ML Service Setup

1. **Install Python Dependencies**
```bash
cd backend/voshan/ml-service
pip install -r requirements.txt
```

2. **Configure `config.yaml`**
```yaml
model:
  path: "models/best.pt"
  confidence: 0.25
  device: "cuda:0"  # or "cpu" for CPU-only

behavior:
  owner_max_dist: 120      # pixels
  owner_absent_sec: 20     # seconds
  loiter_near_radius: 70   # pixels
  loiter_near_sec: 20      # seconds
  running_speed: 260       # pixels/second
```

3. **Run ML Service**
```bash
python app.py
```

Or with gunicorn (production):
```bash
gunicorn -w 4 -b 0.0.0.0:5001 app:app
```

### Frontend Setup

1. **Install Dependencies**
```bash
cd frontend
npm install
```

2. **Create `.env` file**
```env
VITE_API_URL=http://localhost:5000/api
VITE_APP_NAME=Reclaim
```

3. **Start Development Server**
```bash
npm run dev    # Development server
npm run build  # Production build
npm run preview # Preview production build
```

### MongoDB Setup

1. **Local MongoDB**
```bash
# Start MongoDB service
mongod
```

2. **MongoDB Atlas**
- Create account at https://www.mongodb.com/cloud/atlas
- Create cluster and get connection string
- Update `MONGODB_URI` in backend `.env`

---

## 📡 API Endpoints

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
- batchSize: (optional) Number of frames per batch (default: 8)
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

### WebSocket Status
```
GET /api/voshan/detection/websocket/status
```

---

## 🔌 WebSocket Events

### Client → Server

#### Join Camera Room
```javascript
socket.emit('join-camera', 'CAM_001');
```

#### Leave Camera Room
```javascript
socket.emit('leave-camera', 'CAM_001');
```

#### Subscribe to All Alerts
```javascript
socket.emit('subscribe-alerts');
```

#### Unsubscribe from Alerts
```javascript
socket.emit('unsubscribe-alerts');
```

### Server → Client

#### New Alert
```javascript
socket.on('new-alert', (alert) => {
  // {
  //   alertId: 'BAG_UNATTENDED_123_1234567890',
  //   type: 'BAG_UNATTENDED',
  //   severity: 'MEDIUM',
  //   timestamp: 1234567890,
  //   cameraId: 'CAM_001',
  //   details: { ... }
  // }
});
```

#### Connection Status
```javascript
socket.on('joined-camera', (data) => {
  console.log('Joined camera:', data.cameraId);
});

socket.on('subscribed-alerts', (data) => {
  console.log('Subscribed:', data.success);
});
```

---

## 🤖 Models & Training Information

### Model Architecture

The system uses a multi-model approach combining object detection, tracking, and behavior analysis:

#### 1. YOLOv11 Object Detection Model

**Model Details:**
- **Architecture**: YOLOv11 (Ultralytics)
- **Model File**: `backend/voshan/ml-service/models/best.pt`
- **Input Size**: 800×800 pixels (configurable)
- **Confidence Threshold**: 0.25 (default, configurable)
- **Device Support**: CUDA (GPU) or CPU
- **Framework**: PyTorch (via Ultralytics)

**Detected Classes:**
- **Class 0**: Bag (luggage, backpacks, handbags, etc.)
- **Class 1**: Person

**Model Configuration:**
```yaml
model:
  path: "models/best.pt"
  image_size: 800
  confidence: 0.25
  device: "cuda:0"  # or "cpu"
```

**Training Information:**
- **Base Model**: YOLOv11 (pre-trained on COCO dataset)
- **Training Approach**: Fine-tuned for bag and person detection
- **Training Dataset**: Custom dataset with annotated bags and persons
- **Training Framework**: Ultralytics YOLO training pipeline

**Model Performance Metrics:**
*(To be updated with actual training results)*

| Metric | Value | Notes |
|--------|-------|-------|
| **mAP@0.5** | TBD | Mean Average Precision at IoU=0.5 |
| **mAP@0.5:0.95** | TBD | Mean Average Precision at IoU=0.5:0.95 |
| **Precision (Bag)** | TBD | Precision for bag detection |
| **Recall (Bag)** | TBD | Recall for bag detection |
| **Precision (Person)** | TBD | Precision for person detection |
| **Recall (Person)** | TBD | Recall for person detection |
| **F1-Score (Bag)** | TBD | F1-score for bag detection |
| **F1-Score (Person)** | TBD | F1-score for person detection |
| **Inference Speed (GPU)** | ~30-50 FPS | Frames per second on GPU |
| **Inference Speed (CPU)** | ~5-10 FPS | Frames per second on CPU |

**Training Hyperparameters:**
*(To be updated with actual training configuration)*
- **Epochs**: TBD
- **Batch Size**: TBD
- **Learning Rate**: TBD
- **Optimizer**: TBD
- **Image Augmentation**: TBD
- **Validation Split**: TBD

**Dataset Information:**
*(To be updated with actual dataset details)*
- **Total Images**: TBD
- **Training Images**: TBD
- **Validation Images**: TBD
- **Test Images**: TBD
- **Bag Annotations**: TBD
- **Person Annotations**: TBD
- **Image Resolution**: TBD
- **Data Augmentation**: TBD

#### 2. BoTSORT Multi-Object Tracker

**Tracker Details:**
- **Algorithm**: BoTSORT (Bot-SORT with Optical Flow)
- **Implementation**: Ultralytics YOLO integrated tracker
- **Configuration**: `botsort.yaml`
- **Features**:
  - Multi-object tracking with persistent IDs
  - Optical flow-based motion prediction
  - Kalman filter for state estimation
  - Re-identification capability

**Tracking Performance:**
- **MOT Accuracy (MOTA)**: TBD
- **MOT Precision (MOTP)**: TBD
- **ID F1 Score**: TBD
- **Track Fragmentation**: TBD
- **Track Switching**: TBD

**Tracking Configuration:**
```yaml
tracking:
  tracker: "botsort.yaml"
  persist: true
```

#### 3. Behavior Detection Logic

**Algorithm Type**: Rule-based behavior analysis (not a trained model)

**Input**: Tracked objects from YOLOv11 + BoTSORT

**Output**: Behavior alerts (unattended bags, loitering, running)

**Performance Metrics:**
- **Unattended Bag Detection Accuracy**: TBD
- **Loitering Detection Accuracy**: TBD
- **Running Detection Accuracy**: TBD
- **False Positive Rate**: TBD
- **False Negative Rate**: TBD

**Behavior Detection Parameters:**
- **Owner Max Distance**: 120 pixels
- **Owner Absent Time**: 20 seconds
- **Loitering Radius**: 70 pixels
- **Loitering Time**: 20 seconds
- **Running Speed Threshold**: 260 pixels/second

### Model Integration Pipeline

```
Video Frame
    ↓
[YOLOv11 Detection]
    ↓
Detected Objects (Bags, Persons)
    ↓
[BoTSORT Tracking]
    ↓
Tracked Objects with Persistent IDs
    ↓
[Behavior Detection Logic]
    ↓
Behavior Alerts (Unattended, Loitering, Running)
```

### Model Evaluation

**Test Dataset Performance:**
*(To be updated with actual evaluation results)*

| Test Scenario | Accuracy | Precision | Recall | F1-Score |
|---------------|----------|-----------|--------|----------|
| **Bag Detection** | TBD | TBD | TBD | TBD |
| **Person Detection** | TBD | TBD | TBD | TBD |
| **Unattended Bag Detection** | TBD | TBD | TBD | TBD |
| **Loitering Detection** | TBD | TBD | TBD | TBD |
| **Running Detection** | TBD | TBD | TBD | TBD |

**Real-World Performance:**
- **Processing Speed**: 40-50% faster with batch processing optimizations
- **Memory Usage**: Optimized to ~50MB per batch (vs ~6GB for full video)
- **Frame Processing**: All frames processed (no frames skipped)
- **Alert Generation**: Real-time with <1 second latency

### Model Deployment

**Production Configuration:**
- **Model Format**: PyTorch (.pt)
- **Model Size**: TBD MB
- **Inference Engine**: Ultralytics YOLO
- **Batch Processing**: Enabled (8 frames per batch, configurable)
- **GPU Acceleration**: CUDA support (auto-fallback to CPU)

**Model Versioning:**
- **Current Version**: best.pt
- **Model Path**: `backend/voshan/ml-service/models/best.pt`
- **Version Control**: Model files excluded from git (see .gitignore)

### Model Training Process

**Training Pipeline:**
1. **Data Collection**: Gather video footage with bags and persons
2. **Data Annotation**: Label bags and persons in frames
3. **Data Preprocessing**: Resize, augment, and format images
4. **Model Training**: Fine-tune YOLOv11 on custom dataset
5. **Validation**: Evaluate on validation set
6. **Testing**: Test on held-out test set
7. **Deployment**: Export best model as `best.pt`

**Training Tools:**
- **Framework**: Ultralytics YOLO
- **Annotation Tool**: TBD (LabelImg, CVAT, etc.)
- **Training Environment**: TBD (GPU/CPU specifications)
- **Training Duration**: TBD

**Model Improvements:**
- Batch processing optimization (2-4x faster)
- Streaming frame processing (reduced memory)
- Conditional annotation (20-30% faster when output not needed)

---

## 🤖 ML Service - Behavior Detection Logic

### 1. Unattended Bag Detection

**Logic:**
- Track each bag's center position
- For each bag, find the nearest person
- Calculate distance between bag center and person center
- If distance > `OWNER_MAX_DIST` pixels:
  - Start/continue timer for owner absence
  - If timer >= `OWNER_ABSENT_SEC` seconds:
    - Mark bag as "unattended"
    - Generate `BAG_UNATTENDED` alert
- If owner returns (distance <= `OWNER_MAX_DIST`):
  - Remove bag from unattended set
  - Generate `OWNER_RETURNED` alert

**Configuration:**
- `owner_max_dist`: 120 pixels (default)
- `owner_absent_sec`: 20 seconds (default)

### 2. Loitering Detection

**Logic:**
- For each person, check distance to all unattended bags
- If person is within `LOITER_NEAR_RADIUS` of an unattended bag:
  - Start/continue loitering timer
  - If timer >= `LOITER_NEAR_SEC` seconds:
    - Generate `LOITER_NEAR_UNATTENDED` alert
- If person moves away (distance > `LOITER_NEAR_RADIUS`):
  - Reset loitering timer

**Configuration:**
- `loiter_near_radius`: 70 pixels (default)
- `loiter_near_sec`: 20 seconds (default)

### 3. Running Detection

**Logic:**
- Track person position history (last 5 seconds of positions)
- Calculate speed from position changes between frames
- Speed = distance moved per frame × FPS
- If speed > `RUNNING_SPEED`:
  - Generate `RUNNING` alert

**Configuration:**
- `running_speed`: 260 pixels/second (default)

### Alert Types

1. **`BAG_UNATTENDED`**: Bag has been unattended for the threshold time
2. **`OWNER_RETURNED`**: Owner returned to an unattended bag
3. **`LOITER_NEAR_UNATTENDED`**: Person loitering near unattended bag
4. **`RUNNING`**: Person moving faster than threshold speed

### State Management

The behavior detector maintains:
- `bag_owner_lastseen`: Dictionary mapping bag_id → last time owner was nearby
- `bag_center`: Dictionary mapping bag_id → (center_x, center_y)
- `unattended_bags`: Set of bag IDs currently marked as unattended
- `person_pos_hist`: Dictionary mapping person_id → deque of recent positions
- `near_unattend_start`: Nested dictionary mapping (person_id, bag_id) → start time of loitering

---

## ⚡ Performance Optimizations

### 1. Batch Processing for YOLO Detection
- Processes multiple frames at once using YOLO's batch prediction capability
- **Speed improvement:** 2-4x faster detection
- **Default batch size:** 8 frames per batch
- All frames are still processed, just in batches

### 2. Streaming Frame Processing
- Processes frames as they're read from video, instead of loading all frames into memory first
- **Memory improvement:** Reduces memory usage significantly for large videos
- **Speed improvement:** Starts processing immediately

### 3. Conditional Frame Annotation
- Only annotates frames when `save_output=true`
- **Speed improvement:** Saves 20-30% processing time when output video not needed
- Detection and tracking still happen on all frames

### Performance Metrics
- **Before:** ~6 minutes for 12.49 MB video
- **After:** ~3-4 minutes for same video (40-50% faster)
- **Memory usage:** Reduced from ~6GB to ~50MB per batch

---

## 📊 Database Schema

### Alert Model

```javascript
{
  alertId: String,           // Unique alert identifier
  type: String,             // BAG_UNATTENDED, LOITER_NEAR_UNATTENDED, RUNNING, OWNER_RETURNED
  severity: String,         // LOW, MEDIUM, HIGH, INFO
  timestamp: Date,          // When alert occurred
  frame: Number,            // Frame number
  cameraId: String,         // Camera identifier
  details: {
    bagId: String,          // Bag ID (if applicable)
    personId: String,       // Person ID (if applicable)
    confidence: Number,     // Detection confidence
    location: {             // Bounding box coordinates
      x: Number,
      y: Number,
      width: Number,
      height: Number
    }
  },
  videoInfo: {
    videoPath: String,      // Path to original video
    annotatedPath: String,   // Path to annotated video (if saved)
    frameSnapshot: String   // Path to frame snapshot
  },
  acknowledged: Boolean,    // Acknowledgment status
  createdAt: Date,          // Document creation time
  updatedAt: Date           // Document update time
}
```

### Indexes
- `timestamp` (descending)
- `cameraId` + `timestamp`
- `type` + `timestamp`
- `severity` + `timestamp`

---

## 🎨 Frontend Components

### Pages
- **DetectionDashboard** (`/voshan/detection`): Main dashboard with ML service status, statistics, and real-time alerts
- **AlertHistory** (`/voshan/alerts`): Historical alerts with filtering and pagination

### Components
- **AlertCard**: Displays individual alerts with color-coded severity
- **RealTimeAlertDisplay**: Shows real-time alerts from WebSocket connection

### Hooks
- **useWebSocket**: Manages WebSocket connection, handles reconnection, subscribes to alerts

### Services
- **detectionApi**: API client for all detection endpoints

---

## 🔒 Security Considerations

- **Input Validation**: Express-validator for request validation and sanitization
- **Error Handling**: Comprehensive error handling that doesn't expose sensitive system information
- **CORS Configuration**: Proper CORS setup for secure cross-origin requests
- **File Upload Security**: Multer middleware with file type and size validation
- **Environment Variables**: Sensitive configuration stored in `.env` files (not committed)

---

## 📈 Design Excellence & Contributions

### Architecture Excellence
- **Multi-Layered Architecture**: Separation of concerns with Client, Application, ML Service, and Data layers
- **Microservices Design**: Independent ML service allows for horizontal scaling
- **Real-Time Communication**: WebSocket (Socket.IO) implementation for instant alert broadcasting

### Technical Innovation
- **State-of-the-Art AI Models**: 
  - YOLOv11 for high-accuracy object detection
  - BoTSORT for robust multi-object tracking
  - Optical flow analysis for movement pattern recognition
- **Advanced Behavioral Analysis**: Custom behavior detection logic combining object tracking, temporal analysis, and spatial relationships
- **Performance Optimization**: Batch processing, streaming frame processing, conditional annotation

### Code Quality & Maintainability
- **Modular Design**: Organized codebase with clear separation between frontend, backend, and ML service
- **Error Handling**: Comprehensive error handling middleware and graceful degradation
- **API Design**: RESTful endpoints with proper HTTP status codes and error responses
- **Documentation**: Extensive inline documentation

---

## 🧪 Testing

### Test ML Service Health
```bash
curl http://localhost:5000/api/voshan/detection/health
```

### Test Video Processing
```bash
curl -X POST http://localhost:5000/api/voshan/detection/process-video \
  -F "video=@test_video.mp4" \
  -F "cameraId=CAM_001" \
  -F "saveOutput=true"
```

### Test WebSocket Connection
```bash
# Using wscat (install: npm install -g wscat)
wscat -c ws://localhost:5000/api/voshan/socket.io

# In wscat:
> emit subscribe-alerts
> emit join-camera CAM_001
```

### Test Alert Retrieval
```bash
curl http://localhost:5000/api/voshan/detection/alerts?page=1&limit=50&type=BAG_UNATTENDED
```

---

## 🚀 Future Enhancements

- Multi-camera support with camera grouping and management
- Machine learning model fine-tuning based on deployment environment
- Advanced analytics dashboard with trend analysis and reporting
- Mobile application for on-the-go monitoring
- Email/SMS/Push notification implementation
- Video clip storage for alert evidence
- Advanced filtering and export functionality
- Charts and graphs for alert statistics
- Multi-threading for independent operations
- Adaptive batch sizing based on available memory

---

## 📚 Dependencies

### Frontend
- `react` (^18.2.0) - React UI library
- `react-dom` (^18.2.0) - React DOM rendering
- `react-router-dom` (^6.20.0) - Client-side routing
- `axios` (^1.6.2) - HTTP client
- `socket.io-client` (^4.6.0) - WebSocket client
- `vite` (^5.0.8) - Build tool

### Backend
- `express` (^4.18.2) - Web framework
- `mongoose` (^8.0.0) - MongoDB ODM
- `socket.io` (^4.6.0) - WebSocket server
- `multer` (^1.4.5-lts.1) - File upload handling
- `axios` (^1.6.0) - HTTP client
- `form-data` (^4.0.0) - Form data handling
- `dotenv` (^16.3.1) - Environment variables
- `cors` (^2.8.5) - CORS support

### ML Service (Python)
- `flask` (>=3.0.0) - Web framework
- `flask-cors` (>=4.0.0) - CORS support
- `flask-compress` (>=1.14) - Response compression
- `gunicorn` (>=21.2.0) - Production WSGI server
- `ultralytics` (>=8.3.0) - YOLOv11 object detection
- `opencv-python` (>=4.8.0) - Computer vision library
- `numpy` (>=1.24.0) - Numerical computing
- `pillow` (>=10.0.0) - Image processing
- `pandas` (>=2.0.0) - Data analysis
- `python-socketio` (>=5.10.0) - WebSocket support
- `pyyaml` (>=6.0) - YAML configuration

---

## 📝 Notes

- All Voshan-related files are organized under `voshan/` folders to keep changes separate from other contributors
- ML service must be running on `ML_SERVICE_URL` (default: http://localhost:5001)
- Uploads are stored in `backend/uploads/voshan/`
- Alerts are stored in MongoDB collection `voshan_alerts`
- For best performance, use GPU (CUDA) by setting `device: "cuda:0"` in `config.yaml`
- WebSocket is available at `ws://localhost:5000/api/voshan/socket.io`
- All frames are processed (no frames are skipped) even with batch processing optimizations

---

## 🎯 User Requirements Addressed

1. **Real-Time Threat Detection**
   - Live camera feed processing with instant alert generation
   - WebSocket-based real-time notifications to all connected clients

2. **Video Analysis Capabilities**
   - Upload and process video files for offline batch analysis
   - Support for multiple video formats (MP4, AVI, MOV)
   - Frame-by-frame analysis with accurate timestamp tracking

3. **Alert Management System**
   - Comprehensive alert history with filtering capabilities
   - Filter by alert type, severity, camera ID, and date range
   - Detailed alert metadata including frame snapshots and detection confidence

4. **User-Friendly Interface**
   - Intuitive React-based dashboard for monitoring and management
   - Real-time alert notifications with visual indicators
   - Video upload interface with progress tracking

5. **Scalable Architecture**
   - Microservices design allowing independent scaling of components
   - RESTful API for integration with existing security systems
   - MongoDB database for efficient alert storage and retrieval

---

## 📖 References

### Implementation Steps
1. **ML Service Development**: Python Flask service with YOLOv11 and BoTSORT
2. **Behavior Detection Logic**: Extracted from YOLOv8/YOLOv11 notebooks
3. **Node.js Integration**: Backend API with MongoDB integration
4. **Real-time Features**: WebSocket implementation for live alerts
5. **Frontend Integration**: React components and pages for user interface
6. **Performance Optimizations**: Batch processing and streaming frame processing

### Key Files
- **ML Service**: `backend/voshan/ml-service/app.py`
- **Behavior Detection**: `backend/voshan/ml-service/services/behavior.py`
- **Backend Controller**: `backend/src/controllers/voshan/detectionController.js`
- **Frontend Dashboard**: `frontend/src/pages/voshan/DetectionDashboard.jsx`
- **WebSocket Service**: `backend/src/services/voshan/websocketService.js`

---

*This documentation consolidates all research component information for the Voshan suspicious behavior detection system.*

