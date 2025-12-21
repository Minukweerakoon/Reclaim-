# Quick MongoDB Setup

## 🚀 Fastest Option: MongoDB Atlas (Cloud - FREE)

### Step 1: Create Account & Cluster
1. Visit: https://www.mongodb.com/cloud/atlas/register
2. Sign up (free)
3. Create a **FREE M0 cluster** (no credit card needed)
4. Wait 3-5 minutes for cluster to be created

### Step 2: Create Database User
1. Go to **"Database Access"** (left sidebar)
2. Click **"Add New Database User"**
3. Choose **"Password"** authentication
4. Username: `reclaim_user`
5. Password: Create a strong password (save it!)
6. Database User Privileges: **"Atlas admin"**
7. Click **"Add User"**

### Step 3: Configure Network Access
1. Go to **"Network Access"** (left sidebar)
2. Click **"Add IP Address"**
3. Click **"Allow Access from Anywhere"** (for development)
   - Or add your current IP: `0.0.0.0/0`
4. Click **"Confirm"**

### Step 4: Get Connection String
1. Go to **"Database"** → Click **"Connect"**
2. Choose **"Connect your application"**
3. Driver: **Node.js**, Version: **5.5 or later**
4. Copy the connection string
   - Example: `mongodb+srv://reclaim_user:<password>@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority`

### Step 5: Update .env File
1. In `backend/` folder, create `.env` file (copy from `env.example.txt`)
2. Update `MONGODB_URI`:
   ```env
   MONGODB_URI=mongodb+srv://reclaim_user:YOUR_PASSWORD@cluster0.xxxxx.mongodb.net/reclaim?retryWrites=true&w=majority
   ```
3. Replace:
   - `YOUR_PASSWORD` with the password you created
   - `cluster0.xxxxx` with your actual cluster name
   - `reclaim` is the database name (you can change it)

### Step 6: Test Connection
```bash
cd backend
npm run dev
```

You should see: `MongoDB Connected: cluster0.xxxxx.mongodb.net`

---

## Alternative: Local MongoDB (Windows)

### Install MongoDB Community Edition
1. Download: https://www.mongodb.com/try/download/community
2. Run installer
3. Choose "Complete" installation
4. Install as Windows Service ✅
5. Install MongoDB Compass (optional GUI)

### Start MongoDB
- If installed as service, it starts automatically
- Or: `net start MongoDB` in PowerShell (as Administrator)

### Update .env
```env
MONGODB_URI=mongodb://localhost:27017/reclaim
```

---

## Which Should You Choose?

**MongoDB Atlas (Cloud):** ✅ Recommended
- No installation
- Free forever
- Works immediately
- Accessible from anywhere

**Local MongoDB:**
- Requires installation
- Only works on your machine
- Better for offline development

---

## Need Help?

If you get connection errors:
1. Check your connection string is correct
2. Verify network access allows your IP
3. Check username/password are correct
4. Ensure database user has proper privileges

