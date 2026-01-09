# 🔐  Multi-Device Behavior Monitoring System

*(Backend, ML & Real-Time Intelligence)*

## 🧠 System Overview

This system is an **AI-powered IoT security platform** designed to learn how a user’s devices normally move and behave together inside a campus environment, and detect **abnormal or suspicious activity in real time**.

The backend uses **Flask + SocketIO + MongoDB + Machine Learning** to track device locations, analyze behavior patterns, and raise alerts when anomalies are detected.

---

## 🧩 Backend Architecture (Flask + Python)

| File                   | Responsibility                                                       |
| ---------------------- | -------------------------------------------------------------------- |
| `app.py`               | Main Flask server, REST APIs, and Socket.IO real-time communication  |
| `ml_model.py`          | Machine learning training, feature extraction, and anomaly detection |
| `behavior_analyzer.py` | Real-time device behavior tracking and pattern logging               |
| `models/`              | Stores trained ML models (`.pkl`) per user                           |

### 🗄 Database (MongoDB)

The system uses MongoDB with the following collections:

* `users`
* `devices`
* `locations`
* `behaviors`

These collections store device positions, movement history, and learned behavior patterns.

---

## 🖥 Frontend (React)

The frontend provides a real-time visualization and control interface:

* Login & Registration system
* Live dashboard showing all devices
* Real-time campus map
* Location tracking view
* 6 modular UI components for device and user management

The frontend communicates with the backend using:

* REST APIs
* WebSockets (Socket.IO) for live updates

---

## 🗺 Virtual Campus Mapping

The physical campus is digitally modeled as **6 logical sections**:

| Section        |
| -------------- |
| Main Building  |
| Library        |
| New Building   |
| Canteen        |
| Sports Complex |
| Admin Block    |

Each section is mapped as a **12 × 12 meter grid**.
All device locations are mapped to these sections for behavior learning and anomaly detection.

---

## 📍 Smart Location Validation

To improve GPS reliability, the backend applies a **location filtering system**:

| Accuracy    | Action                    |
| ----------- | ------------------------- |
| > 50 meters | Rejected                  |
| < 3 meters  | Anchored as trusted       |
| 3–50 meters | Drift limited to 3 meters |

This prevents false movement caused by GPS noise.

---

## 🤖 Machine Learning System

### Models Used

Each user has their own trained ML model saved as:

```
backend/models/{user_email}_model.pkl
```

The system uses **two models together**:

| Model                | Purpose                         |
| -------------------- | ------------------------------- |
| Isolation Forest     | Detects abnormal behavior       |
| K-Means (3 clusters) | Learns normal movement patterns |

---

### 📊 Feature Engineering (16 Features)

For every pair of devices, the system extracts:

* Distance between devices
* Campus section IDs
* Movement speed of each device
* Speed difference between devices
* Time of day
* Day of week
* Whether devices move together
* Entry / exit from campus
* Historical movement consistency

These features represent **how devices normally behave together**.

---

## 🧪 Model Training Flow

A model is trained when a user has **at least 2 devices**.

Training process:

```
User adds 2+ devices
        ↓
Live tracking starts
        ↓
Behavior data collected
(5 minutes OR 30 samples)
        ↓
Features extracted
        ↓
Isolation Forest + KMeans trained
        ↓
Model saved to disk (.pkl)
        ↓
Real-time anomaly detection enabled
```

Model parameters:

* Isolation Forest:

  * `n_estimators = 150`
  * `contamination = 0.15`
* KMeans:

  * `clusters = 3`

---

## 🚨 Anomaly Detection

The ML system continuously analyzes device behavior and detects:

* Devices suddenly far apart
* One device leaving campus alone
* Unusual movement speed (> 5 m/s)
* Being in unexpected campus sections
* Unusual time-of-day movement patterns

When an anomaly is detected, it is instantly sent to the frontend.

---

## ⚡ Real-Time Communication (Socket.IO)

The system uses **Flask-SocketIO** to provide:

* Live location updates
* ML training progress
* Training completion status
* Real-time anomaly alerts

This makes the dashboard update instantly without page refresh.

---

## 🎯 Why This Is Powerful

Unlike traditional tracking systems, this project:

* Learns **normal behavior**
* Detects **abnormal deviations**
* Works **in real-time**
* Uses **AI instead of static rules**


##Additional Feature For the WEBSITE

# Prediction analyse and Reminder System

A comprehensive smart Lost and Found management system with real-time risk prediction for Future Lost Happen Locataions ,Time,Places in University, ML-powered analytics, and Remind System for set reminders to collect the  stored items while leaving the stored places .

