# Frame Snapshot Implementation Plan

## Overview
Add frame snapshots to alerts so users can see the actual frame where suspicious behavior was detected. This applies to both:
- **Recent Alerts** (from video upload processing)
- **Real-time Alerts** (from live streaming/WebSocket)

## Current State

### ✅ Already in Place
- Alert model has `snapshot` field (base64 string) - **ready to use**
- Frame processing happens in ML service (`app.py`)
- Alerts are stored in MongoDB
- WebSocket broadcasts alerts in real-time
- Frontend displays alerts via `AlertCard` component

### ❌ Missing
- Frame snapshot capture when alert is detected
- Base64 encoding of frame snapshots
- Including snapshot in alert data structure
- Displaying snapshot in AlertCard component
- Displaying snapshot in real-time alerts

## Implementation Plan

### Phase 1: ML Service - Capture Frame Snapshots

#### 1.1 Modify Video Processing (`backend/voshan/ml-service/app.py`)

**Location**: In the video processing loop where alerts are detected

**Changes**:
- When an alert is detected, capture the current frame
- Annotate the frame with detections/boxes (optional - for better visualization)
- Encode frame as base64 JPEG
- Add `snapshot` field to alert object

**Code Location**: Around line 373-378 where `frame_alerts` are generated

**Implementation**:
```python
# When alert is detected
if frame_alerts:
    # Capture annotated frame (with detections drawn)
    annotated_frame = video_processor.draw_detections(frame, tracked_objects)
    annotated_frame = video_processor.draw_alerts(annotated_frame, frame_alerts)
    
    # Encode as base64 JPEG
    import base64
    import cv2
    _, buffer = cv2.imencode('.jpg', annotated_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
    frame_base64 = base64.b64encode(buffer).decode('utf-8')
    snapshot_data_url = f"data:image/jpeg;base64,{frame_base64}"
    
    # Add snapshot to each alert
    for alert in frame_alerts:
        alert['snapshot'] = snapshot_data_url
```

#### 1.2 Add Snapshot Capture Utility (`backend/voshan/ml-service/utils/video.py`)

**New Method**: `capture_frame_snapshot(frame, detections=None, alerts=None)`

**Purpose**: Centralized function to capture and encode frame snapshots

**Features**:
- Option to include annotations (detections/alerts)
- Configurable image quality
- Returns base64 data URL

### Phase 2: Backend - Store and Broadcast Snapshots

#### 2.1 Update Alert Controller (`backend/src/controllers/voshan/detectionController.js`)

**Location**: Where alerts are saved to database (around line 215-228)

**Changes**:
- Include `snapshot` field from ML service response
- Store snapshot in MongoDB alert document

**Code**:
```javascript
const alertDoc = new Alert({
  // ... existing fields ...
  snapshot: alert.snapshot || null, // Add snapshot field
});
```

#### 2.2 Update WebSocket Broadcast (`backend/src/controllers/voshan/detectionController.js`)

**Location**: Where alerts are broadcast via WebSocket (around line 235-242)

**Changes**:
- Include `snapshot` in broadcast payload

**Code**:
```javascript
websocketService.broadcastAlert({
  // ... existing fields ...
  snapshot: alert.snapshot || null, // Add snapshot
});
```

#### 2.3 Update Real-time Frame Processing (`backend/src/controllers/voshan/detectionController.js`)

**Location**: `processFrame` function (around line 333-415)

**Changes**:
- Capture snapshot for real-time alerts
- Include in alert document and WebSocket broadcast

### Phase 3: Frontend - Display Snapshots

#### 3.1 Update AlertCard Component (`frontend/src/components/voshan/AlertCard.jsx`)

**Changes**:
- Add image display section
- Show snapshot if available
- Add thumbnail with expand option
- Handle loading states

**UI Design**:
```jsx
{alert.snapshot && (
  <div className="alert-snapshot">
    <img 
      src={alert.snapshot} 
      alt={`Alert snapshot - ${alert.type}`}
      className="snapshot-image"
    />
  </div>
)}
```

#### 3.2 Update Real-time Alert Display

**Files to Check**:
- `frontend/src/pages/voshan/DetectionDashboard.jsx` (if exists)
- Any component that displays real-time WebSocket alerts

**Changes**:
- Display snapshot in real-time alert notifications
- Update alert list when new alerts arrive with snapshots

