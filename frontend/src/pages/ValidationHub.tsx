import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useLocation } from 'react-router-dom';
import { validationApi } from '../api/validation';
import { reportsApi } from '../api/reports';
import { xaiApi } from '../api/xai';
import { contextApi } from '../api/context';
import { feedbackApi } from '../api/feedback';
import { useValidationStore } from '../store/useValidationStore';
import { useChatStore } from '../store/useChatStore';
import { useAuth } from '../contexts/AuthContext';
import { useWebSocket } from '../hooks/useWebSocket';
import { ErrorMessage, formatErrorMessage } from '../components/ErrorMessage';
import type { EntityDetectionResponse, SpatialTemporalResponse, XAIExplainResponse, Discrepancy, MissionReport } from '../types/api';

const clamp01 = (value: number) => Math.min(1, Math.max(0, value));

const normalizeScore = (value?: number) => {
    if (value === undefined || value === null || Number.isNaN(value)) {
        return 0;
    }
    if (value > 1) {
        return clamp01(value / 100);
    }
    return clamp01(value);
};

const formatPercent = (value?: number) => Math.round(normalizeScore(value) * 100);

const average = (values: number[]) => {
    if (!values.length) return 0;
    return values.reduce((sum, value) => sum + value, 0) / values.length;
};

function ValidationHub() {
    const location = useLocation();
    const [textInput, setTextInput] = useState('');
    const [visualText, setVisualText] = useState('');
    const [imageFile, setImageFile] = useState<File | null>(null);
    const [audioFile, setAudioFile] = useState<File | null>(null);
    const [recordedUrl, setRecordedUrl] = useState<string | null>(null);
    const [isRecording, setIsRecording] = useState(false);
    const [recordingError, setRecordingError] = useState<string | null>(null);
    const [imagePreview, setImagePreview] = useState<string | null>(null);
    const [isWebcamActive, setIsWebcamActive] = useState(false);
    const [localExtractedInfo, setLocalExtractedInfo] = useState<Record<string, string>>({});
    const [webcamError, setWebcamError] = useState<string | null>(null);
    const [capturedImage, setCapturedImage] = useState<string | null>(null);
    const [_entityResult, setEntityResult] = useState<EntityDetectionResponse | null>(null);
    const [contextResult, setContextResult] = useState<SpatialTemporalResponse | null>(null);
    const [xaiExplain, setXaiExplain] = useState<XAIExplainResponse | null>(null);
    const [analysisError, setAnalysisError] = useState<string | null>(null);
    const [feedbackNote, setFeedbackNote] = useState('');
    const [feedbackStatus, setFeedbackStatus] = useState<string | null>(null);
    const [analysisLoading, setAnalysisLoading] = useState(false);
    const autoSubmitRef = useRef(false);
    const recorderRef = useRef<MediaRecorder | null>(null);
    const recordingChunksRef = useRef<Blob[]>([]);
    const recordingStreamRef = useRef<MediaStream | null>(null);
    const discardRecordingRef = useRef(false);
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const webcamStreamRef = useRef<MediaStream | null>(null);

    const { user } = useAuth();

    const {
        currentResult,
        isLoading,
        error,
        progress,
        progressMessage,
        setResult,
        setLoading,
        setError,
        setProgress,
        pendingText,
        pendingVisualText,
        pendingImageFile,
        pendingAudioFile,
        pendingExtractedInfo,
        clearPending,
        reset,
        intent,
    } = useValidationStore();

    const { pendingImage: chatImage, imagePreview: chatImagePreview, setPendingImage } = useChatStore();

    const clientId = useState(() => `client_${Date.now()}_${Math.random().toString(36).slice(2)}`)[0];

    const { isConnected } = useWebSocket({
        clientId,
        onMessage: (msg) => {
            if (msg.type === 'progress') {
                setProgress(msg.progress || 0, msg.message);
            } else if (msg.type === 'complete' && msg.result) {
                setResult(msg.result);
            } else if (msg.type === 'error') {
                setError(msg.error || 'Validation failed');
            }
        },
        onError: (errorMsg) => {
            console.error('WebSocket error:', errorMsg);
        },
        maxRetries: 5,
    });

    const handleImageChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            if (file.size > 10 * 1024 * 1024) {
                setError('Image file is too large. Maximum size is 10MB.');
                return;
            }
            if (!file.type.startsWith('image/')) {
                setError('Please select a valid image file.');
                return;
            }
            setImageFile(file);
            const reader = new FileReader();
            reader.onload = () => {
                setImagePreview(reader.result as string);
                setPendingImage(file, reader.result as string);
            };
            reader.readAsDataURL(file);
        }
    }, [setError, setPendingImage]);

    const stopRecordingStream = useCallback(() => {
        if (recordingStreamRef.current) {
            recordingStreamRef.current.getTracks().forEach((track) => track.stop());
            recordingStreamRef.current = null;
        }
    }, []);

    const clearRecording = useCallback(() => {
        discardRecordingRef.current = true;
        if (recorderRef.current && recorderRef.current.state !== 'inactive') {
            recorderRef.current.stop();
        }
        stopRecordingStream();
        if (recordedUrl) {
            URL.revokeObjectURL(recordedUrl);
        }
        setRecordedUrl(null);
        setAudioFile(null);
        setRecordingError(null);
        setIsRecording(false);
    }, [recordedUrl, stopRecordingStream]);

    const startRecording = useCallback(async () => {
        if (isRecording) return;
        setRecordingError(null);
        clearRecording();
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            recordingStreamRef.current = stream;
            const recorder = new MediaRecorder(stream);
            recordingChunksRef.current = [];

            recorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    recordingChunksRef.current.push(event.data);
                }
            };

            recorder.onstop = () => {
                if (discardRecordingRef.current) {
                    discardRecordingRef.current = false;
                    setIsRecording(false);
                    stopRecordingStream();
                    return;
                }
                const blob = new Blob(recordingChunksRef.current, { type: recorder.mimeType || 'audio/webm' });
                const fileName = `voice-recording-${Date.now()}.webm`;
                const file = new File([blob], fileName, { type: blob.type });
                const url = URL.createObjectURL(blob);
                setRecordedUrl(url);
                setAudioFile(file);
                setIsRecording(false);
                stopRecordingStream();
            };

            recorderRef.current = recorder;
            recorder.start();
            setIsRecording(true);
        } catch (err) {
            console.error('Recording failed:', err);
            setRecordingError('Microphone access failed. Please enable mic permissions and retry.');
            setIsRecording(false);
            stopRecordingStream();
        }
    }, [clearRecording, isRecording, stopRecordingStream]);

    const stopRecording = useCallback(() => {
        if (!recorderRef.current) return;
        if (recorderRef.current.state !== 'inactive') {
            recorderRef.current.stop();
        }
    }, []);

    const handleAudioChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            if (file.size > 5 * 1024 * 1024) {
                setError('Audio file is too large. Maximum size is 5MB.');
                return;
            }
            clearRecording();
            setAudioFile(file);
        }
    }, [clearRecording, setError]);

    const stopWebcamStream = useCallback(() => {
        if (webcamStreamRef.current) {
            webcamStreamRef.current.getTracks().forEach((track) => track.stop());
            webcamStreamRef.current = null;
        }
        if (videoRef.current) {
            videoRef.current.srcObject = null;
        }
    }, []);

    const startWebcam = useCallback(async () => {
        if (isWebcamActive) return;
        setWebcamError(null);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                }
            });
            webcamStreamRef.current = stream;
            if (videoRef.current) {
                videoRef.current.srcObject = stream;
            }
            setIsWebcamActive(true);
        } catch (err) {
            console.error('Webcam access failed:', err);
            setWebcamError('Camera access denied. Please enable camera permissions.');
            setIsWebcamActive(false);
        }
    }, [isWebcamActive]);

    const stopWebcam = useCallback(() => {
        stopWebcamStream();
        setIsWebcamActive(false);
    }, [stopWebcamStream]);

    const capturePhoto = useCallback(() => {
        if (!videoRef.current || !webcamStreamRef.current) return;

        const video = videoRef.current;
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext('2d');

        if (ctx) {
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            canvas.toBlob((blob) => {
                if (blob) {
                    const fileName = `webcam-capture-${Date.now()}.jpg`;
                    const file = new File([blob], fileName, { type: 'image/jpeg' });
                    const url = canvas.toDataURL('image/jpeg', 0.9);

                    setCapturedImage(url);
                    setImageFile(file);
                    setImagePreview(url);
                    setPendingImage(file, url);
                    stopWebcam();
                }
            }, 'image/jpeg', 0.9);
        }
    }, [stopWebcam]);

    const clearWebcamCapture = useCallback(() => {
        setCapturedImage(null);
        if (capturedImage) {
            // Clean up if needed
        }
    }, [capturedImage]);

    useEffect(() => {
        return () => {
            stopWebcamStream();
            stopRecordingStream();
        };
    }, [stopWebcamStream, stopRecordingStream]);

    useEffect(() => {
        const state = location.state as { prefillText?: string; prefillVisualText?: string } | null;
        if (state?.prefillText) {
            setTextInput(state.prefillText);
        }
        if (state?.prefillVisualText) {
            setVisualText(state.prefillVisualText);
        }
    }, [location.state]);

    useEffect(() => {
        return () => {
            stopRecordingStream();
            if (recordedUrl) {
                URL.revokeObjectURL(recordedUrl);
            }
        };
    }, [recordedUrl, stopRecordingStream]);

    useEffect(() => {
        if (pendingText) {
            setTextInput(pendingText);
        }
        if (pendingVisualText) {
            setVisualText(pendingVisualText);
        }
        if (pendingExtractedInfo && Object.keys(pendingExtractedInfo).length > 0) {
            setLocalExtractedInfo(pendingExtractedInfo);
        }
        if (chatImage) {
            setImageFile(chatImage);
            setImagePreview(chatImagePreview);
        } else if (pendingImageFile) {
            setImageFile(pendingImageFile);
            const reader = new FileReader();
            reader.onload = () => {
                setImagePreview(reader.result as string);
                setPendingImage(pendingImageFile, reader.result as string);
            };
            reader.readAsDataURL(pendingImageFile);
        }
        if (pendingAudioFile) {
            setAudioFile(pendingAudioFile);
        }
        if (pendingText || pendingVisualText || pendingImageFile || pendingAudioFile) {
            autoSubmitRef.current = true;
            clearPending();
        }
    }, [
        pendingText,
        pendingVisualText,
        pendingImageFile,
        pendingAudioFile,
        pendingExtractedInfo,
        clearPending,
        chatImage,
        chatImagePreview,
        setPendingImage
    ]);

    const handleSubmit = async () => {
        if (!textInput && !imageFile && !audioFile) {
            setError('Please provide at least one input (text, image, or audio)');
            return;
        }

        setLoading(true);
        setError(null);
        setContextResult(null);
        setXaiExplain(null);
        setProgress(0, 'Preparing validation request...');

        try {
            setProgress(10, 'Sending to server...');

            // Auto-detect intent from text if not provided in state (e.g. user bypassed chat)
            let effectiveIntent = intent;
            if (!effectiveIntent && textInput) {
                const match = textInput.match(/\bintent:\s*(lost|found)\b/i);
                if (match) {
                    effectiveIntent = match[1].toLowerCase() as 'lost' | 'found';
                }
            }

            const result = await validationApi.validateComplete({
                text: textInput || undefined,
                visualText: visualText || undefined,
                imageFile: imageFile || undefined,
                audioFile: audioFile || undefined,
                language: 'en',
                // Supabase routing — both intent and user required
                intent: effectiveIntent || undefined,
                userId: user?.id,
                userEmail: user?.email ?? undefined,
                supabaseId: currentResult?.supabase_id || undefined,
            });
            setProgress(100, 'Complete!');
            setResult(result);

            // Auto-populate context/XAI panels to match previous UX behavior.
            // This keeps validation outputs visible without extra button clicks.
            const extractedFromResult: Record<string, string> = {
                ...localExtractedInfo,
            };

            const completenessEntities = result?.text?.completeness?.entities ?? {};
            const textEntities = result?.text?.entities ?? {};

            const pickFirst = (value: unknown): string => {
                if (Array.isArray(value) && value.length) return String(value[0] ?? '').trim();
                if (typeof value === 'string') return value.trim();
                return '';
            };

            if (!extractedFromResult.item_type) extractedFromResult.item_type = pickFirst(completenessEntities?.item_type) || pickFirst(textEntities?.item_mentions);
            if (!extractedFromResult.color) extractedFromResult.color = pickFirst(completenessEntities?.color) || pickFirst(textEntities?.color_mentions);
            if (!extractedFromResult.brand) extractedFromResult.brand = pickFirst(completenessEntities?.brand) || pickFirst(textEntities?.brand_mentions);
            if (!extractedFromResult.location) extractedFromResult.location = pickFirst(completenessEntities?.location) || pickFirst(textEntities?.location_mentions);
            if (!extractedFromResult.time) extractedFromResult.time = pickFirst(completenessEntities?.time);

            const contextItem = extractedFromResult.item_type;
            const contextLocation = extractedFromResult.location;
            const contextTime = extractedFromResult.time;

            if (contextItem && contextLocation) {
                try {
                    const context = await contextApi.validateContext({
                        item_type: contextItem,
                        location: contextLocation,
                        time: contextTime || undefined,
                    });
                    setContextResult(context);
                } catch (ctxErr) {
                    console.warn('[ValidationHub] Auto context analysis failed:', formatErrorMessage(ctxErr));
                }
            }

            try {
                const transcription = typeof result?.voice?.transcription === 'string'
                    ? result.voice.transcription
                    : result?.voice?.transcription?.transcription;

                const xaiResponse = await xaiApi.explainEnhanced({
                    text: textInput || undefined,
                    image_path: result?.image?.image_path,
                    transcription: transcription || undefined,
                });
                setXaiExplain(xaiResponse);
            } catch (xaiErr) {
                console.warn('[ValidationHub] Auto XAI explanation failed:', formatErrorMessage(xaiErr));
            }

            // ── Save to shared items table (background, non-blocking) ──
            if (user?.id && (effectiveIntent === 'lost' || effectiveIntent === 'found')) {
                const overallConfidence = result?.confidence?.overall_confidence ?? null;

                // Use local preserved structured chat data if available
                const extracted = localExtractedInfo || {};
                const itemCategory = extracted['item_type'] || visualText?.split(' ').slice(-1)[0] || '';
                const locationValue = (() => {
                    // Priority 1: structured extracted info from chat (most reliable)
                    if (extracted['location'] && extracted['location'].trim()) {
                        return extracted['location'].trim();
                    }
                    // Priority 2: parse "location: X" key-value from the summaryText
                    // e.g. "intent: found, item type: keyboard, location: 4th floor of computing faculty building"
                    const locKv = textInput?.match(/\blocation:\s*([^,]+)/i);
                    if (locKv) return locKv[1].trim();
                    // Priority 3: simple "at the X" regex as last resort
                    const locAt = textInput?.match(/\bat\s+(?:the\s+)?([a-zA-Z\s]{2,40})/i);
                    return locAt ? locAt[1].trim() : '';
                })();
                const colorValue = extracted['color'] || '';
                // description = human-readable summary, not the full structured blob
                const descriptionValue = extracted['description'] || textInput || '';

                if (!result?.supabase_id) {
                    reportsApi.saveReport({
                        item_type: itemCategory,
                        user_category: itemCategory,
                        description: descriptionValue,
                        color: colorValue,
                        location: locationValue,
                        intention: effectiveIntent as 'lost' | 'found',
                        confidence_score: overallConfidence,
                        routing: overallConfidence != null && overallConfidence >= 0.7 ? 'auto' : 'manual',
                        action: 'review',
                        validation_results: {
                            cross_modal: result?.cross_modal ?? {},
                            individual_scores: result?.confidence?.individual_scores ?? {},
                            supabase_id: result?.supabase_id,
                        },
                    }).then((saved) => {
                        console.info('[Reclaim] Report saved to items table fallback:', saved.report_id);
                    }).catch((err) => {
                        console.warn('[Reclaim] Report save fallback failed:', err);
                    });
                } else {
                    console.info('[Reclaim] Report already saved by backend to items table with ID:', result.supabase_id);
                }
            }

            // Note: Context analysis auto-run removed to prevent loops
            // User can manually click "Run context analysis" button if needed
        } catch (err: unknown) {
            let errorMsg = formatErrorMessage(err);
            if (err && typeof err === 'object' && 'message' in err) {
                errorMsg = (err as Record<string, unknown>).message as string;
            }
            setError(errorMsg);
        } finally {
            setLoading(false);
            setProgress(0);
        }
    };

    // Auto-submit when arriving from chat with pre-filled data
    useEffect(() => {
        if (autoSubmitRef.current && (textInput || imageFile || audioFile) && !isLoading && !currentResult) {
            autoSubmitRef.current = false;
            handleSubmit();
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [textInput, imageFile, audioFile]);

    const handleReset = () => {
        setTextInput('');
        setVisualText('');
        setImageFile(null);
        setAudioFile(null);
        clearRecording();
        setImagePreview(null);
        setPendingImage(null, null);
        setEntityResult(null);
        setContextResult(null);
        setXaiExplain(null);
        setAnalysisError(null);
        setFeedbackNote('');
        setFeedbackStatus(null);
        reset();
    };

    const handleAnalyzeContext = async () => {
        // Prevent re-triggering if already validating or if we already have results
        if (analysisLoading || isLoading) {
            console.log('[ValidationHub] Context analysis already in progress, skipping');
            return;
        }

        if (!textInput.trim() && !currentResult) {
            setAnalysisError('Provide text input before running context analysis.');
            return;
        }

        setAnalysisError(null);
        setAnalysisLoading(true);
        
        try {
            console.log('[ValidationHub] Running context analysis with existing data');
            
            // Extract entity data from text input
            const extractedEntities: Record<string, string> = {};
            textInput.split(',').forEach((segment) => {
                const colonIdx = segment.indexOf(':');
                if (colonIdx > 0) {
                    const key = segment.slice(0, colonIdx).trim().toLowerCase().replace(/\s+/g, '_');
                    const val = segment.slice(colonIdx + 1).trim();
                    if (val && key !== 'intent') extractedEntities[key] = val;
                }
            });

            // Merge with localExtractedInfo if available
            const merged = { ...extractedEntities, ...localExtractedInfo };

            console.log('[ValidationHub] Extracted entities:', merged);
            const itemType = merged.item_type || merged['item type'];
            const locationValue = merged.location;
            const timeValue = merged.time;

            if (!itemType || !locationValue) {
                setAnalysisError('Need at least item type and location to run context analysis.');
                return;
            }

            const response = await contextApi.validateContext({
                item_type: itemType,
                location: locationValue,
                time: timeValue || undefined,
            });

            console.log('[ValidationHub] Context analysis response:', response);
            setContextResult(response);
            setAnalysisError(null);
        } catch (err) {
            const message = formatErrorMessage(err);
            console.error('[ValidationHub] Context analysis error:', message);
            setAnalysisError(message);
        } finally {
            setAnalysisLoading(false);
        }
    };

    const handleExplainXai = async () => {
        if (!currentResult) return;
        setAnalysisError(null);
        setAnalysisLoading(true);
        try {
            const response = await xaiApi.explainEnhanced({
                text: textInput || undefined,
                image_path: currentResult.image?.image_path,
                transcription: currentResult.voice?.transcription,
            });
            setXaiExplain(response);
        } catch (err) {
            const message = formatErrorMessage(err);
            setAnalysisError(message);
        } finally {
            setAnalysisLoading(false);
        }
    };

    const handleSubmitFeedback = async () => {
        if (!currentResult || !feedbackNote.trim()) return;
        setFeedbackStatus(null);
        setAnalysisLoading(true);
        try {
            const response = await feedbackApi.submitFeedback({
                input_text: textInput || 'N/A',
                original_prediction: currentResult as unknown as Record<string, any>,
                user_correction: { notes: feedbackNote },
                feedback_type: 'user_correction',
            });
            setFeedbackStatus(response.message || 'Feedback recorded.');
            setFeedbackNote('');
        } catch (err) {
            const message = formatErrorMessage(err);
            setFeedbackStatus(message);
        } finally {
            setAnalysisLoading(false);
        }
    };

    const stepIndex = useMemo(() => {
        if (currentResult) return 4;
        if (audioFile) return 3;
        if (imageFile) return 2;
        if (textInput) return 1;
        return 0;
    }, [currentResult, audioFile, imageFile, textInput]);

    const confidenceScore = normalizeScore(
        currentResult?.confidence?.overall_confidence
    );
    const clipScore = normalizeScore(currentResult?.cross_modal?.image_text?.similarity);
    const textScore = normalizeScore(currentResult?.text?.overall_score);
    const imageScore = normalizeScore(currentResult?.image?.overall_score);
    const audioScore = normalizeScore(currentResult?.voice?.confidence);

    const entitiesPreview: [string, string][] = useMemo(() => {
        const merged: Record<string, string> = {};

        // 1) Pull from completeness.entities (item_type, brand, time, etc.)
        const completenessEntities = currentResult?.text?.completeness?.entities ?? {};
        for (const [key, values] of Object.entries(completenessEntities)) {
            const v = Array.isArray(values) ? values[0] : String(values);
            if (v) merged[key] = v;
        }

        // 2) Pull from text.entities mentions — prefer longer/more specific values
        const textEntities = currentResult?.text?.entities;
        if (textEntities) {
            if (textEntities.color_mentions?.length) {
                const val = textEntities.color_mentions[0];
                if (!merged['color'] || val.length > merged['color'].length) merged['color'] = val;
            }
            if (textEntities.location_mentions?.length) {
                const val = textEntities.location_mentions[0];
                if (!merged['location'] || val.length > merged['location'].length) merged['location'] = val;
            }
            if (textEntities.brand_mentions?.length) {
                const val = textEntities.brand_mentions[0];
                if (!merged['brand'] || val.length > merged['brand'].length) merged['brand'] = val;
            }
            if (textEntities.item_mentions?.length) {
                const val = textEntities.item_mentions[0];
                if (!merged['item_type'] || val.length > merged['item_type'].length) merged['item_type'] = val;
            }
        }

        // Filter out stopword-like entries (prepositions that shouldn't be locations)
        const stopwords = new Set(['in', 'at', 'on', 'by', 'to', 'of', 'the', 'a', 'an', 'near']);
        for (const [key, value] of Object.entries(merged)) {
            if (stopwords.has(value.toLowerCase())) delete merged[key];
        }

        // 3) Fallback: parse chatbot-structured "key: value" pairs from text input
        //    e.g. "intent: lost, Item type: camera, color: black, location: movie theater, time: today"
        if (textInput) {
            textInput.split(',').forEach((seg) => {
                const idx = seg.indexOf(':');
                if (idx > 0) {
                    const rawKey = seg.slice(0, idx).trim().toLowerCase().replace(/\s+/g, '_');
                    const val = seg.slice(idx + 1).trim();
                    if (val && !stopwords.has(val.toLowerCase()) && rawKey !== 'intent') {
                        if (!merged[rawKey] || val.length > merged[rawKey].length) {
                            merged[rawKey] = val;
                        }
                    }
                }
            });
        }

        return Object.entries(merged).slice(0, 6) as [string, string][];
    }, [currentResult, textInput]);


    // Build discrepancies from cross-modal analysis
    const discrepancies: Discrepancy[] = useMemo(() => {
        if (!currentResult?.cross_modal?.image_text) return [];
        const it = currentResult.cross_modal.image_text as any;
        const items: Discrepancy[] = [];
        if (!it.valid) {
            items.push({ type: 'Cross-Modal Mismatch', description: it.feedback });
        }
        if (it.mismatch_detection?.mismatches) {
            it.mismatch_detection.mismatches.forEach((m: any) => {
                items.push({ type: `Mismatch: ${m.type}`, description: m.message });
            });
        }
        it.suggestions?.forEach((s: string) => {
            items.push({ type: 'Suggestion', description: s });
        });
        return items;
    }, [currentResult]);

    // Build mission report from backend feedback + confidence routing
    const missionReport: MissionReport | null = useMemo(() => {
        if (!currentResult) return null;
        const routing = currentResult.confidence?.routing?.replace(/_/g, ' ') || 'unknown';
        const action = currentResult.confidence?.action?.replace(/_/g, ' ') || 'unknown';
        const msg = currentResult.feedback?.message || 'Validation complete.';
        const suggestions = currentResult.feedback?.suggestions || [];
        const missing = currentResult.feedback?.missing_elements || [];
        let summary = msg;
        if (missing.length) summary += ` Missing: ${missing.join(', ')}.`;
        if (suggestions.length) summary += ` ${suggestions.join(' ')}`;
        summary += ` Quality tier: ${routing}.`;
        return { summary, recommendation: `Recommended action: ${action}.` };
    }, [currentResult]);

    const qualityGates = [
        { label: 'Text completeness', value: textScore },
        { label: 'Image integrity', value: imageScore },
        { label: 'Audio clarity', value: audioScore },
        { label: 'Cross-modal alignment', value: clipScore },
    ];

    const { data: reportsData } = useQuery({
        queryKey: ['reports', 'overlay'],
        queryFn: () => reportsApi.getMyReports(),
        refetchInterval: 30000,
    });

    const overlayReports = useMemo(() => {
        const baseReports = reportsData?.reports ? [...reportsData.reports] : [];
        if (currentResult) {
            baseReports.unshift({
                id: 'current',
                request_id: currentResult.request_id,
                timestamp: currentResult.timestamp || new Date().toISOString(),
                confidence: currentResult.confidence,
                cross_modal: currentResult.cross_modal,
            });
        }
        return baseReports
            .filter((report) => Boolean(report.timestamp))
            .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    }, [reportsData, currentResult]);

    const confidenceSeries = useMemo(() => {
        return overlayReports
            .slice(0, 12)
            .reverse()
            .map((report) => normalizeScore(report.confidence?.overall_confidence));
    }, [overlayReports]);

    const confidenceDrift = useMemo(() => {
        const recent = confidenceSeries.slice(-3);
        const previous = confidenceSeries.slice(-6, -3);
        const recentAvg = average(recent);
        const previousAvg = average(previous);
        return {
            recentAvg,
            previousAvg,
            delta: recentAvg - previousAvg,
        };
    }, [confidenceSeries]);

    const sparklinePoints = useMemo(() => {
        if (confidenceSeries.length < 2) return '';
        const width = 160;
        const height = 48;
        const step = width / (confidenceSeries.length - 1);
        return confidenceSeries
            .map((value, index) => {
                const x = index * step;
                const y = height - value * height;
                return `${x},${y}`;
            })
            .join(' ');
    }, [confidenceSeries]);

    const temporalHeatmap = useMemo(() => {
        const days = 7;
        const buckets = 6;
        const today = new Date();
        const midnight = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        const labels = Array.from({ length: days }, (_, index) => {
            const day = new Date(midnight);
            day.setDate(day.getDate() - (days - 1 - index));
            return day.toLocaleDateString('en-US', { weekday: 'short' });
        });

        const matrix = Array.from({ length: days }, () => Array.from({ length: buckets }, () => [] as number[]));

        overlayReports.forEach((report) => {
            if (!report.timestamp) return;
            const timestamp = new Date(report.timestamp);
            const reportDay = new Date(timestamp.getFullYear(), timestamp.getMonth(), timestamp.getDate());
            const diffDays = Math.floor((midnight.getTime() - reportDay.getTime()) / (24 * 60 * 60 * 1000));
            if (diffDays < 0 || diffDays >= days) return;
            const dayIndex = days - 1 - diffDays;
            const bucket = Math.min(buckets - 1, Math.floor(timestamp.getHours() / 4));

            const alignmentPenalty = report.cross_modal?.image_text?.valid === false ? 0.2 : 0;
            const discrepancyPenalty = alignmentPenalty > 0 ? 0.4 : 0;
            const confidencePenalty = normalizeScore(report.confidence?.overall_confidence) < 0.5 ? 0.2 : 0;
            const consistencyScore = Math.max(0, 1 - (alignmentPenalty + discrepancyPenalty + confidencePenalty));

            matrix[dayIndex][bucket].push(consistencyScore);
        });

        const averaged = matrix.map((row) => row.map((cell) => average(cell)));
        return { labels, buckets, values: averaged };
    }, [overlayReports]);

    const lineageCards = useMemo(() => overlayReports.slice(0, 3), [overlayReports]);

    return (
        <div className="animate-fade-in">
            {/* Page Title */}
            <div className="mb-8 text-center">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-cyan-500/10 border border-cyan-500/20 text-cyan-300 text-xs font-medium mb-4">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500"></span>
                    </span>
                    Validation Stage
                </div>
                <h1 className="text-4xl md:text-5xl font-bold mb-3 tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white to-slate-400">
                    Validation Hub
                </h1>
                <p className="text-slate-400 max-w-2xl mx-auto">
                    Proactive multimodal input validation. Visual attention overlay and real-time analysis.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[420px_1fr] gap-6">
                <section className="glass-panel-heavy rounded-2xl overflow-hidden flex flex-col">
                <div className="p-6 border-b border-white/10">
                    <div className="flex justify-between items-center text-[10px] uppercase tracking-[0.2em] text-slate-500">
                        <span>Sequence Progress</span>
                        <span className="text-primary">Step {stepIndex}/4</span>
                    </div>
                    <div className="flex items-center gap-2 mt-3">
                        {[1, 2, 3, 4].map((step) => (
                            <div
                                key={step}
                                className={`flex-1 h-1 rounded-full ${step <= stepIndex ? 'bg-primary shadow-neon-cyan' : 'bg-slate-700'}`}
                            />
                        ))}
                    </div>
                    <div className="flex justify-between mt-2 text-[10px] font-mono text-slate-400">
                        <span className={stepIndex >= 1 ? 'text-primary' : ''}>DESC</span>
                        <span className={stepIndex >= 2 ? 'text-primary' : ''}>IMG</span>
                        <span className={stepIndex >= 3 ? 'text-primary' : ''}>VOICE</span>
                        <span className={stepIndex >= 4 ? 'text-primary' : ''}>RSLT</span>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto p-6 space-y-5">
                    <div className="flex items-start justify-between">
                        <div>
                            <h2 className="text-xl font-bold text-white">Validation Hub</h2>
                            <p className="text-xs text-slate-400 mt-1">Proactive multimodal input validation</p>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-slate-500">
                            <span className={`h-1.5 w-1.5 rounded-full ${isConnected ? 'bg-neon-green/50' : 'bg-slate-600'}`} />
                            {isConnected ? 'Live link' : 'Syncing'}
                        </div>
                    </div>

                    <div className="glass-panel rounded-xl p-4">
                        <div className="text-[11px] uppercase tracking-widest text-primary mb-3">Text Intake</div>
                        <textarea
                            value={textInput}
                            onChange={(e) => setTextInput(e.target.value)}
                            placeholder="Describe the item, location, and context"
                            className="w-full h-24 bg-slate-900/80 border border-white/10 rounded-lg p-3 text-sm text-white placeholder-slate-500 focus:border-primary focus:ring-1 focus:ring-primary outline-none resize-none"
                        />
                        <div className="mt-3">
                            <label className="text-[11px] text-slate-400 mb-2 block uppercase tracking-widest">Visual description for CLIP</label>
                            <input
                                type="text"
                                value={visualText}
                                onChange={(e) => setVisualText(e.target.value)}
                                placeholder="Short visual descriptor"
                                className="w-full bg-slate-900/80 border border-white/10 rounded-lg p-3 text-sm text-white placeholder-slate-500 focus:border-primary focus:ring-1 focus:ring-primary outline-none"
                            />
                        </div>
                    </div>

                    <div className="glass-panel rounded-xl p-4">
                        <div className="text-[11px] uppercase tracking-widest text-primary mb-3">Image Evidence</div>

                        {/* Webcam Capture Section */}
                        {isWebcamActive ? (
                            <div className="space-y-3 mb-4">
                                <div className="relative rounded-lg overflow-hidden bg-slate-900/80">
                                    <video
                                        ref={videoRef}
                                        autoPlay
                                        playsInline
                                        muted
                                        className="w-full h-48 object-cover"
                                    />
                                    <div className="absolute top-2 left-2 px-2 py-1 bg-alert-red/80 rounded text-[10px] uppercase tracking-widest text-white flex items-center gap-1">
                                        <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
                                        Live
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <button
                                        type="button"
                                        onClick={capturePhoto}
                                        className="flex-1 px-4 py-2 rounded-lg text-xs uppercase tracking-widest border border-primary/50 text-primary hover:bg-primary/20 transition-colors"
                                    >
                                        📸 Capture photo
                                    </button>
                                    <button
                                        type="button"
                                        onClick={stopWebcam}
                                        className="px-4 py-2 rounded-lg text-xs uppercase tracking-widest border border-alert-red/50 text-alert-red hover:bg-alert-red/10 transition-colors"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-3 mb-4">
                                <button
                                    type="button"
                                    onClick={startWebcam}
                                    disabled={!!imagePreview}
                                    className="w-full px-4 py-2 rounded-lg text-xs uppercase tracking-widest border border-primary/50 text-primary hover:bg-primary/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    📷 Use webcam
                                </button>
                                {webcamError && (
                                    <div className="text-xs text-alert-red">{webcamError}</div>
                                )}
                            </div>
                        )}

                        {/* File Upload Section */}
                        <div className="border border-dashed border-white/20 rounded-lg p-4 text-center hover:border-primary transition-colors">
                            <input
                                type="file"
                                accept="image/*"
                                onChange={handleImageChange}
                                className="hidden"
                                id="image-upload"
                                disabled={isWebcamActive}
                            />
                            <label htmlFor="image-upload" className="cursor-pointer">
                                {imagePreview ? (
                                    <img src={imagePreview} alt="Preview" className="max-h-36 mx-auto rounded-lg" />
                                ) : (
                                    <div className="text-xs text-slate-400">
                                        {isWebcamActive ? 'Webcam active' : 'Click to upload image file'}
                                    </div>
                                )}
                            </label>
                            {imageFile && (
                                <button
                                    onClick={() => {
                                        setImageFile(null);
                                        setImagePreview(null);
                                        clearWebcamCapture();
                                        setPendingImage(null, null);
                                    }}
                                    className="mt-3 text-[11px] text-alert-red hover:underline"
                                >
                                    Remove
                                </button>
                            )}
                        </div>
                    </div>

                    <div className="glass-panel rounded-xl p-4">
                        <div className="text-[11px] uppercase tracking-widest text-primary mb-3">Voice Recording</div>
                        <div className="space-y-3">
                            <div className="flex items-center gap-3">
                                <button
                                    type="button"
                                    onClick={isRecording ? stopRecording : startRecording}
                                    className={`px-4 py-2 rounded-lg text-xs uppercase tracking-widest border transition-colors ${isRecording
                                        ? 'border-alert-red/50 text-alert-red hover:bg-alert-red/10'
                                        : 'border-primary/50 text-primary hover:bg-primary/20'
                                        }`}
                                >
                                    {isRecording ? 'Stop recording' : 'Record'}
                                    <span className="ml-2">🎤</span>
                                </button>
                                {isRecording && (
                                    <div className="flex items-center gap-2 text-[10px] uppercase tracking-widest text-slate-400">
                                        <div className="flex items-end gap-1">
                                            {[0, 150, 300, 450].map((delay) => (
                                                <span
                                                    key={delay}
                                                    className="w-1 bg-primary/80 rounded-full animate-bounce"
                                                    style={{ height: `${10 + delay / 30}px`, animationDelay: `${delay}ms` }}
                                                />
                                            ))}
                                        </div>
                                        Recording...
                                    </div>
                                )}
                            </div>

                            {recordedUrl && (
                                <audio controls src={recordedUrl} className="w-full" />
                            )}

                            {recordingError && (
                                <div className="text-xs text-alert-red">{recordingError}</div>
                            )}

                            {recordedUrl && !isRecording && (
                                <div className="flex items-center gap-3">
                                    <button
                                        type="button"
                                        onClick={clearRecording}
                                        className="text-[11px] text-alert-red hover:underline"
                                    >
                                        Remove
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => {
                                            clearRecording();
                                            startRecording();
                                        }}
                                        className="text-[11px] text-primary hover:underline"
                                    >
                                        Retry
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>

                    <div className="glass-panel rounded-xl p-4">
                        <div className="text-[11px] uppercase tracking-widest text-primary mb-3">Audio Context</div>
                        <div className="border border-dashed border-white/20 rounded-lg p-4 text-center hover:border-primary transition-colors">
                            <input
                                type="file"
                                accept="audio/*"
                                onChange={handleAudioChange}
                                className="hidden"
                                id="audio-upload"
                            />
                            <label htmlFor="audio-upload" className="cursor-pointer">
                                {audioFile ? (
                                    <div className="text-xs text-slate-200">{audioFile.name}</div>
                                ) : (
                                    <div className="text-xs text-slate-400">Click to attach audio evidence</div>
                                )}
                            </label>
                            {audioFile && (
                                <button
                                    onClick={() => setAudioFile(null)}
                                    className="mt-3 text-[11px] text-alert-red hover:underline"
                                >
                                    Remove
                                </button>
                            )}
                        </div>
                    </div>

                    {isLoading && (
                        <div className="glass-panel rounded-xl p-4">
                            <div className="flex items-center justify-between text-[11px] text-slate-400 uppercase tracking-widest">
                                <span>Processing</span>
                                <span className="text-primary">{Math.round(progress)}%</span>
                            </div>
                            <div className="w-full bg-slate-900 rounded-full h-1.5 mt-3 overflow-hidden">
                                <div
                                    className="bg-gradient-to-r from-primary to-neon-purple h-full transition-all duration-300"
                                    style={{ width: `${progress}%` }}
                                />
                            </div>
                            {progressMessage && (
                                <p className="text-[11px] text-slate-400 mt-2">{progressMessage}</p>
                            )}
                        </div>
                    )}

                    {error && (
                        <ErrorMessage
                            title="Validation Error"
                            message={error}
                            onRetry={handleSubmit}
                            onDismiss={() => setError(null)}
                        />
                    )}
                </div>

                <div className="p-5 border-t border-white/10 bg-gradient-to-t from-background-dark via-background-dark/80 to-transparent">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={handleSubmit}
                            disabled={isLoading || (!textInput && !imageFile && !audioFile)}
                            className="flex-1 bg-primary/20 text-primary border border-primary/50 hover:bg-primary/30 disabled:opacity-50 disabled:cursor-not-allowed text-xs font-bold uppercase tracking-widest py-3 rounded-lg transition-all"
                        >
                            {isLoading ? 'Validating' : 'Run Validation'}
                        </button>
                        <button
                            onClick={handleReset}
                            className="px-4 py-3 text-xs uppercase tracking-widest border border-white/10 text-slate-300 rounded-lg hover:bg-white/5 transition-colors"
                        >
                            Reset
                        </button>
                    </div>
                </div>
            </section>

            <section className="flex flex-col gap-6">
                <div className="glass-panel rounded-2xl p-4 relative overflow-hidden">
                    <div className="absolute top-0 left-0 w-full h-[2px] bg-primary/80" />
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <div className="text-[11px] uppercase tracking-[0.2em] text-primary">XAI Vision Stage</div>
                            <div className="text-[10px] text-slate-400 mt-1">Visual attention overlay and input scan</div>
                        </div>
                        <div className="text-[10px] text-slate-400 uppercase">Heatmap</div>
                    </div>
                    <div className="relative rounded-xl overflow-hidden bg-black/70 border border-white/10 h-72 flex items-center justify-center">
                        {currentResult?.xai_heatmap_url ? (
                            <img src={currentResult.xai_heatmap_url} alt="XAI Heatmap" className="w-full h-full object-contain" />
                        ) : imagePreview ? (
                            <img src={imagePreview} alt="Preview" className="w-full h-full object-contain" />
                        ) : (
                            <div className="text-xs text-slate-500">Awaiting visual input</div>
                        )}
                        <div className="absolute inset-x-0 h-[2px] bg-primary shadow-neon-cyan animate-scan-vertical" />
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="glass-panel rounded-2xl p-6 flex flex-col items-center justify-center">
                        <div className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-4">Confidence Core</div>
                        <div className="relative w-36 h-36">
                            <svg className="w-full h-full -rotate-90">
                                <circle className="text-slate-800" cx="72" cy="72" r="60" fill="transparent" stroke="currentColor" strokeWidth="8" />
                                <circle
                                    className="text-primary"
                                    cx="72"
                                    cy="72"
                                    r="60"
                                    fill="transparent"
                                    stroke="currentColor"
                                    strokeDasharray="377"
                                    strokeDashoffset={`${377 - Math.round(confidenceScore * 377)}`}
                                    strokeWidth="8"
                                />
                            </svg>
                            <div className="absolute inset-0 flex flex-col items-center justify-center">
                                <span className="text-3xl font-bold text-white neon-text-cyan">
                                    {confidenceScore > 0 ? `${Math.round(confidenceScore * 100)}%` : '—'}
                                </span>
                                <span className="text-[10px] text-primary/80 uppercase tracking-widest">Authenticity</span>
                            </div>
                        </div>
                    </div>

                    <div className="glass-panel rounded-2xl p-6 relative overflow-hidden">
                        <div className="text-[11px] uppercase tracking-[0.2em] text-slate-400">Plausibility Matrix</div>
                        <div className="flex items-center justify-center h-40">
                            <div className="relative w-32 h-32 rounded-full border border-white/10">
                                <div className="absolute inset-0 rounded-full border border-white/5 scale-75" />
                                <div className="absolute inset-0 rounded-full border border-white/5 scale-50" />
                                <div className="absolute inset-0 rounded-full bg-gradient-to-r from-transparent via-primary/10 to-transparent animate-radar-sweep border-r border-primary/30" />
                                <div className="absolute top-[30%] left-[55%] w-2 h-2 bg-neon-green rounded-full shadow-neon-cyan" />
                            </div>
                        </div>
                        <div className="text-[10px] text-slate-400">
                            {contextResult
                                ? `Plausibility: ${Math.round(contextResult.plausibility_score * 100)}% — ${contextResult.explanation}`
                                : currentResult
                                    ? 'Click "Run Context Analysis" below to score plausibility.'
                                    : 'Spatial-temporal coherence pending.'
                            }
                        </div>
                    </div>

                    <div className="glass-panel rounded-2xl p-6">
                        <div className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-4">Quality Gates</div>
                        <div className="space-y-3">
                            {qualityGates.map((gate) => (
                                <div key={gate.label} className="flex items-center justify-between">
                                    <div className="text-xs text-slate-300">{gate.label}</div>
                                    <div className="w-32 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                                        <div className="h-full bg-primary" style={{ width: `${Math.round(gate.value * 100)}%` }} />
                                    </div>
                                    <div className="text-[10px] text-slate-400 w-10 text-right">{Math.round(gate.value * 100)}%</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="glass-panel rounded-2xl p-6">
                        <div className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-4">Entity Extraction</div>
                        {entitiesPreview.length > 0 ? (
                            <div className="grid grid-cols-2 gap-3">
                                {entitiesPreview.map(([key, value]) => (
                                    <div key={key} className="bg-slate-900/60 border border-white/10 rounded-lg p-3">
                                        <div className="text-[10px] text-slate-500 uppercase">{key.replace(/_/g, ' ')}</div>
                                        <div className="text-sm text-white mt-1">{String(value)}</div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-xs text-slate-500">Entities will appear after validation.</div>
                        )}
                        <button
                            type="button"
                            onClick={handleAnalyzeContext}
                            disabled={analysisLoading}
                            className="mt-4 w-full text-[10px] uppercase tracking-widest border border-primary/40 text-primary py-2 rounded-lg hover:bg-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {analysisLoading ? 'Analyzing...' : 'Run context analysis'}
                        </button>
                    </div>

                    <div className="glass-panel rounded-2xl p-6">
                        <div className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-4">Cross-Modal Alignment</div>
                        <div className="space-y-3">
                            <div>
                                <div className="flex justify-between text-[10px] text-slate-400 uppercase">
                                    <span>CLIP similarity</span>
                                    <span className="text-primary">{formatPercent(clipScore)}%</span>
                                </div>
                                <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden mt-2">
                                    <div className="h-full bg-primary" style={{ width: `${formatPercent(clipScore)}%` }} />
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-[10px] text-slate-400 uppercase">
                                    <span>Voice-text similarity</span>
                                    <span className="text-neon-purple">{formatPercent(currentResult?.confidence?.cross_modal_scores?.voice_text_similarity)}%</span>
                                </div>
                                <div className="w-full h-2 bg-slate-900 rounded-full overflow-hidden mt-2">
                                    <div className="h-full bg-neon-purple" style={{ width: `${formatPercent(currentResult?.confidence?.cross_modal_scores?.voice_text_similarity)}%` }} />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                    <div className="glass-panel rounded-2xl p-6">
                        <div className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-4">Confidence Drift</div>
                        <div className="flex items-center justify-between mb-3">
                            <div>
                                <div className="text-2xl font-bold text-white">{Math.round(confidenceDrift.recentAvg * 100)}%</div>
                                <div className="text-[10px] text-slate-500 uppercase">Recent average</div>
                            </div>
                            <div className={`text-xs font-mono ${confidenceDrift.delta >= 0 ? 'text-accent-emerald' : 'text-alert-red'}`}>
                                {confidenceDrift.delta >= 0 ? '+' : ''}{Math.round(confidenceDrift.delta * 100)}%
                            </div>
                        </div>
                        {sparklinePoints ? (
                            <svg viewBox="0 0 160 48" className="w-full h-12">
                                <polyline
                                    points={sparklinePoints}
                                    fill="none"
                                    stroke="#06b6d4"
                                    strokeWidth="2"
                                    strokeLinejoin="round"
                                    strokeLinecap="round"
                                />
                            </svg>
                        ) : (
                            <div className="text-[10px] text-slate-500">Not enough data for drift.</div>
                        )}
                    </div>

                    <div className="glass-panel rounded-2xl p-6">
                        <div className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-4">Temporal Consistency</div>
                        <div className="grid grid-cols-7 gap-1 text-[9px] text-slate-500 mb-2">
                            {temporalHeatmap.labels.map((label) => (
                                <div key={label} className="text-center">{label}</div>
                            ))}
                        </div>
                        <div className="grid grid-cols-7 gap-1">
                            {temporalHeatmap.values.map((row, rowIndex) => (
                                row.map((value, colIndex) => {
                                    const alpha = 0.15 + value * 0.75;
                                    return (
                                        <div
                                            key={`${rowIndex}-${colIndex}`}
                                            className="h-5 rounded border border-white/5"
                                            style={{ backgroundColor: `rgba(6, 182, 212, ${alpha})` }}
                                        />
                                    );
                                })
                            ))}
                        </div>
                        <div className="flex justify-between text-[9px] text-slate-500 mt-2">
                            <span>00-04</span>
                            <span>20-24</span>
                        </div>
                    </div>

                    <div className="glass-panel rounded-2xl p-6">
                        <div className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-4">QA Lineage</div>
                        <div className="space-y-3">
                            {lineageCards.length ? lineageCards.map((report) => (
                                <div key={report.id} className="bg-slate-900/60 border border-white/10 rounded-lg p-3">
                                    <div className="flex items-center justify-between">
                                        <span className="text-xs font-bold text-white">ID-{(report.id || report.request_id || '').slice(0, 6).toUpperCase()}</span>
                                        <span className="text-[10px] text-slate-500 font-mono">
                                            {new Date(report.timestamp).toLocaleTimeString()}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-2 text-[10px] text-slate-500 mt-2">
                                        {report.input_types?.includes('text') && <span>TXT</span>}
                                        {report.input_types?.includes('image') && <span>IMG</span>}
                                        {report.input_types?.includes('voice') && <span>VOICE</span>}
                                        <span className="ml-auto">{report.confidence?.routing?.replace(/_/g, ' ') || ''}</span>
                                    </div>
                                </div>
                            )) : (
                                <div className="text-[10px] text-slate-500">No lineage data available.</div>
                            )}
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="glass-panel rounded-2xl p-6 border border-alert-red/30">
                        <div className="text-[11px] uppercase tracking-[0.2em] text-alert-red mb-3">Discrepancy Engine</div>
                        {discrepancies.length ? (
                            <div className="space-y-3">
                                {discrepancies.slice(0, 3).map((disc, idx) => (
                                    <div key={idx} className="bg-slate-900/70 border border-alert-red/20 rounded-lg p-3">
                                        <div className="text-xs text-alert-red uppercase">{disc.type}</div>
                                        <div className="text-xs text-slate-300 mt-1">{disc.description}</div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-xs text-slate-500">{currentResult ? 'No discrepancies detected.' : 'Run validation to check.'}</div>
                        )}
                        {currentResult && (
                            <button
                                type="button"
                                onClick={handleExplainXai}
                                disabled={analysisLoading}
                                className="mt-4 w-full text-[10px] uppercase tracking-widest border border-white/10 text-slate-300 py-2 rounded-lg hover:bg-white/5 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {analysisLoading ? 'Explaining...' : 'Run XAI explanation'}
                            </button>
                        )}
                    </div>

                    <div className="glass-panel rounded-2xl p-6">
                        <div className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-3">Mission Report</div>
                        {missionReport ? (
                            <div className="space-y-3">
                                <div className="text-xs text-slate-300">{missionReport.summary}</div>
                                <div className="text-xs text-primary">{missionReport.recommendation}</div>
                            </div>
                        ) : (
                            <div className="text-xs text-slate-500">No mission report available yet.</div>
                        )}
                    </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <div className="glass-panel rounded-2xl p-6">
                        <div className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-3">Spatial-Temporal Context</div>
                        {contextResult ? (
                            <div className="space-y-2 text-xs text-slate-300">
                                <div>Plausibility: {Math.round(contextResult.plausibility_score * 100)}%</div>
                                <div className="text-slate-400">{contextResult.explanation}</div>
                                <div className="text-[10px] uppercase text-slate-500">Context: {contextResult.context}</div>
                            </div>
                        ) : (
                            <div className="text-xs text-slate-500">Run context analysis to score plausibility.</div>
                        )}
                    </div>

                    <div className="glass-panel rounded-2xl p-6">
                        <div className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-3">Active Learning Feedback</div>
                        <textarea
                            value={feedbackNote}
                            onChange={(event) => setFeedbackNote(event.target.value)}
                            placeholder="Describe any corrections or mismatches to improve the model."
                            className="w-full h-24 bg-slate-900/80 border border-white/10 rounded-lg p-3 text-xs text-white placeholder-slate-500 focus:border-primary focus:ring-1 focus:ring-primary outline-none resize-none"
                        />
                        <button
                            type="button"
                            onClick={handleSubmitFeedback}
                            disabled={!currentResult || !feedbackNote.trim() || analysisLoading}
                            className="mt-3 w-full text-[10px] uppercase tracking-widest border border-primary/40 text-primary py-2 rounded-lg hover:bg-primary/20 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {analysisLoading ? 'Submitting...' : 'Submit correction'}
                        </button>
                        {feedbackStatus && (
                            <div className="mt-2 text-[10px] text-slate-400">{feedbackStatus}</div>
                        )}
                    </div>
                </div>

                {analysisError && (
                    <div className="glass-panel rounded-2xl p-4 border border-alert-red/30 text-xs text-alert-red">
                        {analysisError}
                    </div>
                )}

                {xaiExplain && (
                    <div className="glass-panel rounded-2xl p-6">
                        <div className="text-[11px] uppercase tracking-[0.2em] text-slate-400 mb-3">XAI Explanation</div>
                        <div className="text-xs text-slate-300 mb-2">{xaiExplain.explanation}</div>
                        {xaiExplain.discrepancies?.length ? (
                            <div className="space-y-2">
                                {xaiExplain.discrepancies.map((disc, idx) => (
                                    <div key={idx} className="bg-slate-900/70 border border-white/10 rounded-lg p-3">
                                        <div className="text-[10px] uppercase text-alert-red">{disc.type}</div>
                                        <div className="text-xs text-slate-300 mt-1">{disc.explanation}</div>
                                    </div>
                                ))}
                            </div>
                        ) : null}
                    </div>
                )}
            </section>
            </div>
        </div>
    );
}

export default ValidationHub;
