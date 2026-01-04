# Frame Snapshot Implementation Plan

## 📋 Overview

This plan outlines how to add frame snapshot display to alert cards by extracting frames from uploaded videos in the UI and matching them with alert frame numbers, without affecting existing processes.

## 🎯 Goal

- Extract frames from uploaded videos client-side (in the browser)
- Store frames with their frame numbers
- Display the matching frame snapshot in alert cards when available
- Ensure frame extraction matches the backend's frame numbering system
- Maintain backward compatibility with existing functionality

---

## 📊 Current State Analysis

### Existing Data Flow:
1. **Backend Processing:**
   - Python ML service processes video frame-by-frame
   - Each alert includes a `frame` field (frame number, 0-indexed)
   - Video FPS is extracted and used for time calculations

2. **Frontend:**
   - `AlertCard` component displays frame number but not the actual frame
   - `VideoUpload` component handles video file selection
   - Alerts are received with `frame` property (number)

3. **Database:**
   - Alert model already has `frame: Number` field
   - Alerts stored with frame numbers

### Key Technical Details:
- Backend uses OpenCV to read frames sequentially
- Frame numbers are 0-indexed (first frame = 0)
- Video FPS is extracted from video metadata
- Frames are processed at the video's native frame rate

---

## 🏗️ Implementation Plan

### Phase 1: Create Frame Extraction Utility

**File:** `frontend/src/utils/videoFrameExtractor.js`

**Purpose:** Extract frames from video files in the browser and store them with frame numbers.

**Key Functions:**
- `extractVideoFrames(videoFile, options)` - Main extraction function
- `getFrameAt(videoFile, frameNumber)` - Get specific frame by number
- Store frames as data URLs (base64 encoded images)

**Considerations:**
- Use HTMLVideoElement and Canvas API for frame extraction
- Extract frames at the video's native frame rate
- Frame numbering should match backend (0-indexed)
- Store frames efficiently (consider memory usage for long videos)

---

### Phase 2: Integrate Frame Extraction into Video Upload

**File:** `frontend/src/pages/voshan/VideoUpload.jsx`

**Changes:**
1. Extract frames when video file is selected (before upload)
2. Store frames in component state or context
3. Pass frame map/array to AlertCard components
4. Handle cleanup of frames when video changes

**Implementation Strategy:**
- Extract frames asynchronously when file is selected
- Show loading indicator during frame extraction
- Store frames in a Map: `Map<frameNumber, dataURL>`
- Make frames available to AlertCard components

---

### Phase 3: Update AlertCard Component

**File:** `frontend/src/components/voshan/AlertCard.jsx`

**Changes:**
1. Accept `frameSnapshot` prop (optional data URL)
2. Display frame image if available
3. Add loading/error states for frame display
4. Style frame snapshot appropriately

**UI Updates:**
- Add frame snapshot section above alert details
- Show frame number on snapshot
- Add click-to-expand functionality (optional)
- Handle cases where frame is not available

---

### Phase 4: Connect Frame Extraction to Alert Display

**Integration Points:**

1. **VideoUpload Page:**
   - Extract frames when file selected
   - Store frames in state/context
   - Pass frame map to AlertCard in results section

2. **AlertHistory Page:**
   - For alerts from uploaded videos, need to associate with source video
   - Consider storing video reference in alert or session storage
   - Extract frames if video is still available

3. **Real-time Alerts:**
   - Real-time alerts won't have source video available
   - Skip frame snapshot for real-time alerts (only show for uploaded video alerts)

---

## 🔧 Technical Implementation Details

### Frame Extraction Algorithm

```javascript
// Pseudo-code for frame extraction
async function extractVideoFrames(videoFile) {
  const video = document.createElement('video');
  video.src = URL.createObjectURL(videoFile);
  
  await video.load();
  
  const frames = new Map();
  const fps = video.videoMetadata?.frameRate || 30;
  const totalFrames = Math.floor(video.duration * fps);
  
  // Extract frames at video's native rate
  for (let frameNumber = 0; frameNumber < totalFrames; frameNumber++) {
    const time = frameNumber / fps;
    video.currentTime = time;
    
    await new Promise(resolve => {
      video.onseeked = () => {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        canvas.getContext('2d').drawImage(video, 0, 0);
        
        frames.set(frameNumber, canvas.toDataURL('image/jpeg', 0.8));
        resolve();
      };
    });
  }
  
  return frames;
}
```

### Frame Matching Strategy

- Backend frame numbers are 0-indexed
- Frontend extraction should also be 0-indexed
- Match exact frame numbers from alerts
- Handle edge cases (frame number out of range, video not available)

### Memory Management

- Store frames as data URLs (base64 JPEG)
- Consider compressing frames (quality 0.7-0.8)
- Limit frame storage for very long videos (optional: only store frames with alerts)
- Clean up object URLs when done

