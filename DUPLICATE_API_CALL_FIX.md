# Duplicate API Call Fix ✅

## Problem
The video upload API was being called twice, causing:
- First call succeeds
- Second call fails with `ERR_CONNECTION_RESET`
- Unnecessary server load
- Confusing error messages

## Root Causes

1. **React StrictMode**: In development, React StrictMode causes components to render twice, which can trigger event handlers twice
2. **useCallback Dependencies**: The `processing` state in dependencies caused the callback to be recreated, potentially allowing duplicate calls
3. **Async State Updates**: React state updates are async, so duplicate prevention checks might not catch rapid successive calls
4. **No API-Level Deduplication**: Even if component-level prevention worked, there was no protection at the API service level

## Fixes Applied

### 1. ✅ Improved Component-Level Duplicate Prevention
**File**: `frontend/src/pages/voshan/VideoUpload.jsx`

**Changes**:
- Added `activeRequestRef` to track the actual request promise
- Set `isProcessingRef.current = true` **immediately** before any async operations
- Increased debounce time from 500ms to 1000ms
- Removed `processing` from `useCallback` dependencies to prevent unnecessary re-creation
- Added check for existing active request promise before creating new one

**Key Improvements**:
```javascript
// Check ref FIRST before any async operations
if (isProcessingRef.current) {
  return; // Prevent duplicate
}

// Track the actual request promise
activeRequestRef.current = requestPromise;
```

### 2. ✅ API-Level Request Deduplication
**File**: `frontend/src/services/voshan/detectionApi.js`

**Changes**:
- Added `activeRequests` Map to track ongoing requests
- Created `getRequestKey()` function to generate unique keys based on file and options
- If duplicate request detected, return existing promise instead of creating new request
- Clean up request from map when done (success or error)
- Handle abort signals properly

**Key Features**:
```javascript
// Generate unique key for request
const requestKey = getRequestKey(videoFile, options);

// Check if same request already exists
if (activeRequests.has(requestKey)) {
  return activeRequests.get(requestKey); // Reuse existing
}

// Store new request
activeRequests.set(requestKey, requestPromise);
```

### 3. ✅ Better Request Cleanup
- Clean up `activeRequestRef` in finally block
- Clean up `activeRequests` Map on abort
- Ensure all refs are reset in `handleReset()`

## How It Works

### Component Level (VideoUpload.jsx):
1. User clicks upload button
2. `handleUpload` checks `isProcessingRef.current` - if true, return immediately
3. Check debounce time - if too soon, return
4. Check `activeRequestRef.current` - if exists, return
5. Set `isProcessingRef.current = true` immediately
6. Create request promise and store in `activeRequestRef.current`
7. When done, clear all refs

### API Level (detectionApi.js):
1. `processVideo` called with file and options
2. Generate unique `requestKey` from file properties + options
3. Check if `activeRequests` has this key
4. If yes, return existing promise (deduplication)
5. If no, create new request and store in `activeRequests`
6. When request completes (success/error/abort), remove from map

## Benefits

1. **Double Protection**: Both component and API level prevent duplicates
2. **Works with React StrictMode**: Even if component renders twice, API deduplication catches it
3. **Prevents Race Conditions**: Immediate ref setting prevents async timing issues
4. **Better User Experience**: No confusing duplicate error messages
5. **Reduced Server Load**: Only one request per file/options combination

## Testing

### Test Case 1: Rapid Double Click
1. Click upload button twice quickly
2. **Expected**: Only one API call, second click ignored
3. **Result**: ✅ Works - debounce + ref check prevents duplicate

### Test Case 2: React StrictMode Double Render
1. In development mode (StrictMode enabled)
2. Click upload button once
3. **Expected**: Only one API call (even if component renders twice)
4. **Result**: ✅ Works - API deduplication catches duplicate

### Test Case 3: Same File, Different Options
1. Upload same file with different camera ID
2. **Expected**: Two separate requests (different options)
3. **Result**: ✅ Works - request key includes options

### Test Case 4: Same File, Same Options (Duplicate)
1. Upload same file with same options twice
2. **Expected**: Second request reuses first (deduplication)
3. **Result**: ✅ Works - API deduplication reuses request

## Files Modified

1. `frontend/src/pages/voshan/VideoUpload.jsx`
   - Added `activeRequestRef` tracking
   - Improved duplicate prevention logic
   - Removed `processing` from useCallback dependencies

2. `frontend/src/services/voshan/detectionApi.js`
   - Added `activeRequests` Map for deduplication
   - Added `getRequestKey()` function
   - Added duplicate request detection and reuse

## Status

✅ **FIXED** - Duplicate API calls should no longer occur

The fix provides double protection:
- Component level prevents rapid clicks and re-renders
- API level prevents any duplicate requests that slip through

Both mechanisms work together to ensure only one request is made per unique file/options combination.

