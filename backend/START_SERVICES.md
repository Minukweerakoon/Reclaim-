# Quick Start Guide - Starting All Services

## Service Startup Order

### 1. Python ML Service ✅ (Already Running)
```bash
cd backend/ml-service
python app.py
```
**Status:** Running on http://127.0.0.1:5001

### 2. Node.js Backend (New Terminal)
```bash
cd backend
npm run dev
```
**Expected:** Server on port 5000, WebSocket on port 5000

### 3. React Frontend (New Terminal)
```bash
cd frontend
npm run dev
```
**Expected:** Frontend on http://localhost:3000

---

## Quick Test

Once all services are running:

1. **Open Browser:** http://localhost:3000/voshan/detection
2. **Check Status:** ML Service should show "✅ Healthy"
3. **Test WebSocket:** Should show "🟢 Connected"

---

## Health Check URLs

- **ML Service:** http://localhost:5001/api/v1/detect/status
- **Backend API:** http://localhost:5000/api/health
- **Frontend:** http://localhost:3000

