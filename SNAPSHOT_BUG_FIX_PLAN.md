# Frame Snapshot Bug Fix Plan

## Problem Analysis

The snapshot feature has several issues:

1. **Real-time Alerts (WebSocket) - No Snapshots**
   - Real-time alerts received via WebSocket don't have frame snapshots
   - AlertNotification component displays alerts without images
   - No video file available for real-time alerts (they come from live processing)

2. **Historical Alerts (AlertHistory) - No Snapshots**
   - Alerts loaded from database don't have frame snapshots
   - No video file available to extract frames from
   - User can't see snapshots when viewing alert history

3. **VideoUpload Page - Potential Frame Mismatch**
   - Frames are extracted from video file
   - Frame numbers from backend might not match frontend frame numbers
   - Re-extraction happens after backend response, but timing issues might occur

4. **Missing Snapshot Storage**
   - Snapshots are only stored in browser memory (frameMap)
   - When page refreshes, snapshots are lost
   - No persistence of snapshots

## Solution Options

### Option 1: Backend-Stored Snapshots (Recommended)
**Pros:**
- Snapshots available for all alerts (real-time, historical, VideoUpload)
- Persists across page refreshes
- No need for video file on frontend
- Better user experience

**Cons:**
- Requires backend storage (database or file system)
- Increases storage requirements
- Backend needs to extract and store frames

### Option 2: Frontend-Only Snapshots (Current Approach)
**Pros:**
- No backend changes needed
- Lower storage requirements

**Cons:**
- Only works on VideoUpload page
- Lost on page refresh
- Not available for real-time/historical alerts

### Option 3: Hybrid Approach
- Backend stores snapshots for persistence
- Frontend can also extract frames for immediate display
- Best of both worlds

## Recommended Solution: Backend-Stored Snapshots

### Implementation Plan

#### Phase 1: Backend Changes

1. **Modify ML Service to Save Frame Snapshots**
   - When an alert is detected, extract the frame image
   - Save frame as base64 or image file
   - Store frame snapshot path/URL in alert data
   - Include snapshot in alert response

2. **Update Alert Model**
   - Add `snapshot` field to Alert schema (if not already present)
   - Store base64 data URL or file path
   - Support both formats (base64 for small images, file path for large)

3. **Create Snapshot Storage Strategy**
   - Option A: Store as base64 in MongoDB (good for small snapshots)
   - Option B: Save as image files, store paths (better for large images)
   - Option C: Use a hybrid (small snapshots in DB, large as files)

4. **Update Detection Controller**
   - Ensure snapshot is included when saving alerts
   - Include snapshot in WebSocket broadcasts
   - Include snapshot in API responses

#### Phase 2: Frontend Changes

1. **Update AlertCard Component**
   - Handle snapshots from backend (base64 or URL)
   - Fallback to frameMap if available (for VideoUpload page)
   - Better error handling for missing/invalid snapshots

2. **Update AlertNotification Component**
   - Display snapshots from backend (WebSocket alerts)
   - No need for video file access

3. **Update AlertHistory Component**
   - Display snapshots from database
   - No need for video file access

4. **Update VideoUpload Component (Optional Enhancement)**
   - Keep frameMap for immediate display
   - Use backend snapshots as fallback or primary source
   - Could cache snapshots for better performance

#### Phase 3: Optimization

1. **Snapshot Compression**
   - Compress images before storing
   - Reduce file size while maintaining quality
   - Consider thumbnail generation for list views

2. **Lazy Loading**
   - Load snapshots on demand (when alert is viewed)
   - Improve initial page load performance

3. **Caching Strategy**
   - Cache snapshots in browser (IndexedDB or localStorage)
   - Reduce server requests

## Implementation Steps

### Step 1: Backend - Save Snapshots in ML Service
- [ ] Modify Python ML service to extract frame image when alert is detected
- [ ] Save frame as base64 encoded string
- [ ] Include snapshot in alert data returned to backend
- [ ] Test with small videos first

### Step 2: Backend - Update Alert Model
- [ ] Verify snapshot field exists in Alert schema
- [ ] Update if needed to support base64 data URLs
- [ ] Ensure snapshot is saved when creating alerts

### Step 3: Backend - Include Snapshot in Responses
- [ ] Include snapshot in WebSocket broadcast
- [ ] Include snapshot in API responses (getAlerts, getAlertById)
- [ ] Test snapshot serialization

### Step 4: Frontend - Update AlertCard
- [ ] Accept snapshot from alert object (alert.snapshot)
- [ ] Prioritize backend snapshot over frameMap
- [ ] Handle base64 data URLs
- [ ] Improve error handling

### Step 5: Frontend - Update All Alert Displays
- [ ] Update AlertNotification to use backend snapshots
- [ ] Update AlertHistory to use backend snapshots
- [ ] Update VideoUpload to use backend snapshots (with frameMap fallback)
- [ ] Test all three locations

### Step 6: Testing & Validation
- [ ] Test real-time alerts (WebSocket) have snapshots
- [ ] Test historical alerts have snapshots
- [ ] Test VideoUpload page snapshots
- [ ] Test page refresh (snapshots should persist)
- [ ] Test with different video sizes
- [ ] Test error cases (missing snapshots, invalid data)

## Alternative: Quick Fix (Frontend Only)

If backend changes are not feasible immediately, we can:

1. **Add snapshot to WebSocket broadcasts (if backend can provide)**
2. **Store snapshots in localStorage/IndexedDB for persistence**
3. **Create a snapshot service to manage snapshot storage**

However, this is less ideal as it doesn't solve the real-time alert issue.

## Decision Needed

**Which approach should we take?**
- **A**: Full backend solution (recommended - best user experience)
- **B**: Quick frontend fix (temporary - limits functionality)
- **C**: Hybrid approach (most flexible but more complex)

Once decided, we'll proceed with implementation.

