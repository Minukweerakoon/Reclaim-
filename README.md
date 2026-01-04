# Reclaim – AI-Powered Smart Lost & Found System  
### With Integrated Security, Risk Analytics, and User Assistance

Reclaim is an AI-powered smart Lost & Found platform designed to improve item recovery, system reliability, and on-ground security in real-world environments such as university campuses and public spaces.

The system is developed as a **Final Year Research Project** and consists of **four distinct but integrated research contributions**, each addressing a critical limitation in existing lost-and-found systems.

Rather than being a single-model solution, Reclaim functions as a **modular AI ecosystem**, combining intelligent retrieval, input validation, security monitoring, risk prediction, and user assistance.

---

## 1. Project Overview

Traditional lost-and-found systems suffer from:
- Unreliable matching results
- Poor-quality user submissions
- No confidence awareness
- Lack of security and misuse detection
- No proactive prevention mechanisms

Reclaim addresses these issues through **four novel AI modules**, working together as a unified platform:

### Research Contributions (Modules)

1. **Uncertainty-Aware Cascaded Retrieval (UACR)**  
   *Owner: Retrieval & Matching Module*  
   Improves the reliability of lost–found matching by incorporating uncertainty into category selection, candidate retrieval, and hybrid re-ranking.  
   The system dynamically adjusts search scope based on confidence, preventing overconfident wrong matches.

2. **Multimodal Input Validation & Quality Assessment Module**  
   *Owner: Input Reliability Module*  
   Validates and scores user-submitted image, text, and voice inputs to prevent low-quality or inconsistent data from entering the system.  
   Provides real-time feedback to users before submission.

3. **Real-Time Suspicious Behavior Detection System**  
   *Owner: Security & Surveillance Module*  
   Analyzes CCTV footage using computer vision to detect suspicious activities such as loitering, tampering, or abnormal behavior around found-item locations.  
   Generates alerts for security personnel.

4. **Device Behavior Anomaly Detection, Predictive Risk Analytics & Multilingual IVR Assistance**  
   *Owner: Prevention & User Assistance Module*  
   Detects abnormal device movement or usage patterns, predicts high-risk zones and time windows, and provides multilingual IVR/SMS reminders to reduce item loss after storage.

Together, these modules form a **holistic, intelligent lost-and-found ecosystem** that focuses on **recovery, prevention, trust, and safety**.

---

## 2. Key Features

- Image-based lost item matching
- Text-based semantic search
- Uncertainty-aware retrieval and ranking (UACR)
- Multimodal input validation (image, text, voice)
- Real-time suspicious behavior detection
- Device behavior anomaly detection
- Predictive risk analytics
- Multilingual IVR and SMS user nudging
- Modular and extensible architecture

---

## 3. High-Level System Architecture

Users (Lost / Found / Security)
↓
Frontend (React)
↓
Backend API Layer
↓
Input Validation Module
↓
Lost & Found Database
↓
UACR Retrieval & Matching Engine
↓
Confidence-Aware Results
↓
Security & Risk Modules
↓
Alerts / IVR / SMS Notifications

System and software architecture diagrams are maintained under:
docs/architecture/

---

## 4. AI Pipeline Overview

### 4.1 Uncertainty-Aware Cascaded Retrieval (UACR)
- Probabilistic classification with uncertainty estimation
- Uncertainty-weighted category selection
- Hybrid re-ranking using semantic and visual similarity
- Confidence-aware result presentation

### 4.2 Multimodal Input Validation
- Image quality assessment
- Text completeness and consistency checks
- Cross-modal validation
- Real-time user feedback

### 4.3 Suspicious Behavior Detection
- Computer vision-based activity recognition
- Real-time alert generation
- Security dashboard integration

### 4.4 Device Anomaly Detection & Risk Analytics
- Behavioral pattern learning
- Anomaly detection
- Spatio-temporal risk prediction
- Multilingual IVR/SMS nudging

---

## 5. Project Structure
<img width="2816" height="1536" alt="Gemini_Generated_Image_n6b6gdn6b6gdn6b6" src="https://github.com/user-attachments/assets/ad71b7a2-bcc7-4779-ba6a-7ddb87c1dd7f" />

---

## 6. Tech Stack

### Frontend
- React 18
- Vite
- React Router
- Axios

### Backend
- Node.js + Express
- Python (AI services)

### Database
- MongoDB

### AI / ML
- PyTorch
- CLIP / Vision-Language Models
- CNN-based classifiers and metric models
- YOLO / CV models (security)
- FAISS (vector search)

---

## 7. Dependencies

Each module maintains its own dependency list:

- `backend/requirements.txt` (Python)
- `backend/package.json` (Node.js)
- `frontend/package.json` (React)

Common dependencies include:
torch
torchvision
numpy
opencv-python
scikit-learn
fastapi
express
mongoose
react
axios
---

## 8. Environment Variables

### Backend (`backend/.env`)
MONGO_URI=
JWT_SECRET=
MODEL_PATH=
FAISS_INDEX_PATH=
DEVICE=cuda
SMS_API_KEY=
IVR_CONFIG=

### Frontend (`frontend/.env`)
VITE_API_BASE_URL=http://localhost:5000
---

## 9. Setup & Installation
Backend
cd backend
npm install
pip install -r requirements.txt
npm run dev

Frontend
cd frontend
npm install
npm run dev

## 10. Evaluation Metrics
	•	Precision@K, Recall@K, MAP (retrieval)
	•	Uncertainty calibration (UACR)
	•	Validation accuracy (input quality)
	•	Detection precision/recall (security)
	•	Anomaly detection accuracy
	•	Risk prediction performance
	•	End-to-end latencyjop




