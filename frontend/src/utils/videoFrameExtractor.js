/**
 * Video Frame Extractor Utility
 * Extracts frames from video files in the browser and stores them with frame numbers
 */

/**
 * Extract frames from a video file
 * @param {File} videoFile - The video file to extract frames from
 * @param {Object} options - Extraction options
 * @param {Function} options.onProgress - Progress callback (frameNumber, totalFrames)
 * @param {number} options.maxFrames - Maximum number of frames to extract (optional, for performance)
 * @param {number} options.quality - JPEG quality (0-1, default 0.8)
 * @returns {Promise<Map<number, string>>} Map of frameNumber -> dataURL
 */
export async function extractVideoFrames(videoFile, options = {}) {
  const { onProgress, maxFrames, quality = 0.8, totalFrames: backendTotalFrames, fps: backendFps } = options;
  
  // Store backend values in variables accessible in the closure
  const backendTotalFramesValue = backendTotalFrames;
  const backendFpsValue = backendFps;
  
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    const videoURL = URL.createObjectURL(videoFile);
    video.src = videoURL;
    video.preload = 'metadata';
    
    // Use crossOrigin to avoid CORS issues
    video.crossOrigin = 'anonymous';
    
    const frames = new Map();
    
    // Handle video load
    video.addEventListener('loadedmetadata', () => {
      // Get video properties
      const duration = video.duration;
      
      // Use backend FPS if provided, otherwise estimate
      // Backend processes frames sequentially, so we need to match the frame count
      let fps = backendFpsValue || 30; // Default to 30 if not provided
      
      // Determine total frames to extract
      // If backend provided total frames, use that for accurate matching
      // Otherwise, estimate from duration and FPS
      let totalFrames;
      if (backendTotalFramesValue && backendTotalFramesValue > 0) {
        // Use backend frame count for accurate matching
        totalFrames = maxFrames 
          ? Math.min(maxFrames, backendTotalFramesValue)
          : backendTotalFramesValue;
        // Use backend FPS if provided, otherwise calculate from duration
        if (!backendFpsValue && duration > 0) {
          fps = totalFrames / duration;
        }
        console.log(`[Frame Extractor] Using backend frame count: ${totalFrames} frames at ${fps.toFixed(2)} FPS`);
      } else {
        // Estimate from duration and FPS
        totalFrames = maxFrames 
          ? Math.min(maxFrames, Math.floor(duration * fps))
          : Math.floor(duration * fps);
        console.log(`[Frame Extractor] Estimating frames from duration: ${totalFrames} frames at ${fps} FPS (duration: ${duration}s)`);
      }
      
      if (totalFrames === 0 || isNaN(totalFrames) || !isFinite(totalFrames)) {
        URL.revokeObjectURL(videoURL);
        reject(new Error('Invalid video duration or frame count'));
        return;
      }
      
      // Calculate frame interval time (time between frames)
      // This ensures we extract frames at consistent intervals matching the FPS
      const frameInterval = 1 / fps;
      
      let framesExtracted = 0;
      let currentFrame = 0;
      
      // Function to extract a frame at a specific frame number
      // Backend uses frame numbers 0, 1, 2, 3... sequentially
      // We need to extract frames at the same positions
      const extractFrameAtTime = (frameNumber) => {
        return new Promise((frameResolve, frameReject) => {
          // Calculate time for this frame number
          // Frame 0 = time 0, Frame 1 = time frameInterval, Frame 2 = time 2*frameInterval, etc.
          const time = frameNumber * frameInterval;
          
          if (time >= duration) {
            frameResolve(null);
            return;
          }
          
          video.currentTime = time;
          
          const onSeeked = () => {
            try {
              // Create canvas to capture frame
              const canvas = document.createElement('canvas');
              canvas.width = video.videoWidth;
              canvas.height = video.videoHeight;
              
              if (canvas.width === 0 || canvas.height === 0) {
                frameResolve(null);
                return;
              }
              
              const ctx = canvas.getContext('2d');
              ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
              
              // Convert to data URL (JPEG)
              const dataURL = canvas.toDataURL('image/jpeg', quality);
              frames.set(frameNumber, dataURL);
              
              framesExtracted++;
              
              // Report progress
              if (onProgress) {
                onProgress(frameNumber, totalFrames);
              }
              
              video.removeEventListener('seeked', onSeeked);
              frameResolve(dataURL);
            } catch (error) {
              video.removeEventListener('seeked', onSeeked);
              frameReject(error);
            }
          };
          
          video.addEventListener('seeked', onSeeked, { once: true });
          
          // Timeout for frame extraction
          setTimeout(() => {
            video.removeEventListener('seeked', onSeeked);
            frameResolve(null);
          }, 5000); // 5 second timeout per frame
        });
      };
      
      // Extract frames sequentially to avoid overwhelming the browser
      const extractAllFrames = async () => {
        try {
          console.log(`[Frame Extractor] Starting extraction: ${totalFrames} frames to extract`);
          for (let frameNumber = 0; frameNumber < totalFrames; frameNumber++) {
            await extractFrameAtTime(frameNumber);
            if (frameNumber % 10 === 0) {
              console.log(`[Frame Extractor] Progress: ${frameNumber}/${totalFrames} frames extracted`);
            }
          }
          
          console.log(`[Frame Extractor] Extraction complete: ${frames.size} frames extracted`);
          URL.revokeObjectURL(videoURL);
          resolve(frames);
        } catch (error) {
          URL.revokeObjectURL(videoURL);
          reject(error);
        }
      };
      
      // Start extraction
      extractAllFrames();
    });
    
    // Handle errors
    video.addEventListener('error', (e) => {
      URL.revokeObjectURL(videoURL);
      const error = video.error;
      reject(new Error(`Video load error: ${error ? error.message : 'Unknown error'}`));
    });
    
    // Load video metadata
    video.load();
  });
}

