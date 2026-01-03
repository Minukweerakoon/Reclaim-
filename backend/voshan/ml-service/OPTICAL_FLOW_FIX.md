# Optical Flow Error Fix

## Problem

The OpenCV optical flow error occurs when video frames have inconsistent dimensions:
```
OpenCV error: (-215:Assertion failed) prevPyr[level * lvlStep1].size() == nextPyr[level * lvlStep2].size()
```

This happens because the BoTSORT tracker uses optical flow internally, which requires consistent frame dimensions across frames.

## Solution Implemented

### 1. Frame Dimension Consistency Check
- All frames are resized to match the first frame's dimensions
- Frame dimensions are tracked and validated before processing
- Warnings are logged when frame size changes are detected

### 2. Error Handling in Tracker
- Added try-catch around tracking operations
- If optical flow error occurs, tracker falls back to detection-only mode
- Prevents crashes and allows processing to continue

### 3. Tracker Reset on Frame Size Change
- If frame dimensions change during processing, tracker is reset
- This prevents optical flow state corruption
- Note: This will lose track continuity but prevents crashes

### 4. Frame Format Validation
- Ensures frames are in correct format (BGR, uint8, 3 channels)
- Skips invalid frames instead of crashing

## Changes Made

### `app.py`
- Added frame dimension tracking (`prev_frame_shape`)
- Enhanced frame resizing with interpolation
- Added try-catch around tracking with automatic recovery
- Improved error messages for optical flow errors

### `tracker.py`
- Added frame validation before tracking
- Added error handling with fallback to detection-only
- Prevents crashes from optical flow errors

## Testing

After these fixes, videos with variable frame dimensions should:
1. Process successfully without crashing
2. Log warnings when frame sizes change
3. Continue processing even if some frames cause errors
4. Provide helpful error messages if issues persist

## If Error Still Occurs

1. **Check video file**: Some videos may have corrupted frames
2. **Try different video**: Test with a video that has consistent dimensions
3. **Check logs**: Look for frame size change warnings
4. **Reduce video size**: Try processing a shorter segment first

## Performance Impact

- Minimal: Frame resizing is fast
- Tracking reset: May lose track continuity but prevents crashes
- Overall: Better than crashing completely

