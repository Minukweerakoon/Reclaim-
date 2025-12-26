import React, { useState, useRef, useEffect } from 'react';

interface CameraCaptureProps {
    onCapture: (blob: Blob, dataUrl: string) => void;
    onCancel?: () => void;
}

export const CameraCapture: React.FC<CameraCaptureProps> = ({ onCapture, onCancel }) => {
    const [isStreaming, setIsStreaming] = useState(false);
    const [capturedImage, setCapturedImage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [facingMode, setFacingMode] = useState<'user' | 'environment'>('environment');

    const videoRef = useRef<HTMLVideoElement>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const streamRef = useRef<MediaStream | null>(null);

    useEffect(() => {
        startCamera();

        return () => {
            stopCamera();
        };
    }, [facingMode]);

    const startCamera = async () => {
        try {
            setError(null);

            // Request camera access
            const constraints: MediaStreamConstraints = {
                video: {
                    facingMode: facingMode,
                    width: { ideal: 1280 },
                    height: { ideal: 720 }
                },
                audio: false
            };

            const stream = await navigator.mediaDevices.getUserMedia(constraints);
            streamRef.current = stream;

            if (videoRef.current) {
                videoRef.current.srcObject = stream;
                videoRef.current.play();
                setIsStreaming(true);
            }
        } catch (err: any) {
            console.error('Camera access error:', err);

            if (err.name === 'NotAllowedError') {
                setError('Camera access denied. Please allow camera permissions and try again.');
            } else if (err.name === 'NotFoundError') {
                setError('No camera found on this device.');
            } else {
                setError('Failed to access camera. Please check your device settings.');
            }

            setIsStreaming(false);
        }
    };

    const stopCamera = () => {
        if (streamRef.current) {
            streamRef.current.getTracks().forEach(track => track.stop());
            streamRef.current = null;
        }
        setIsStreaming(false);
    };

    const capturePhoto = () => {
        if (!videoRef.current || !canvasRef.current) return;

        const video = videoRef.current;
        const canvas = canvasRef.current;

        // Set canvas dimensions to video dimensions
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        // Draw video frame to canvas
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Convert canvas to blob and data URL
        canvas.toBlob(
            (blob) => {
                if (blob) {
                    const dataUrl = canvas.toDataURL('image/jpeg', 0.9);
                    setCapturedImage(dataUrl);
                    stopCamera();
                }
            },
            'image/jpeg',
            0.9
        );
    };

    const retake = () => {
        setCapturedImage(null);
        startCamera();
    };

    const usePhoto = () => {
        if (!capturedImage || !canvasRef.current) return;

        canvasRef.current.toBlob(
            (blob) => {
                if (blob) {
                    onCapture(blob, capturedImage);
                }
            },
            'image/jpeg',
            0.9
        );
    };

    const switchCamera = () => {
        setFacingMode(prevMode => prevMode === 'user' ? 'environment' : 'user');
        setCapturedImage(null);
    };

    return (
        <div className="camera-capture">
            <canvas ref={canvasRef} style={{ display: 'none' }} />

            {error && (
                <div className="camera-capture__error">
                    <p>{error}</p>
                    {onCancel && (
                        <button className="button button--secondary" onClick={onCancel}>
                            Use File Upload Instead
                        </button>
                    )}
                </div>
            )}

            {!error && !capturedImage && (
                <>
                    <video
                        ref={videoRef}
                        className="camera-capture__video"
                        autoPlay
                        playsInline
                        muted
                    />

                    <div className="camera-capture__controls">
                        {onCancel && (
                            <button className="button button--secondary" onClick={onCancel}>
                                Cancel
                            </button>
                        )}

                        <button
                            className="button button--primary"
                            onClick={capturePhoto}
                            disabled={!isStreaming}
                        >
                            📸 Capture Photo
                        </button>

                        {/* Show switch camera button on mobile */}
                        {'mediaDevices' in navigator && 'enumerateDevices' in navigator.mediaDevices && (
                            <button className="button button--quiet" onClick={switchCamera}>
                                🔄 Switch Camera
                            </button>
                        )}
                    </div>
                </>
            )}

            {capturedImage && (
                <>
                    <img
                        src={capturedImage}
                        alt="Captured"
                        className="camera-capture__preview"
                    />

                    <div className="camera-capture__controls">
                        <button className="button button--secondary" onClick={retake}>
                            Retake
                        </button>

                        <button className="button button--primary" onClick={usePhoto}>
                            Use This Photo
                        </button>
                    </div>
                </>
            )}
        </div>
    );
};
