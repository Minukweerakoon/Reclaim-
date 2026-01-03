# Reclaim - Real-time Suspicious Behavior Detection (Voshan)

A real-time suspicious behavior detection system using AI-powered video analysis to detect unattended bags, loitering, and suspicious movements.

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

## 📦 Project Dependencies

### Frontend Dependencies

**Core Framework:**
- `react` (^18.2.0) - React UI library
- `react-dom` (^18.2.0) - React DOM rendering
- `react-router-dom` (^6.20.0) - Client-side routing

**HTTP & Real-time:**
- `axios` (^1.6.2) - HTTP client for API requests
- `socket.io-client` (^4.6.0) - WebSocket client for real-time updates

**Development:**
- `@vitejs/plugin-react` (^4.2.1) - Vite React plugin
- `vite` (^5.0.8) - Build tool and dev server

### Backend Dependencies

**Core Framework:**
- `express` (^4.18.2) - Web application framework
- `mongoose` (^8.0.0) - MongoDB object modeling

**Utilities:**
- `dotenv` (^16.3.1) - Environment variable management
- `cors` (^2.8.5) - Cross-origin resource sharing
- `axios` (^1.6.0) - HTTP client for ML service communication
- `form-data` (^4.0.0) - Form data handling

**File Handling:**
- `multer` (^1.4.5-lts.1) - Multipart/form-data handling for file uploads

**Authentication & Security:**
- `bcryptjs` (^2.4.3) - Password hashing
- `jsonwebtoken` (^9.0.2) - JWT token generation/verification
- `express-validator` (^7.0.1) - Input validation

**Real-time Communication:**
- `socket.io` (^4.6.0) - WebSocket server for real-time alerts

**Development:**
- `nodemon` (^3.0.2) - Auto-restart on file changes
- `jest` (^29.7.0) - Testing framework

### ML Service Dependencies (Python)

**Core Framework:**
- `flask` (>=3.0.0) - Web framework
- `flask-cors` (>=4.0.0) - CORS support
- `flask-compress` (>=1.14) - Response compression
- `gunicorn` (>=21.2.0) - Production WSGI server

**Computer Vision & ML:**
- `ultralytics` (>=8.3.0) - YOLOv11 object detection
- `opencv-python` (>=4.8.0) - Computer vision library
- `numpy` (>=1.24.0) - Numerical computing
- `pillow` (>=10.0.0) - Image processing

**Data Processing:**
- `pandas` (>=2.0.0) - Data analysis and manipulation

**Real-time:**
- `python-socketio` (>=5.10.0) - WebSocket support

**Configuration:**
- `pyyaml` (>=6.0) - YAML configuration parsing
