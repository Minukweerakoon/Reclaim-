# Video Processing Tips

## Timeout Issues

If you're getting timeout errors, here are some solutions:

### 1. Timeout Has Been Increased
- Default timeout is now **15 minutes** (was 5 minutes)
- This should handle most videos up to ~10-15 minutes long

### 2. For Very Long Videos
If your video is longer than 15 minutes, consider:

**Option A: Split the Video**
- Use video editing software to split into smaller segments (5-10 minutes each)
- Process each segment separately

**Option B: Increase Timeout Further**
Add to `backend/.env`:
```
ML_SERVICE_TIMEOUT=1800000  # 30 minutes in milliseconds
```

**Option C: Process in Background (Future Enhancement)**
- We can add async processing with job queues
- This would allow processing very long videos without timeouts

### 3. Processing Speed Factors

Processing time depends on:
- **Video length** (duration in seconds)
- **Frame rate** (fps - more frames = longer processing)
- **Resolution** (higher resolution = slower)
- **Device** (CPU is slower than GPU)

**Example:**
- 1 minute video at 30fps = ~1800 frames
- At ~0.1 seconds per frame on CPU = ~3 minutes processing time
- 5 minute video = ~15 minutes processing time

### 4. Optimize Your Videos

Before uploading:
- **Reduce resolution** if possible (720p instead of 1080p)
- **Lower frame rate** if acceptable (24fps instead of 30fps)
- **Shorter clips** work better for testing

### 5. Check ML Service Logs

Watch the ML service terminal for progress:
```
Processed 100/1800 frames
Processed 200/1800 frames
...
```

This shows processing is working, just taking time.

### 6. Current Status

- ✅ Timeout increased to 15 minutes
- ✅ Better error messages
- ✅ Progress tracking in ML service logs
- ⏳ Future: Async processing for very long videos

## Quick Reference

| Video Length | Expected Processing Time | Timeout |
|--------------|-------------------------|---------|
| 1-2 minutes  | 3-6 minutes             | ✅ OK   |
| 3-5 minutes  | 9-15 minutes            | ✅ OK   |
| 5-10 minutes | 15-30 minutes           | ⚠️ May timeout |
| 10+ minutes  | 30+ minutes             | ❌ Will timeout |

**Recommendation:** Keep videos under 5 minutes for best results, or split longer videos.

