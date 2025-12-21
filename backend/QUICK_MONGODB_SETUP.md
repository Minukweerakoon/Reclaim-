# Quick MongoDB Setup Guide

## 🎯 Recommended: MongoDB Atlas (Cloud - FREE & EASY)

### Why MongoDB Atlas?
- ✅ **FREE forever** (M0 tier)
- ✅ **No installation** needed
- ✅ **5 minutes** to set up
- ✅ Works from anywhere

---

## 📋 Step-by-Step Setup

### 1. Create MongoDB Atlas Account
1. Go to: **https://www.mongodb.com/cloud/atlas/register**
2. Sign up with email (free account)
3. Verify your email

### 2. Create Free Cluster
1. Click **"Build a Database"**
2. Choose **"M0 FREE"** (Free Shared tier)
3. Select **Cloud Provider** (AWS, Google Cloud, or Azure)
4. Choose **Region** (closest to you)
5. Click **"Create"**
6. Wait 3-5 minutes for cluster creation

### 3. Create Database User
1. In left sidebar, click **"Database Access"**
2. Click **"Add New Database User"**
3. Authentication Method: **"Password"**
4. Username: `reclaim_user`
5. Password: **Create a strong password** (save it!)
6. Database User Privileges: **"Atlas admin"**
7. Click **"Add User"**

### 4. Configure Network Access
1. In left sidebar, click **"Network Access"**
2. Click **"Add IP Address"**
3. Click **"Allow Access from Anywhere"** button
   - This adds `0.0.0.0/0` (allows all IPs for development)
4. Click **"Confirm"**

### 5. Get Connection String
1. In left sidebar, click **"Database"**
2. Click **"Connect"** button on your cluster
3. Choose **"Connect your application"**
4. Driver: **Node.js**, Version: **5.5 or later**
5. **Copy the connection string**
   - Looks like: `mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`

### 6. Update Your .env File

**Location:** `backend/.env`

**Update this line:**
```env
MONGODB_URI=mongodb+srv://reclaim_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/reclaim?retryWrites=true&w=majority
```

**Replace:**
- `YOUR_PASSWORD` → Your database user password
- `cluster0.xxxxx` → Your actual cluster name
- `reclaim` → Database name (you can change this)

**Example:**
```env
MONGODB_URI=mongodb+srv://reclaim_user:MySecurePass123@cluster0.abc123.mongodb.net/reclaim?retryWrites=true&w=majority
```

### 7. Test Connection

Start your backend:
```bash
cd backend
npm run dev
```

**Expected Output:**
```
MongoDB Connected: cluster0.xxxxx.mongodb.net
🚀 Server running on port 5000
```

---

## 🔧 Alternative: Local MongoDB (Windows)

If you prefer local installation:

### Install MongoDB
1. Download: **https://www.mongodb.com/try/download/community**
2. Run installer
3. Choose **"Complete"** installation
4. ✅ Check **"Install MongoDB as a Service"**
5. ✅ Check **"Install MongoDB Compass"** (GUI tool)
6. Install

### Start MongoDB
- Service starts automatically
- Or manually: `net start MongoDB` (PowerShell as Admin)

### Update .env
```env
MONGODB_URI=mongodb://localhost:27017/reclaim
```

---

## ✅ Verification

After setup, test:

```bash
cd backend
npm run dev
```

**Success looks like:**
```
MongoDB Connected: cluster0.xxxxx.mongodb.net
🚀 Server running on port 5000
📡 WebSocket available at ws://localhost:5000/api/voshan/socket.io
```

**Error looks like:**
```
Error: connect ECONNREFUSED...
```
→ Check your connection string and network access settings

---

## 🆘 Troubleshooting

### Connection Refused
- ✅ Check MongoDB Atlas network access allows your IP
- ✅ Verify username/password are correct
- ✅ Ensure cluster is running (not paused)

### Authentication Failed
- ✅ Check username and password in connection string
- ✅ Verify database user exists in Atlas

### Timeout
- ✅ Check internet connection
- ✅ Verify network access settings in Atlas

---

## 📝 Quick Reference

**MongoDB Atlas Dashboard:** https://cloud.mongodb.com/

**Connection String Format:**
```
mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority
```

**Your .env should have:**
```env
MONGODB_URI=mongodb+srv://reclaim_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/reclaim?retryWrites=true&w=majority
```

---

**Ready?** Follow steps 1-7 above, then start your backend! 🚀