#### 3.3 Add Snapshot Styling (`frontend/src/components/voshan/AlertCard.css`)

**Features**:
- Responsive image sizing
- Thumbnail with hover effects
- Modal/lightbox for full-size view
- Loading placeholder

### Phase 4: Optimization & Performance

#### 4.1 Snapshot Size Management

**Considerations**:
- Limit snapshot resolution (e.g., max 800x600)
- Compress JPEG quality (85% is good balance)
- Consider storing snapshots in file system instead of base64 (future optimization)

#### 4.2 Database Storage

**Current**: Base64 string in MongoDB document
**Pros**: Simple, no file management
**Cons**: Larger documents, slower queries

**Future Optimization**:
- Store snapshots as files (local or S3)
- Store file path in database
- Serve via static file endpoint

#### 4.3 WebSocket Payload Size

**Consideration**: Base64 images can be large (50-200KB)
- May need to limit snapshot size for real-time alerts
- Consider sending thumbnail for real-time, full image on demand

## File Changes Summary

### Backend (Python/ML Service)
1. `backend/voshan/ml-service/app.py`
   - Add snapshot capture in video processing loop
   - Add snapshot to alert objects

2. `backend/voshan/ml-service/utils/video.py`
   - Add `capture_frame_snapshot()` method

### Backend (Node.js)
3. `backend/src/controllers/voshan/detectionController.js`
   - Include snapshot when saving alerts
   - Include snapshot in WebSocket broadcasts

### Frontend
4. `frontend/src/components/voshan/AlertCard.jsx`
   - Add snapshot display
   - Add image viewer/lightbox

5. `frontend/src/components/voshan/AlertCard.css`
   - Add snapshot styling

6. Real-time alert components (if any)
   - Update to display snapshots

## Implementation Steps

### Step 1: ML Service Snapshot Capture
1. Modify `app.py` to capture frames when alerts detected
2. Encode frames as base64
3. Add to alert objects
4. Test with video upload

### Step 2: Backend Integration
1. Update alert controller to store snapshots
2. Update WebSocket broadcast to include snapshots
3. Test database storage
4. Test WebSocket broadcasting

### Step 3: Frontend Display
1. Update AlertCard to show snapshots
2. Add styling for snapshots
3. Test with recent alerts
4. Test with real-time alerts

### Step 4: Testing & Optimization
1. Test with various video sizes
2. Monitor snapshot sizes
3. Optimize image quality/size
4. Test WebSocket performance

## Testing Checklist

- [ ] Video upload processing includes snapshots in alerts
- [ ] Snapshots are stored in database
- [ ] Snapshots appear in recent alerts list
- [ ] Snapshots appear in real-time alerts
- [ ] Snapshot images load correctly
- [ ] Snapshot images are properly sized
- [ ] WebSocket payload size is acceptable
- [ ] Database document size is reasonable
- [ ] Performance is acceptable with snapshots

## Performance Considerations

### Snapshot Size Limits
- **Recommended**: Max 800x600 pixels, 85% JPEG quality
- **Expected size**: 50-150KB per snapshot (base64)
- **Database impact**: ~100KB per alert document

### Optimization Options
1. **Thumbnail + Full Image**: Store thumbnail in alert, fetch full image on demand
2. **File Storage**: Store images as files, reference in database
3. **Lazy Loading**: Only load snapshots when alert is viewed
4. **Compression**: Use WebP format for smaller file sizes

## Future Enhancements

1. **Multiple Snapshots**: Store multiple frames for alert timeline
2. **Video Clips**: Store short video clips instead of single frames
3. **Annotation Options**: Toggle annotations on/off
4. **Export**: Download snapshots as images
5. **Comparison**: Side-by-side comparison of alerts

## Estimated Implementation Time

- **Phase 1 (ML Service)**: 2-3 hours
- **Phase 2 (Backend)**: 1-2 hours
- **Phase 3 (Frontend)**: 2-3 hours
- **Phase 4 (Testing/Optimization)**: 2-3 hours

**Total**: ~8-11 hours

## Dependencies

- OpenCV (already installed) - for image encoding
- Base64 encoding (Python standard library)
- No new npm packages needed for frontend

## Notes

- The `snapshot` field already exists in the alert model - just needs to be populated
- Base64 encoding is simple but increases payload size
- Consider file storage for production (future optimization)
- WebSocket payload size may need monitoring for real-time alerts

