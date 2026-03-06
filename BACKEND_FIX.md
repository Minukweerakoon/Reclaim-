# Backend Fix - Root Cause Analysis

## Problem Summary
You're running the WRONG backend. The ValidationHub requires endpoints that don't exist in `src.api.main:app`.

## Root Cause
- **Currently Running**: `uvicorn src.api.main:app --reload` 
  - ✅ Has: `/api/chat/message`, `/api/reports`
  - ❌ Missing: `/validate/complete`, `/ws/validation/{client_id}`, entity/context/xai endpoints

- **Should be Running**: `uvicorn app:app --reload`
  - ✅ Has: ALL endpoints including validation, WebSocket, entities, context, XAI
  - ✅ Already imports and includes chat & reports routers from src.api

## The Fix

### Stop Current Backend
```bash
pkill -f "uvicorn"
```

### Start Correct Backend
```bash
cd /Users/apple/Desktop/Reclaim-/Kumesha
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## Why This Works
1. `app.py` is the COMPLETE backend with:
   - All validation endpoints (`/validate/complete`, `/validate/text`, `/validate/image`)
   - WebSocket endpoint (`/ws/validation/{client_id}`)
   - Entity detection, spatial-temporal context, XAI endpoints
   - **PLUS** it imports and includes the new chat & reports routers

2. Your frontend expects:
   - Chat: `/api/chat/message` ✓ (via chat_router in app.py)
   - Reports: `/api/reports` ✓ (via reports_router in app.py)
   - Validation: `/validate/complete` ✓ (in app.py)
   - WebSocket: `/ws/validation/{client_id}` ✓ (in app.py)

## Changes Already Applied
1. ✅ Fixed auto-confirm logic - bot's `next_action: 'validate'` triggers navigation
2. ✅ Updated LLM prompt to ask for image for FOUND items
3. ✅ Improved conversation flow sequencing

## Expected Behavior After Fix
1. Chat asks: "I found a keyboard"
2. Bot extracts: item_type, asks for color
3. User provides: color, location, time
4. Bot asks: **"Do you have an image of the keyboard?"**
5. User uploads image
6. Bot asks: "Would you like to proceed to validation to help find the owner?"
7. User types: "yes"
8. **Auto-navigation** to ValidationHub with all data
9. ValidationHub connects via WebSocket ✓ (no more 403 errors)
10. Validation runs successfully ✓

## Verification
After starting app.py, check:
```bash
curl http://localhost:8000/health
# Should return: {"status": "ok", ...}

# Check validation endpoint exists
curl -X POST http://localhost:8000/validate/text \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key" \
  -d '{"text": "test", "language": "en"}'
```
