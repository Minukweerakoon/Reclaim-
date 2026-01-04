/**
 * Video Upload Page
 * Allows users to upload videos for suspicious behavior detection
 */

import React, { useState, useRef, useCallback, useEffect } from 'react';
import { processVideo } from '../../services/voshan/detectionApi';
import AlertCard from '../../components/voshan/AlertCard';
import { extractVideoFrames } from '../../utils/videoFrameExtractor';
import './VideoUpload.css';

const VideoUpload = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [cameraId, setCameraId] = useState('');
  const [saveOutput, setSaveOutput] = useState(true);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const [frameMap, setFrameMap] = useState(new Map());
  const [extractingFrames, setExtractingFrames] = useState(false);
  const [frameExtractionProgress, setFrameExtractionProgress] = useState(0);
  
  // Use ref to prevent duplicate submissions (more reliable than state)
  const isProcessingRef = useRef(false);
  const currentRequestIdRef = useRef(null);
  const lastUploadTimeRef = useRef(0);
  const uploadAbortControllerRef = useRef(null);
  const activeRequestRef = useRef(null); // Track active request promise

  const handleFileSelect = async (file) => {
    if (file && file.type.startsWith('video/')) {
      setSelectedFile(file);
      setError(null);
      setResult(null);
      setFrameMap(new Map()); // Clear previous frames
      setFrameExtractionProgress(0);
      
      // Extract frames from the selected video
      try {
        setExtractingFrames(true);
        const frames = await extractVideoFrames(file, {
          onProgress: (currentFrame, totalFrames) => {
            const progress = Math.round((currentFrame / totalFrames) * 100);
            setFrameExtractionProgress(progress);
          },
          quality: 0.8 // Good balance between quality and file size
        });
        console.log('[Frame Extraction] Successfully extracted frames:', {
          totalFrames: frames.size,
          frameNumbers: Array.from(frames.keys()).slice(0, 10), // First 10 frame numbers
          sampleFrameKey: frames.keys().next().value
        });
        setFrameMap(frames);
        setExtractingFrames(false);
        setFrameExtractionProgress(0);
      } catch (err) {
        console.warn('Frame extraction failed:', err);
        // Don't block the user if frame extraction fails
        setExtractingFrames(false);
        setFrameExtractionProgress(0);
        // Continue without frames - alerts will still work, just without snapshots
      }
    } else {
      setError('Please select a valid video file');
    }
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = useCallback(async () => {
    const now = Date.now();
    
    // CRITICAL: Prevent duplicate submissions - check ref FIRST before any async operations
    if (isProcessingRef.current) {
      console.warn('[handleUpload] Upload already in progress, ignoring duplicate request');
      return;
    }

    // Debounce: Prevent rapid successive clicks (within 1000ms - increased from 500ms)
    if (lastUploadTimeRef.current > 0 && now - lastUploadTimeRef.current < 1000) {
      console.warn('[handleUpload] Upload clicked too quickly after previous attempt, ignoring');
      return;
    }

    // Check if there's already an active request promise
    if (activeRequestRef.current) {
      console.warn('[handleUpload] Active request already exists, ignoring duplicate');
      return;
    }

    if (!selectedFile) {
      setError('Please select a video file first');
      return;
    }

    // Set processing flag IMMEDIATELY to prevent duplicates
    isProcessingRef.current = true;
    lastUploadTimeRef.current = now;

    // Cancel any previous abort controller
    if (uploadAbortControllerRef.current) {
      uploadAbortControllerRef.current.abort();
      uploadAbortControllerRef.current = null;
    }

    // Create new abort controller for this upload
    const abortController = new AbortController();
    uploadAbortControllerRef.current = abortController;

    // Generate unique request ID for this upload
    const requestId = `upload-${now}-${Math.random().toString(36).substr(2, 9)}`;
    currentRequestIdRef.current = requestId;
    
    // Update UI state
    setProcessing(true);
    setError(null);
    setResult(null);
    setUploadProgress(0);

    // Create and store the request promise to prevent duplicates
    const requestPromise = (async () => {
      try {
        console.log(`[${requestId}] Starting video upload and processing...`);
        
        const response = await processVideo(
          selectedFile,
          {
            cameraId: cameraId || undefined,
            saveOutput: saveOutput,
            signal: abortController.signal, // Pass abort signal to cancel request if needed
          },
          (progress) => {
            // Only update progress if this is still the current request and not aborted
            if (currentRequestIdRef.current === requestId && !abortController.signal.aborted) {
              setUploadProgress(progress);
            }
          }
        );
        
        return response;
      } finally {
        // Clear active request when done
        if (activeRequestRef.current === requestPromise) {
          activeRequestRef.current = null;
        }
      }
    })();
    
    // Store the active request promise
    activeRequestRef.current = requestPromise;

    try {
      const response = await requestPromise;

      // Check if request was aborted or superseded
      if (abortController.signal.aborted) {
        console.warn(`[${requestId}] Request was aborted, ignoring response`);
        return;
      }

      // Only process response if this is still the current request
      if (currentRequestIdRef.current !== requestId) {
        console.warn(`[${requestId}] Response received but request was superseded, ignoring`);
        return;
      }

      // Check if response indicates success or error
      if (response && response.success === false) {
        // Error response from API (now handled in detectionApi.js)
        const errorMsg = response.message || 'Failed to process video';
        const errorDetails = response.error || response.details?.error || response.details?.message || '';
        const fullError = errorDetails ? `${errorMsg}: ${errorDetails}` : errorMsg;
        console.error(`[${requestId}] API returned error:`, response);
        setError(fullError);
        return;
      }

      if (response && response.success) {
        console.log(`[${requestId}] Video processing completed successfully`);
        
        // Check if this was already processed (backend deduplication)
        if (response.alreadyProcessed) {
          console.log(`[${requestId}] Video was already processed, showing cached results`);
          setError('This video was already processed recently. Showing previous results.');
        }
        
        setResult(response.data);
        
        // Re-extract frames with backend frame count for accurate matching
        // Do this AFTER setting result so we can use the file
        if (selectedFile && response.data?.totalFrames) {
          console.log(`[${requestId}] Re-extracting frames with backend frame count: ${response.data.totalFrames}`);
          try {
            setExtractingFrames(true);
            // Calculate FPS from backend data if available
            const backendFps = response.data.videoInfo?.fps || 30;
            const frames = await extractVideoFrames(selectedFile, {
              onProgress: (currentFrame, totalFrames) => {
                const progress = Math.round((currentFrame / totalFrames) * 100);
                setFrameExtractionProgress(progress);
              },
              quality: 0.8,
              totalFrames: response.data.totalFrames,
              fps: backendFps
            });
            console.log(`[${requestId}] Re-extraction complete: ${frames.size} frames`);
            setFrameMap(frames);
            setExtractingFrames(false);
            setFrameExtractionProgress(0);
          } catch (err) {
            console.warn(`[${requestId}] Frame re-extraction failed:`, err);
            setExtractingFrames(false);
            setFrameExtractionProgress(0);
          }
        }
        
        // Reset form after successful upload (but keep file for re-extraction if needed)
        // Actually, we need to keep the file reference for frame matching
        // Don't clear selectedFile here - user can clear it manually if needed
        // setSelectedFile(null);
        setCameraId('');
      } else {
        // Unexpected response format
        console.error(`[${requestId}] Unexpected response format:`, response);
        setError('Unexpected response from server. Please try again.');
      }
    } catch (err) {
      // Check if request was aborted
      if (abortController.signal.aborted || err.name === 'AbortError' || err.name === 'CanceledError') {
        console.warn(`[${requestId}] Request was aborted, ignoring error`);
        return;
      }

      // Only process error if this is still the current request
      if (currentRequestIdRef.current !== requestId) {
        console.warn(`[${requestId}] Error received but request was superseded, ignoring`);
        return;
      }

      console.error(`[${requestId}] Error processing video:`, err);
      
      // Check if error has response data (from axios)
      if (err.response && err.response.data) {
        const errorData = err.response.data;
        const errorMsg = errorData.message || 'Failed to process video';
        const errorDetails = errorData.error || errorData.details?.error || errorData.details?.message || '';
        const fullError = errorDetails ? `${errorMsg}: ${errorDetails}` : errorMsg;
        setError(fullError);
        return;
      }
      
      // Check for common connection errors
      let errorMessage = 'An error occurred while processing the video';
      
      if (err.code === 'ERR_NETWORK' || err.message === 'Network Error' || err.message?.includes('ERR_CONNECTION_RESET')) {
        errorMessage = 'Connection was reset during video processing. The video may have been processed successfully on the server.';
        const suggestion = 'Please check the alerts page to see if alerts were generated. If not, wait a moment and try uploading again.';
        errorMessage += ` ${suggestion}`;
        
        // Don't allow immediate retry - prevent duplicate processing
        console.warn(`[${requestId}] Connection reset detected. Video may have been processed. Preventing immediate retry.`);
      } else if (err.code === 'ECONNREFUSED' || err.message?.includes('ECONNREFUSED')) {
        errorMessage = 'Cannot connect to backend server. Please ensure the Node.js backend is running on port 5000.';
      } else if (err.code === 'ETIMEDOUT' || err.message?.includes('timeout')) {
        errorMessage = 'Request timed out. Video processing is taking longer than expected.';
        const suggestion = 'This can happen with longer videos. The timeout has been increased to 15 minutes. If the video is very long, consider splitting it into smaller segments.';
        errorMessage += ` ${suggestion}`;
      } else if (err.response?.data?.message) {
        errorMessage = err.response.data.message;
        if (err.response.data.error) {
          errorMessage += `: ${err.response.data.error}`;
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      
      setError(errorMessage);
    } finally {
      // Only reset if this is still the current request
      if (currentRequestIdRef.current === requestId) {
        isProcessingRef.current = false;
        currentRequestIdRef.current = null;
        uploadAbortControllerRef.current = null;
        activeRequestRef.current = null;
        setProcessing(false);
        setUploadProgress(0);
      } else {
        // If request was superseded, still reset the refs to allow new uploads
        console.log(`[${requestId}] Resetting refs for superseded request`);
        isProcessingRef.current = false;
        uploadAbortControllerRef.current = null;
        activeRequestRef.current = null;
      }
    }
  }, [selectedFile, cameraId, saveOutput]); // Removed 'processing' from dependencies to prevent re-creation

  const handleReset = () => {
    // Cancel any ongoing upload
    if (uploadAbortControllerRef.current) {
      uploadAbortControllerRef.current.abort();
      uploadAbortControllerRef.current = null;
    }
    
    // Reset all refs
    isProcessingRef.current = false;
    currentRequestIdRef.current = null;
    lastUploadTimeRef.current = 0;
    activeRequestRef.current = null;
    
    // Reset state
    setSelectedFile(null);
    setCameraId('');
    setSaveOutput(true);
    setResult(null);
    setError(null);
    setUploadProgress(0);
    setProcessing(false);
    setFrameMap(new Map());
    setExtractingFrames(false);
    setFrameExtractionProgress(0);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDuration = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="video-upload-page">
      <div className="upload-header">
        <h1>📹 Upload Video for Detection</h1>
        <p>Upload a video file to detect suspicious behaviors (unattended bags, loitering, running)</p>
      </div>

      <div className="upload-container">
        {/* Upload Section */}
        <div className="upload-section">
          <div
            className={`upload-area ${dragActive ? 'drag-active' : ''} ${selectedFile ? 'has-file' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            {selectedFile ? (
              <div className="file-selected">
                <div className="file-icon">🎬</div>
                <div className="file-info">
                  <div className="file-name">{selectedFile.name}</div>
                  <div className="file-size">{formatFileSize(selectedFile.size)}</div>
                </div>
                <button
                  className="btn-remove"
                  onClick={() => setSelectedFile(null)}
                  title="Remove file"
                >
                  ✕
                </button>
              </div>
            ) : (
              <div className="upload-placeholder">
                <div className="upload-icon">📤</div>
                <p className="upload-text">
                  Drag and drop a video file here, or click to browse
                </p>
                <p className="upload-hint">
                  Supported formats: MP4, AVI, MOV (Max 500MB)
                </p>
                <input
                  type="file"
                  id="video-input"
                  accept="video/*"
                  onChange={handleFileInput}
                  className="file-input"
                />
                <label htmlFor="video-input" className="btn-browse">
                  Browse Files
                </label>
              </div>
            )}
          </div>

          {/* Options */}
          <div className="upload-options">
            <div className="option-group">
              <label htmlFor="camera-id">Camera ID (Optional):</label>
              <input
                type="text"
                id="camera-id"
                value={cameraId}
                onChange={(e) => setCameraId(e.target.value)}
                placeholder="e.g., CAM_001"
                disabled={processing}
              />
            </div>

            <div className="option-group">
              <label>
                <input
                  type="checkbox"
                  checked={saveOutput}
                  onChange={(e) => setSaveOutput(e.target.checked)}
                  disabled={processing}
                />
                Save processed video output
              </label>
            </div>
          </div>

          {/* Upload Progress */}
          {processing && (
            <div className="upload-progress">
              <div className="progress-bar">
                <div
                  className="progress-fill"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
              <p className="progress-text">
                {uploadProgress < 100
                  ? `Uploading... ${uploadProgress}%`
                  : 'Processing video... This may take a few minutes'}
              </p>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="error-message">
              <span className="error-icon">❌</span>
              <span>{error}</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="upload-actions">
            <button
              className="btn-upload"
              onClick={(e) => {
                e.preventDefault();
                e.stopPropagation();
                handleUpload();
              }}
              disabled={!selectedFile || processing}
              type="button"
            >
              {processing ? '⏳ Processing...' : '🚀 Upload & Process Video'}
            </button>
            {(selectedFile || result) && (
              <button
                className="btn-reset"
                onClick={handleReset}
                disabled={processing}
              >
                🔄 Reset
              </button>
            )}
          </div>
        </div>

        {/* Results Section */}
        {result && (
          <div className="results-section">
            <h2>✅ Processing Complete</h2>

            {/* Video Info */}
            <div className="result-info">
              <div className="info-card">
                <div className="info-label">Total Frames</div>
                <div className="info-value">{result.totalFrames || 'N/A'}</div>
              </div>
              <div className="info-card">
                <div className="info-label">Total Detections</div>
                <div className="info-value">{result.totalDetections || 0}</div>
              </div>
              <div className="info-card">
                <div className="info-label">Total Alerts</div>
                <div className="info-value highlight">{result.totalAlerts || 0}</div>
              </div>
            </div>

            {/* Alerts */}
            {result.alerts && result.alerts.length > 0 ? (
              <div className="alerts-section">
                <h3>🚨 Detected Alerts ({result.alerts.length})</h3>
                <div className="alerts-list">
                  {result.alerts.map((alert, index) => {
                    // Get frame snapshot for this alert if available
                    const frameSnapshot = alert.frame !== undefined && alert.frame !== null
                      ? frameMap.get(alert.frame)
                      : null;
                    
                    // Debug logging
                    if (index === 0) {
                      console.log('[Alert Frame Matching] Debug info:', {
                        frameMapSize: frameMap.size,
                        alertFrame: alert.frame,
                        alertFrameType: typeof alert.frame,
                        frameSnapshotExists: !!frameSnapshot,
                        availableFrameNumbers: Array.from(frameMap.keys()).slice(0, 20), // First 20 frame numbers
                        allAlertFrames: result.alerts.map(a => a.frame).slice(0, 10) // First 10 alert frames
                      });
                    }
                    
                    return (
                      <AlertCard
                        key={alert._id || alert.alertId || index}
                        alert={alert}
                        frameSnapshot={frameSnapshot}
                      />
                    );
                  })}
                </div>
              </div>
            ) : (
              <div className="no-alerts">
                <p>✅ No suspicious behaviors detected in this video</p>
              </div>
            )}

            {/* Output Files */}
            {result.outputVideo && (
              <div className="output-files">
                <h3>📁 Output Files</h3>
                <div className="file-links">
                  {result.outputVideo && (
                    <div className="file-link">
                      <span>🎬 Processed Video:</span>
                      <a
                        href={result.outputVideo}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Download
                      </a>
                    </div>
                  )}
                  {result.logJson && (
                    <div className="file-link">
                      <span>📊 Detection Log (JSON):</span>
                      <a
                        href={result.logJson}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Download
                      </a>
                    </div>
                  )}
                  {result.logCsv && (
                    <div className="file-link">
                      <span>📈 Detection Log (CSV):</span>
                      <a
                        href={result.logCsv}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Download
                      </a>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoUpload;