/**
 * Get a single frame from a video file at a specific frame number
 * @param {File} videoFile - The video file
 * @param {number} frameNumber - Frame number (0-indexed)
 * @param {number} fps - Frames per second (default 30)
 * @returns {Promise<string>} Data URL of the frame
 */
export async function getFrameAt(videoFile, frameNumber, fps = 30) {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    const videoURL = URL.createObjectURL(videoFile);
    video.src = videoURL;
    video.crossOrigin = 'anonymous';
    
    video.addEventListener('loadedmetadata', () => {
      const duration = video.duration;
      const time = frameNumber / fps;
      
      if (time > duration) {
        URL.revokeObjectURL(videoURL);
        reject(new Error(`Frame ${frameNumber} is beyond video duration`));
        return;
      }
      
      video.currentTime = time;
      
      video.addEventListener('seeked', () => {
        try {
          const canvas = document.createElement('canvas');
          canvas.width = video.videoWidth;
          canvas.height = video.videoHeight;
          
          if (canvas.width === 0 || canvas.height === 0) {
            URL.revokeObjectURL(videoURL);
            reject(new Error('Invalid video dimensions'));
            return;
          }
          
          const ctx = canvas.getContext('2d');
          ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
          
          const dataURL = canvas.toDataURL('image/jpeg', 0.8);
          URL.revokeObjectURL(videoURL);
          resolve(dataURL);
        } catch (error) {
          URL.revokeObjectURL(videoURL);
          reject(error);
        }
      }, { once: true });
    });
    
    video.addEventListener('error', () => {
      URL.revokeObjectURL(videoURL);
      const error = video.error;
      reject(new Error(`Video load error: ${error ? error.message : 'Unknown error'}`));
    });
    
    video.load();
  });
}

/**
 * Estimate total frames in a video file
 * @param {File} videoFile - The video file
 * @returns {Promise<number>} Estimated total frame count
 */
export async function estimateFrameCount(videoFile, fps = 30) {
  return new Promise((resolve, reject) => {
    const video = document.createElement('video');
    const videoURL = URL.createObjectURL(videoFile);
    video.src = videoURL;
    
    video.addEventListener('loadedmetadata', () => {
      const duration = video.duration;
      const frameCount = Math.floor(duration * fps);
      URL.revokeObjectURL(videoURL);
      resolve(frameCount);
    });
    
    video.addEventListener('error', () => {
      URL.revokeObjectURL(videoURL);
      reject(new Error('Failed to load video metadata'));
    });
    
    video.load();
  });
}