---

## 📝 Step-by-Step Implementation

### Step 1: Create Frame Extraction Utility

1. Create `frontend/src/utils/videoFrameExtractor.js`
2. Implement frame extraction using HTMLVideoElement + Canvas
3. Return Map of frameNumber -> dataURL
4. Add error handling and progress callbacks

### Step 2: Update VideoUpload Component

1. Add state for frame map: `const [frameMap, setFrameMap] = useState(new Map())`
2. Extract frames when file is selected (useEffect or handler)
3. Show loading indicator during extraction
4. Pass frame map to AlertCard components in results section

### Step 3: Update AlertCard Component

1. Add `frameSnapshot` prop (optional string - data URL)
2. Add frame snapshot display section in JSX
3. Update CSS for snapshot display
4. Handle missing frames gracefully

### Step 4: Update AlertHistory (Optional)

1. For alerts from video uploads, check if source video is available
2. Extract frames if video file reference is stored
3. This is optional - can be added later

### Step 5: Testing

1. Test with short videos first
2. Verify frame numbers match between backend and frontend
3. Test with videos of different frame rates
4. Test memory usage with longer videos
5. Verify no impact on existing functionality

---

## ⚠️ Considerations & Limitations

### Performance Considerations:
- Frame extraction can be slow for long videos
- Memory usage increases with number of frames stored
- Consider extracting only frames that have alerts (future optimization)

### Browser Compatibility:
- HTMLVideoElement and Canvas API are well-supported
- Video codec support varies by browser
- Consider fallback for unsupported formats

### Frame Rate Matching:
- Backend processes all frames sequentially
- Frontend should extract frames at the same rate
- Frame numbers should align (0-indexed, sequential)

### Real-time Alerts:
- Real-time alerts won't have source video in UI
- Skip frame snapshots for real-time alerts
- Only show snapshots for uploaded video alerts

### Memory Management:
- Store frames as compressed JPEG data URLs
- Consider cleanup strategies for long videos
- Optional: Only extract frames that have alerts (requires knowing alerts first)

---

## 🎨 UI/UX Enhancements

1. **Loading State:**
   - Show "Extracting frames..." indicator during extraction
   - Progress indicator for long videos

2. **Frame Display:**
   - Show frame snapshot in alert card
   - Display frame number on snapshot
   - Click to view full-size (optional modal)

3. **Error Handling:**
   - Show placeholder if frame extraction fails
   - Gracefully handle missing frames
   - Show message if video format not supported

4. **Performance Indicators:**
   - Show frame extraction progress
   - Warn about memory usage for very long videos

---

## 🔄 Alternative Approach (Future Optimization)

Instead of extracting all frames upfront, we could:
1. Extract frames on-demand when alert is displayed
2. Cache extracted frames in memory
3. Extract only frames that have alerts
4. Use IndexedDB for persistent frame storage

This would reduce initial processing time and memory usage but requires more complex implementation.

---

## ✅ Success Criteria

1. ✅ Frame extraction works for uploaded videos
2. ✅ Frame numbers match between backend and frontend
3. ✅ Alert cards display frame snapshots correctly
4. ✅ No impact on existing functionality
5. ✅ Handles errors gracefully
6. ✅ Works with different video formats and frame rates
7. ✅ Memory usage is reasonable for typical videos

---

## 📦 Files to Create/Modify

### New Files:
- `frontend/src/utils/videoFrameExtractor.js` - Frame extraction utility

### Modified Files:
- `frontend/src/pages/voshan/VideoUpload.jsx` - Add frame extraction
- `frontend/src/components/voshan/AlertCard.jsx` - Display frame snapshots
- `frontend/src/components/voshan/AlertCard.css` - Style frame snapshots

### Optional (Future):
- `frontend/src/pages/voshan/AlertHistory.jsx` - Frame support for historical alerts
- `frontend/src/context/VideoFrameContext.jsx` - Global frame storage (if needed)

---

## 🚀 Implementation Order

1. **Create utility** (videoFrameExtractor.js) - Test independently
2. **Integrate into VideoUpload** - Extract frames when file selected
3. **Update AlertCard** - Display frames
4. **Test thoroughly** - Various video formats and lengths
5. **Optimize if needed** - Memory usage, performance

---

## 📚 References

- HTMLVideoElement API: https://developer.mozilla.org/en-US/docs/Web/API/HTMLVideoElement
- Canvas API: https://developer.mozilla.org/en-US/docs/Web/API/Canvas_API
- Video frame extraction: Browser-based video frame extraction techniques

---

**Status:** Ready for Implementation  
**Priority:** Medium (Nice-to-have feature)  
**Estimated Complexity:** Medium  
**Dependencies:** None (uses browser APIs only)