## Table of Contents
- [Project Overview](#project-overview)
- [System Architecture](#system-architecture)
- [Technologies Used](#technologies-used)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Machine Learning Model](#machine-learning-model)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Project Overview

Lost and Found ConnectPlus is an intelligent management system designed to streamline the handling of lost and found items with advanced machine learning capabilities. The system provides real-time risk assessment, predictive analytics, and automated incident management.

**Key Capabilities:**
- Real-time risk prediction using ensemble ML models
- IoT device integration for automated item tracking
- Calendar-based zone booking system
- SMS and IVR reminder automation
- Advanced analytics dashboard with data visualizations
- Multi-role user management (Admin, Staff, User)
- CSV data import/export functionality
- Geolocation-based item tracking with interactive maps

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         React Frontend (Vite + Material-UI)              │   │
│  │  - Dashboard  - Analytics  - Item Management             │   │
│  │  - Zone Booking  - Device Monitoring  - Reports          │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────────────┐
│                      APPLICATION LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Node.js/Express Backend API                    │   │
│  │                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │ Auth Service │  │ Item Service │  │ Risk Service │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │Alert Service │  │ Zone Service │  │ Device Mgmt  │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  │                                                           │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │   │
│  │  │ SMS Reminders│  │  IVR Calling │  │  Scheduler   │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↕ HTTP/REST API
┌─────────────────────────────────────────────────────────────────┐
│                    ML/AI SERVICE LAYER                           │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │         Python FastAPI ML Service (Port 5001)            │   │
│  │                                                           │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │           Ensemble ML Models                       │  │   │
│  │  │  • Random Forest Classifier                        │  │   │
│  │  │  • XGBoost Classifier                              │  │   │
│  │  │  • LightGBM Classifier                             │  │   │
│  │  │  • CatBoost Classifier                             │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  │                                                           │   │
│  │  ┌────────────────────────────────────────────────────┐  │   │
│  │  │         Feature Engineering Pipeline               │  │   │
│  │  │  • Time-based features                             │  │   │
│  │  │  • Rolling window aggregations                     │  │   │
│  │  │  • Categorical encoding                            │  │   │
│  │  │  • Feature importance analysis (SHAP)              │  │   │
│  │  └────────────────────────────────────────────────────┘  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │              MongoDB Database (NoSQL)                    │   │
│  │                                                           │   │
│  │  Collections:                                            │   │
│  │  • Users            • Stored Items      • Devices        │   │
│  │  • Alerts           • Zone Bookings     • Risk Snapshots │   │
│  │  • SMS Reminders    • IVR Calls         • Device Pings   │   │
│  │  • Closure Events   • OTP Sessions      • Bookings       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   SMS API    │  │   IVR API    │  │  Weather API │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

### Architecture Components

**Frontend (React + Vite)**
- Single Page Application with React Router
- Material-UI and Bootstrap for responsive design
- Real-time data visualization with charts
- Leaflet maps for geolocation tracking
- Axios for API communication

**Backend (Node.js + Express)**
- RESTful API architecture
- JWT-based authentication and authorization
- Role-based access control (RBAC)
- Scheduled tasks with node-cron
- Multer for file uploads
- Express-validator for input validation

**ML Service (Python + FastAPI)**
- Microservice architecture for ML predictions
- Ensemble learning with multiple algorithms
- Real-time risk assessment API
- Model training and retraining capabilities
- Feature importance analysis with SHAP
- Automated data preprocessing pipeline

**Database (MongoDB)**
- NoSQL document-based storage
- Mongoose ODM for schema validation
- Indexing for optimized queries
- Time-series data for analytics

## Technologies Used

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | ^18.2.0 | UI Framework |
| Vite | ^5.0.0 | Build Tool & Dev Server |
| Material-UI | ^5.14.17 | UI Component Library |
| Bootstrap | ^5.3.3 | CSS Framework |
| React Router | ^6.20.0 | Client-side Routing |
| Axios | ^1.6.2 | HTTP Client |
| Leaflet | ^1.9.4 | Interactive Maps |
| React Toastify | ^9.1.3 | Toast Notifications |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Node.js | - | JavaScript Runtime |
| Express | ^4.18.2 | Web Framework |
| MongoDB | - | NoSQL Database |
| Mongoose | ^7.6.3 | MongoDB ODM |
| JWT | ^9.0.2 | Authentication |
| bcryptjs | ^2.4.3 | Password Hashing |
| dotenv | ^16.3.1 | Environment Variables |
| multer | ^2.0.2 | File Upload Handling |
| node-cron | ^4.2.1 | Task Scheduling |
| cors | ^2.8.5 | Cross-Origin Resource Sharing |
| express-validator | ^7.0.1 | Input Validation |
| axios | ^1.6.0 | HTTP Client |
| csv-parser | ^3.2.0 | CSV Processing |

### ML/AI Service
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Programming Language |
| FastAPI | 0.104.1 | Web Framework |
| scikit-learn | 1.3.2 | Machine Learning |
| XGBoost | 2.0.3 | Gradient Boosting |
| LightGBM | 4.1.0 | Gradient Boosting |
| CatBoost | 1.2.2 | Gradient Boosting |
| pandas | 2.1.4 | Data Manipulation |
| numpy | 1.26.2 | Numerical Computing |
| SHAP | 0.44.0 | Model Interpretability |
| matplotlib | 3.8.2 | Data Visualization |
| seaborn | 0.13.0 | Statistical Visualization |
| imbalanced-learn | 0.11.0 | Handling Imbalanced Data |
| joblib | 1.3.2 | Model Serialization |
| uvicorn | 0.24.0 | ASGI Server |

## Features

### Core Features
- User authentication and authorization with JWT
- Role-based access control (Admin, Staff, User)
- Real-time item tracking and management
- Advanced search and filtering
- Geolocation-based item mapping
- File upload and image management
- CSV data import/export

### ML-Powered Features
- Real-time risk prediction for lost items
- Incident forecasting (2-hour prediction window)
- Ensemble ML models (Random Forest, XGBoost, LightGBM, CatBoost)
- Feature importance analysis
- Model performance metrics and monitoring
- Automated model retraining
- Historical trend analysis

### Automation Features
- Automated SMS reminders
- IVR call scheduling and tracking
- Zone closure event management
- Scheduled report generation
- Device activity monitoring
- Automated alert generation

### Analytics & Reporting
- Interactive dashboards
- Real-time analytics
- Risk assessment visualization
- Device activity reports
- Zone utilization statistics
- Custom date range filtering
- Export capabilities

### Device Management
- IoT device integration
- Real-time device status monitoring
- Activity tracking and logging
- Device ping monitoring
- Automated device alerts

### Zone & Booking Management
- Calendar-based zone booking
- Availability checking
- Booking conflict resolution
- Zone closure management
- Automated notifications

## Prerequisites

Before installing, ensure you have the following installed:

- **Node.js** (v18.0.0 or higher)
- **Python** (v3.11 or higher)
- **MongoDB** (v6.0 or higher)
- **Git** (for cloning the repository)
- **npm** or **yarn** (package managers)

**Optional:**
- MongoDB Compass (for database visualization)
- Postman (for API testing)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/lost-and-found-connectplus-final.git
cd lost-and-found-connectplus-final
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install dependencies
npm install

# Create .env file
cp .env.example .env

# Edit .env with your configuration
# See Configuration section below
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Create .env file (if needed)
cp .env.example .env
```

### 4. ML Service Setup

```bash
# Navigate to ML service directory
cd ../ml-service

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 5. Database Setup

**Option 1: Local MongoDB**
```bash
# Start MongoDB service
# On Windows (if installed as service):
net start MongoDB

# On macOS/Linux:
sudo systemctl start mongod
```

**Option 2: MongoDB Atlas (Cloud)**
- Create account at https://www.mongodb.com/atlas
- Create a new cluster
- Get connection string
- Update MONGODB_URI in backend .env

### 6. Seed Database (Optional)

```bash
# Navigate to backend directory
cd backend

# Run seed script
npm run seed
```

## Configuration

### Backend Configuration (.env)

Create a `.env` file in the `backend` directory:

```env
# Server Configuration
NODE_ENV=development
PORT=5000
FRONTEND_URL=http://localhost:5173

# Database
MONGODB_URI=mongodb://localhost:27017/lost-and-found

# JWT Authentication
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production

# ML Service
ML_SERVICE_URL=http://localhost:5001

# SMS Configuration (Optional)
SMS_API_KEY=your-sms-api-key
SMS_API_URL=https://api.sms-provider.com/send

# IVR Configuration (Optional)
IVR_API_KEY=your-ivr-api-key
IVR_API_URL=https://api.ivr-provider.com/call

# Weather API (Optional)
WEATHER_API_KEY=your-weather-api-key
WEATHER_API_URL=https://api.openweathermap.org/data/2.5

# Timezone
TZ=Asia/Colombo
```

### Frontend Configuration

Create a `.env` file in the `frontend` directory:

```env
VITE_API_BASE_URL=http://localhost:5000
VITE_ML_API_BASE_URL=http://localhost:5001
```

### ML Service Configuration

The ML service reads configuration from environment variables. Create a `.env` file in the `ml-service` directory:

```env
# Service Configuration
ML_SERVICE_PORT=5001
MODEL_PATH=./models/risk_model.pkl

# Model Training Parameters
TRAIN_TEST_SPLIT=0.2
RANDOM_STATE=42
N_ESTIMATORS=100

# Feature Engineering
ROLLING_WINDOW_1H=1
ROLLING_WINDOW_6H=6
ROLLING_WINDOW_24H=24
```

## Running the Application

### Development Mode

**1. Start MongoDB**
```bash
# Ensure MongoDB is running
# Check with:
mongosh --eval "db.version()"
```

**2. Start Backend Server**
```bash
cd backend
npm run dev
# Backend runs on http://localhost:5000
```

**3. Start ML Service**
```bash
cd ml-service
# Activate venv first
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Train model (first time only)
python train.py

# Start service
python main.py
# ML service runs on http://localhost:5001
```

**4. Start Frontend**
```bash
cd frontend
npm run dev
# Frontend runs on http://localhost:5173
```

**5. Access the Application**
- Frontend: http://localhost:5173
- Backend API: http://localhost:5000
- ML API: http://localhost:5001
- ML API Docs: http://localhost:5001/docs

### Production Mode

**Backend:**
```bash
cd backend
npm start
```

**Frontend:**
```bash
cd frontend
npm run build
npm run preview
```

**ML Service:**
```bash
cd ml-service
uvicorn main:app --host 0.0.0.0 --port 5001 --workers 4
```

## API Documentation

### Authentication Endpoints

```
POST   /api/auth/register          - Register new user
POST   /api/auth/login             - Login user
GET    /api/auth/me                - Get current user
PUT    /api/auth/profile           - Update profile
```

### Item Management Endpoints

```
GET    /api/stored-items           - Get all items
GET    /api/stored-items/:id       - Get item by ID
POST   /api/stored-items           - Create new item
PUT    /api/stored-items/:id       - Update item
DELETE /api/stored-items/:id       - Delete item
POST   /api/stored-items/upload    - Upload item image
```

### Risk Prediction Endpoints

```
GET    /api/risk/current           - Get current risk assessment
POST   /api/risk/predict           - Predict risk for parameters
GET    /api/risk/history           - Get risk history
GET    /api/risk/analytics         - Get risk analytics
```

### ML Service Endpoints

```
GET    /health                     - Health check
POST   /api/predict                - Predict incident risk
GET    /api/model/info             - Get model information
GET    /api/model/feature-importance - Get feature importance
POST   /api/train                  - Trigger model training
POST   /api/upload/training-data   - Upload training data
```

### Device Management Endpoints

```
GET    /api/devices                - Get all devices
GET    /api/devices/:id            - Get device by ID
POST   /api/devices                - Register device
PUT    /api/devices/:id            - Update device
DELETE /api/devices/:id            - Delete device
POST   /api/devices/:id/ping       - Record device ping
GET    /api/devices/:id/activity   - Get device activity
```

### Zone Booking Endpoints

```
GET    /api/zone-bookings          - Get all bookings
GET    /api/zone-bookings/:id      - Get booking by ID
POST   /api/zone-bookings          - Create booking
PUT    /api/zone-bookings/:id      - Update booking
DELETE /api/zone-bookings/:id      - Cancel booking
GET    /api/zone-bookings/availability - Check availability
```

### Admin Endpoints

```
GET    /api/admin/users            - Get all users
PUT    /api/admin/users/:id        - Update user
DELETE /api/admin/users/:id        - Delete user
GET    /api/admin/stats            - Get system statistics
GET    /api/admin/reports          - Generate reports
```

For complete API documentation, visit http://localhost:5001/docs (ML Service) when running.

## Machine Learning Model

### Model Architecture

The system uses an ensemble learning approach combining multiple algorithms:

1. **Random Forest Classifier** - Robust baseline model
2. **XGBoost** - High-performance gradient boosting
3. **LightGBM** - Fast gradient boosting for large datasets
4. **CatBoost** - Handles categorical features natively

### Features Used

**Time-based Features:**
- Hour of day
- Day of week
- Is weekend
- Is peak hour

**Location Features:**
- Encoded location ID
- Historical incident count for location

**Crowd Features:**
- Current crowd level
- Average crowd level (6-hour rolling window)

**Environmental Features:**
- Weather condition
- Day type (weekday/weekend)

**Rolling Features:**
- Incidents in last 1 hour
- Incidents in last 6 hours
- Incidents in last 24 hours

**Item Features:**
- Item type
- Historical lost count

### Model Performance

Current model metrics (trained on historical data):
- **Accuracy**: ~85-92%
- **Precision**: ~80-88%
- **Recall**: ~75-85%
- **F1 Score**: ~78-86%
- **ROC-AUC**: ~88-94%

### Training the Model

```bash
cd ml-service
python train.py

# With custom data
python train.py --data-path ./data/custom_data.csv

# With hyperparameter tuning
python train.py --tune-hyperparameters
```

### Model Interpretability

The system uses SHAP (SHapley Additive exPlanations) for model interpretability:
- Feature importance ranking
- Individual prediction explanations
- Global model behavior analysis

Access feature importance via:
```
GET http://localhost:5001/api/model/feature-importance
```

## Project Structure

```
lost-and-found-connectplus-final/
├── backend/
│   ├── src/
│   │   ├── config/           # Configuration files
│   │   │   ├── db.js
│   │   │   ├── env.js
│   │   │   └── adaptiveSystemSetup.js
│   │   ├── middleware/       # Express middleware
│   │   │   └── auth.js
│   │   ├── models/           # Mongoose models
│   │   │   ├── User.js
│   │   │   ├── StoredItem.js
│   │   │   ├── Device.js
│   │   │   ├── Alert.js
│   │   │   ├── Zone.js
│   │   │   ├── ZoneBooking.js
│   │   │   ├── RiskSnapshot.js
│   │   │   ├── SmsReminder.js
│   │   │   ├── IvrCall.js
│   │   │   └── ...
│   │   ├── routes/           # API routes
│   │   │   ├── authRoutes.js
│   │   │   ├── adminRoutes.js
│   │   │   ├── deviceRoutes.js
│   │   │   ├── riskRoutes.js
│   │   │   ├── storedItemRoutes.js
│   │   │   └── ...
│   │   ├── services/         # Business logic
│   │   │   ├── pythonMLService.js
│   │   │   ├── reminderScheduler.js
│   │   │   └── ...
│   │   └── server.js         # Express app entry
│   ├── data/                 # Data files
│   ├── package.json
│   └── .env
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   │   ├── Dashboard/
│   │   │   ├── Items/
│   │   │   ├── Analytics/
│   │   │   ├── Devices/
│   │   │   └── ...
│   │   ├── pages/            # Page components
│   │   │   ├── Login.jsx
│   │   │   ├── Dashboard.jsx
│   │   │   ├── Items.jsx
│   │   │   └── ...
│   │   ├── services/         # API services
│   │   │   ├── api.js
│   │   │   └── authService.js
│   │   ├── context/          # React context
│   │   ├── layout/           # Layout components
│   │   ├── styles/           # CSS files
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── public/               # Static assets
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── .env
├── ml-service/
│   ├── models/               # Trained models
│   │   ├── risk_model.pkl
│   │   └── model_metrics.json
│   ├── data/                 # Training data
│   │   └── risk_data.csv
│   ├── main.py               # FastAPI application
│   ├── train.py              # Model training script
│   ├── train_simple.py       # Simple training script
│   ├── requirements.txt
│   └── .env
├── .venv/                    # Python virtual environment
├── README.md
└── .gitignore
```



### Code Style

**JavaScript/React:**
- Follow ESLint configuration
- Use functional components and hooks
- Write meaningful component and variable names

**Python:**
- Follow PEP 8 style guide
- Use type hints where applicable
- Document functions with docstrings

## Troubleshooting

### Common Issues

**1. MongoDB Connection Error**
```
Error: MongooseServerSelectionError
```
Solution: Ensure MongoDB is running and connection string is correct in .env

**2. ML Service Not Starting**
```
ModuleNotFoundError: No module named 'fastapi'
```
Solution: Activate virtual environment and install requirements
```bash
venv\Scripts\activate
pip install -r requirements.txt
```

**3. Port Already in Use**
```
Error: listen EADDRINUSE: address already in use :::5000
```
Solution: Kill the process using the port or change port in .env

**4. Model Not Found**
```
Model not loaded. Train the model first.
```
Solution: Run training script
```bash
cd ml-service
python train.py
```

**5. CORS Errors**
```
Access to fetch has been blocked by CORS policy
```
Solution: Verify FRONTEND_URL in backend .env matches your frontend URL


## Acknowledgments

- Built with React, Node.js, Python, and MongoDB
- ML models powered by scikit-learn, XGBoost, LightGBM, and CatBoost
- UI components from Material-UI and Bootstrap
- Maps powered by Leaflet and OpenStreetMap







