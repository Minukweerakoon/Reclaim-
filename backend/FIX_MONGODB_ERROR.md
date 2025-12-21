# Fix MongoDB Connection Error

## Issue
The error `querySrv ENOTFOUND _mongodb._tcp.929` indicates a malformed MongoDB connection string.

## Solution

### Option 1: Use Local MongoDB (if installed)
In `backend/.env`, set:
```env
MONGODB_URI=mongodb://localhost:27017/reclaim
```

### Option 2: Use MongoDB Atlas (Cloud - Recommended)
1. Get your connection string from MongoDB Atlas
2. In `backend/.env`, set:
```env
MONGODB_URI=mongodb+srv://username:password@cluster0.xxxxx.mongodb.net/reclaim?retryWrites=true&w=majority
```

### Option 3: Skip MongoDB for Now (Testing)
The server will now start even without MongoDB, but database features won't work.

Just make sure `MONGODB_URI` is set in `.env` (even if it's incorrect, server will warn but continue).

---

## Quick Fix

1. **Check your `.env` file:**
   ```bash
   cd backend
   type .env
   ```

2. **If MONGODB_URI looks wrong, update it:**
   - For local: `mongodb://localhost:27017/reclaim`
   - For Atlas: Your full connection string from Atlas

3. **Restart server:**
   ```bash
   npm run dev
   ```

---

## What I Fixed

✅ Removed deprecated MongoDB options  
✅ Made database connection non-blocking (server starts even if DB fails)  
✅ Added helpful error messages  

The server should now start successfully! 🚀

