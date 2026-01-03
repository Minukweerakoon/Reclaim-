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





