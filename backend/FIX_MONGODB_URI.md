# Fix MongoDB URI with Special Characters in Password

## Issue
Your MongoDB password contains `@` symbol: `Voshan@929`

In MongoDB connection strings, `@` is used as a separator between credentials and host. If your password contains `@`, it needs to be **URL-encoded**.

## Solution

### Your Current URI (Incorrect):
```
mongodb+srv://kavishavoshan:Voshan@929@relaim.b3o6zvw.mongodb.net/
```

### Fixed URI (Correct):
```
mongodb+srv://kavishavoshan:Voshan%40929@relaim.b3o6zvw.mongodb.net/reclaim?retryWrites=true&w=majority
```

**Changes:**
- `Voshan@929` → `Voshan%40929` (URL-encoded `@` as `%40`)
- Added database name: `/reclaim`
- Added connection options: `?retryWrites=true&w=majority`

## Update Your .env File

In `backend/.env`, set:

```env
MONGODB_URI=mongodb+srv://kavishavoshan:Voshan%40929@relaim.b3o6zvw.mongodb.net/reclaim?retryWrites=true&w=majority
```

## Automatic Fix

I've updated the code to automatically URL-encode passwords, so you can use:

```env
MONGODB_URI=mongodb+srv://kavishavoshan:Voshan@929@relaim.b3o6zvw.mongodb.net/reclaim?retryWrites=true&w=majority
```

The code will automatically encode the password for you!

## Test

After updating `.env`, restart the server:
```bash
npm run dev
```

You should see:
```
✅ MongoDB Connected: relaim.b3o6zvw.mongodb.net
   Database: reclaim
```

