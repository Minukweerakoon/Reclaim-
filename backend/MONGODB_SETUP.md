# MongoDB Setup Guide

## Option 1: MongoDB Atlas (Cloud - Recommended for Quick Start) ✅

MongoDB Atlas is a free cloud database service. No local installation needed!

### Steps:

1. **Create Free Account:**
   - Go to https://www.mongodb.com/cloud/atlas/register
   - Sign up for free (M0 cluster is free forever)

2. **Create Cluster:**
   - Choose "Build a Database"
   - Select "M0 FREE" tier
   - Choose a cloud provider and region (closest to you)
   - Click "Create"

3. **Create Database User:**
   - Go to "Database Access" → "Add New Database User"
   - Choose "Password" authentication
   - Username: `reclaim_user` (or your choice)
   - Password: Generate or create your own (save it!)
   - Database User Privileges: "Atlas admin" or "Read and write to any database"
   - Click "Add User"

4. **Configure Network Access:**
   - Go to "Network Access" → "Add IP Address"
   - Click "Allow Access from Anywhere" (for development)
   - Or add your specific IP address
   - Click "Confirm"

5. **Get Connection String:**
   - Go to "Database" → "Connect"
   - Choose "Connect your application"
   - Copy the connection string
   - It looks like: `mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`

6. **Update .env File:**
   ```env
   MONGODB_URI=mongodb+srv://reclaim_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/reclaim?retryWrites=true&w=majority
   ```
   Replace:
   - `reclaim_user` with your username
   - `YOUR_PASSWORD` with your password
   - `cluster0.xxxxx` with your cluster name
   - `reclaim` is the database name (you can change it)

---

## Option 2: Local MongoDB Installation

### Windows Installation:

1. **Download MongoDB:**
   - Go to https://www.mongodb.com/try/download/community
   - Select: Windows, MSI, Latest version
   - Download and run installer

2. **Install:**
   - Choose "Complete" installation
   - Install as Windows Service (recommended)
   - Install MongoDB Compass (GUI tool, optional but helpful)

3. **Verify Installation:**
   ```powershell
   mongod --version
   ```

4. **Start MongoDB:**
   - If installed as service, it starts automatically
   - Or manually: `net start MongoDB`

5. **Update .env File:**
   ```env
   MONGODB_URI=mongodb://localhost:27017/reclaim
   ```

---

## Quick Setup Script

After choosing an option above, create your `.env` file:

```bash
# Copy example file
cd backend
copy env.example.txt .env
```

Then edit `.env` and update `MONGODB_URI` with your connection string.

---

## Test Connection

After setting up, test the connection:

```bash
cd backend
npm run dev
```

You should see:
```
MongoDB Connected: localhost:27017
# or
MongoDB Connected: cluster0.xxxxx.mongodb.net
```

---

## Recommended: MongoDB Atlas (Cloud)

**Advantages:**
- ✅ No installation needed
- ✅ Free tier available
- ✅ Accessible from anywhere
- ✅ Automatic backups
- ✅ Easy to scale

**For Development:** MongoDB Atlas is perfect and free!

