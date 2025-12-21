# MongoDB URI Fix - Password with @ Symbol

## The Problem

Your password `Voshan@929` contains `@`, which is a special character in MongoDB connection strings.

**Your current URI:**
```
mongodb+srv://kavishavoshan:Voshan@929@relaim.b3o6zvw.mongodb.net/
```

MongoDB interprets this as:
- Username: `kavishavoshan`
- Password: `Voshan` ❌ (wrong - cuts off at first @)
- Host: `929@relaim.b3o6zvw.mongodb.net` ❌ (wrong)

## The Solution

I've updated the code to **automatically URL-encode** passwords, so you can use your password as-is!

## Update Your .env File

In `backend/.env`, add this line:

```env
MONGODB_URI=mongodb+srv://kavishavoshan:Voshan@929@relaim.b3o6zvw.mongodb.net/reclaim?retryWrites=true&w=majority
```

**Important:** 
- Keep the password as `Voshan@929` (the code will encode it automatically)
- Added database name: `/reclaim`
- Added connection options: `?retryWrites=true&w=majority`

## Manual Encoding (Alternative)

If you prefer to encode it manually, use:

```env
MONGODB_URI=mongodb+srv://kavishavoshan:Voshan%40929@relaim.b3o6zvw.mongodb.net/reclaim?retryWrites=true&w=majority
```

Where `%40` is the URL encoding for `@`.

## Steps

1. **Create/Edit `backend/.env` file:**
   ```bash
   cd backend
   # If .env doesn't exist:
   copy env.example.txt .env
   ```

2. **Edit `.env` and set:**
   ```env
   MONGODB_URI=mongodb+srv://kavishavoshan:Voshan@929@relaim.b3o6zvw.mongodb.net/reclaim?retryWrites=true&w=majority
   ```

3. **Restart server:**
   ```bash
   npm run dev
   ```

4. **Expected output:**
   ```
   ✅ MongoDB Connected: relaim.b3o6zvw.mongodb.net
      Database: reclaim
   🚀 Server running on port 5000
   ```

## Verification

After restarting, you should see:
- ✅ MongoDB Connected (not ❌ error)
- Server running successfully
- No connection errors

---

**The code now automatically handles password encoding, so you can use your password with @ symbol directly!** 🎉

