import React, {
    useEffect,
    useCallback,
    useMemo,
    useState
} from 'react';
import { ChatInterface } from '../components/Chat/ChatWindow';
import { FileUploadZone } from '../components/Uploads/Dropzone';
import { VoiceRecorder } from '../components/Uploads/AudioRecorder';
import { CameraCapture } from '../components/Uploads/CameraCapture';
import { useWebSocket } from '../hooks/useWebSocket';
import { useValidation } from '../hooks/useValidation';
import { FeedbackModal } from '../components/Feedback/FeedbackModal';
import { ChatInput } from '../components/Chat/ChatInput';
import {
    ValidationSummary,
    SummaryCard,
} from '../components/Validation/ValidationSummary';
import { PlausibilityCard } from '../components/Validation/PlausibilityCard';
import { DiscrepancyCard } from '../components/Validation/DiscrepancyCard';
import { Modal } from '../components/UI/Modal';
import { useValidationStore, ValidationState } from '../store/useValidationStore';
import { useNavigate } from 'react-router-dom';

const COLOR_KEYWORDS = [
    'black', 'white', 'red', 'blue', 'green', 'yellow', 'brown', 'gray', 'grey', 'purple', 'orange', 'pink', 'silver', 'gold',
] as const;

const BRAND_KEYWORDS = [
    'gucci', 'coach', 'prada', 'lacoste', 'nike', 'adidas', 'michael kors', 'samsung', 'apple', 'sony'
] as const;

const ITEM_KEYWORDS = [
    'phone', 'mobile', 'iphone', 'samsung', 'smartphone', 'cellphone', 'bag', 'backpack', 'purse', 'wallet', 'keys', 'keychain', 'laptop', 'tablet', 'ipad', 'watch', 'airpods', 'headphones', 'umbrella', 'camera',
] as const;


const formatPercent = (value?: number | null) => {
    if (typeof value !== 'number' || Number.isNaN(value)) {
        return '--';
    }
    if (value > 1) {
        return `${Math.round(value)}%`;
    }
    return `${Math.round(value * 100)}%`;
};

const formatSharpnessScore = (sharpness?: { score?: number }) => {
    if (!sharpness || typeof sharpness.score !== 'number') {
        return '--';
    }
    return `${sharpness.score.toFixed(1)}%`;
};

const listOrFallback = (items?: string[] | null, fallback: string = 'None') => {
    if (!items || items.length === 0) {
        return fallback;
    }
    return items.join(', ');
};

const pickMentions = (
    primary?: string[] | null,
    secondary?: string[] | null
): string[] | null => {
    if (primary && primary.length > 0) {
        return primary;
    }
    if (secondary && secondary.length > 0) {
        return secondary;
    }
    return null;
};

export const ValidationPage: React.FC = () => {
    const navigate = useNavigate();

    // Global State
    const messages = useValidationStore((state) => state.messages);
    const conversationState = useValidationStore((state) => state.conversationState);
    const validationState = useValidationStore((state) => state.validationState);
    const isProcessing = useValidationStore((state) => state.isProcessing);
    const progressLog = useValidationStore((state) => state.progressLog);
    const activeTaskId = useValidationStore((state) => state.activeTaskId);

    // Actions
    const {
        addBotMessage,
        addUserMessage,
        setConversationState,
        setUserIntention,
        updateValidationState,
        setIsProcessing,
        pushProgress,
        setActiveTaskId
    } = useValidationStore();

    // Local UI State
    const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
    const [isCameraOpen, setIsCameraOpen] = useState(false);
    const [isUploadOpen, setIsUploadOpen] = useState(false);

    // Hooks
    const { sendMessage, wsConnected, lastMessage } = useWebSocket();
    const { validateComplete, validateImage, validateText, validateVoice, sendChatMessage, validateContext, getAttentionMap, submitFeedback } = useValidation();

    // Initial Message on Mount (if empty)
    useEffect(() => {
        if (messages.length === 0) {
            addBotMessage(
                "Hi! I'm here to help you report your lost item using our multimodal validation system. What did you lose today?"
            );
        }
    }, []); // Run once on mount

    // WebSocket Updates
    useEffect(() => {
        if (!lastMessage) return;

        if (typeof lastMessage.progress === 'number') {
            const messageDetails = lastMessage.message && lastMessage.message.length > 0
                ? ` — ${lastMessage.message}`
                : '';
            pushProgress('Realtime validation', `${Math.max(-1, lastMessage.progress)}%${messageDetails}`);
        }

        if (typeof lastMessage.task_id === 'string') {
            setActiveTaskId(lastMessage.task_id);
        }

        if (lastMessage.result) {
            updateValidationState({ overallResult: lastMessage.result });
            if (conversationState !== 'completed') {
                addBotMessage('Realtime validation is complete. I have applied the final confidence score to your report.');
                setConversationState('completed');
                // Navigate to results after a short delay? Or let user decide?
                // For now, let's keep it in chat until they click "View Report" or similar, or we trigger it here.
                // navigate('/results'); // Optional auto-redirect
            }
        }
    }, [lastMessage, pushProgress, updateValidationState, addBotMessage, conversationState, setActiveTaskId, setConversationState]);


    // Helper functions (Utilities)
    const detectColorFromText = useCallback((text: string): string | undefined => {
        const lower = text.toLowerCase();
        return COLOR_KEYWORDS.find((color) => lower.includes(color.toLowerCase()));
    }, []);

    const detectBrandFromText = useCallback((text: string): string | undefined => {
        const lower = text.toLowerCase();
        return BRAND_KEYWORDS.find((brand) => lower.includes(brand.toLowerCase()));
    }, []);


    // --- Interaction Handlers (Refactored to use useValidationStore.getState()) ---

    const handleDescriptionInput = useCallback(
        async (description: string) => {
            const currentState = useValidationStore.getState().validationState;
            const currentText = currentState.text || '';
            const separator = currentText ? ' ' : '';
            const fullText = currentText + separator + description;

            updateValidationState({ text: fullText });
            setIsProcessing(true);
            pushProgress('Description analysis', 'Running');

            try {
                const textResult = await validateText(fullText, {
                    itemTypeHint: currentState.itemType,
                    colorHint: currentState.colorHint,
                });
                updateValidationState({ textResult });

                if (textResult?.valid) {
                    const mentions = textResult?.entities?.item_mentions?.length > 0
                        ? textResult.entities.item_mentions.join(', ')
                        : 'the item';

                    if (textResult?.clarification_questions && textResult.clarification_questions.length > 0) {
                        addBotMessage(textResult.clarification_questions.join(' '));
                        addBotMessage(`I noted ${mentions}, but please clarify the above if needed. If you have a photo of the item, upload it so I can verify the visual details.`);
                    } else {
                        addBotMessage(`Excellent description! I noted ${mentions}. If you have a photo of the item, upload it so I can verify the visual details.`);
                    }

                    pushProgress('Description analysis', formatPercent(textResult.overall_score));
                    setConversationState('awaiting_image');
                } else {
                    const completenessFeedback = textResult?.completeness?.feedback ?? 'This description is too vague to evaluate.';
                    if (textResult?.completeness?.is_vague) {
                        addBotMessage(completenessFeedback);
                    } else {
                        const missingDetails = listOrFallback(textResult?.completeness?.missing_info, 'more context');
                        addBotMessage(`Thanks! Could you expand the description by adding: ${missingDetails}? This helps match your report faster.`);
                    }
                    pushProgress('Description analysis', 'Needs more detail');
                }
            } catch (error) {
                addBotMessage('I could not analyse that description. Please try again or simplify the text.');
                pushProgress('Description analysis', 'Failed');
            } finally {
                setIsProcessing(false);
            }
        },
        [validateText, updateValidationState, addBotMessage, pushProgress, setIsProcessing, setConversationState]
    );

    const handleImageUpload = useCallback(
        async (file: File) => {
            updateValidationState({ image: file });
            setIsProcessing(true);
            addBotMessage('Analyzing your photo now...');
            pushProgress('Image analysis', 'Processing');

            try {
                const state = useValidationStore.getState().validationState;
                const itemType = state.itemType || '';
                const textDescription = state.text || '';
                const fullDescription = itemType ? `${itemType} ${textDescription}`.trim() : textDescription;

                const imageResult = await validateImage(file, fullDescription);
                updateValidationState({ imageResult });
                pushProgress('Image analysis', formatPercent(imageResult?.overall_score));

                if (imageResult?.valid) {
                    const detected = imageResult?.objects?.detections?.[0]?.class || 'your item';

                    if (state.text) {
                        // Build COMPLETE description
                        const parts: string[] = [];
                        if (state.colorHint) parts.push(state.colorHint);
                        if (state.brandHint) parts.push(state.brandHint);
                        if (state.itemType) parts.push(state.itemType);
                        if (state.text) parts.push(state.text);

                        const fullCompleteDescription = parts.join(' ').trim();

                        const visualParts = [];
                        if (state.colorHint) visualParts.push(state.colorHint);
                        if (state.brandHint) visualParts.push(state.brandHint);
                        if (state.itemType) visualParts.push(state.itemType);
                        const visualOnlyDescription = visualParts.length > 0 ? `A photo of a ${visualParts.join(' ')}` : '';

                        const combined = await validateComplete({
                            image: file,
                            text: fullCompleteDescription,
                            visualText: visualOnlyDescription,
                        });

                        updateValidationState({
                            textResult: combined.text,
                            imageResult: combined.image,
                            crossModalPreview: combined.cross_modal,
                        });

                        if (combined?.cross_modal && state.text) {
                            getAttentionMap(file, state.text).then(attMap => {
                                if (attMap && !attMap.error) {
                                    updateValidationState({ attentionResult: attMap });
                                }
                            }).catch(e => console.warn('Heatmap generation skipped', e));
                        }

                        const imageText = combined?.cross_modal?.image_text;
                        if (imageText?.valid) {
                            addBotMessage(`Nice! The photo clearly shows ${detected} and matches your description. A quick voice note can add even more context if you have time.`);
                            setConversationState('awaiting_voice');
                        } else {
                            const similarity = formatPercent(imageText?.similarity);
                            const xaiExplanation = combined?.cross_modal?.xai_explanation;
                            let feedbackMsg = imageText?.feedback || `The photo highlights ${detected}, but it does not quite align with the written description (similarity ${similarity}).`;

                            if (xaiExplanation && xaiExplanation.has_discrepancy && xaiExplanation.discrepancies?.length > 0) {
                                const discrepancyDetails = xaiExplanation.discrepancies
                                    .map((d: any) => `• ${d.type}: ${d.explanation}`)
                                    .join('\n');
                                feedbackMsg = `Image and text are not well aligned (similarity: ${similarity}, threshold: 0.85). Could you clarify or update the description?\n\n🔍 Discrepancy Analysis:\n${discrepancyDetails}\n\nSeverity: ${xaiExplanation.severity}\nSuggestion: ${xaiExplanation.suggestion}`;
                            }
                            addBotMessage(feedbackMsg);
                            setConversationState('resolving_mismatch');
                        }
                    } else {
                        addBotMessage(`Great shot! I can see ${detected}. If you have not already, please describe the item so I can link the visual details.`);
                    }
                } else {
                    const issues: string[] = [];
                    if (!imageResult?.sharpness?.valid) issues.push('the image looks blurry');
                    if (!imageResult?.objects?.valid) issues.push('the main item is difficult to recognise');
                    addBotMessage(`I could not confirm the photo because ${issues.join(' and ')}. Try retaking the photo with better lighting and focus.`);
                }
            } catch (error) {
                addBotMessage('Something went wrong while processing that photo. Please try again with a different image.');
                pushProgress('Image analysis', 'Failed');
            } finally {
                setIsProcessing(false);
            }
        },
        [validateImage, validateComplete, addBotMessage, updateValidationState, pushProgress, getAttentionMap, setConversationState, setIsProcessing]
    );

    const handleImageCapture = useCallback(
        async (blob: Blob, dataUrl: string) => {
            const file = new File([blob], 'camera_capture.jpg', { type: 'image/jpeg' });
            await handleImageUpload(file);
            setIsCameraOpen(false);
        },
        [handleImageUpload]
    );

    const finalizeSubmission = useCallback(async () => {
        const state = useValidationStore.getState().validationState;
        if (!state.text) {
            addBotMessage('Please provide a description before finalising the report.');
            return;
        }

        setIsProcessing(true);
        pushProgress('Full validation', 'Running');

        try {
            const payload: { text?: string; image?: File; voice?: Blob; } = { text: state.text };
            if (state.image) payload.image = state.image;
            if (state.voice) payload.voice = state.voice;

            if (wsConnected) {
                sendMessage({
                    type: 'validate',
                    text: state.text,
                    image_path: state.imageResult?.image_path,
                    audio_path: state.voiceResult?.audio_path,
                    language: 'en',
                });
            }

            const completeResult = await validateComplete(payload);
            updateValidationState({ overallResult: completeResult });

            const confidenceScore = completeResult?.confidence?.overall_confidence ?? null;
            const action = completeResult?.confidence?.action ?? 'review';

            addBotMessage(`All set! Your report scored ${formatPercent(confidenceScore)} confidence and will be ${action.replace('_', ' ')}. We will notify you as soon as we find a match.`);
            pushProgress('Full validation', formatPercent(confidenceScore));
            setConversationState('completed');

            // NEW: Suggest viewing results page
            // setTimeout(() => navigate('/results'), 2000);

        } catch (error) {
            addBotMessage('I was unable to finalise the report. Please try again once more.');
            pushProgress('Full validation', 'Failed');
        } finally {
            setIsProcessing(false);
        }
    }, [validateComplete, wsConnected, sendMessage, updateValidationState, addBotMessage, pushProgress, setConversationState, setIsProcessing, navigate]);


    const handleVoiceRecording = useCallback(
        async (audioBlob: Blob) => {
            updateValidationState({ voice: audioBlob });
            setIsProcessing(true);
            addBotMessage('Processing your voice note...');
            pushProgress('Voice analysis', 'Processing');

            try {
                const voiceResult = await validateVoice(audioBlob);
                updateValidationState({ voiceResult });

                if (voiceResult?.valid) {
                    const transcription = voiceResult?.transcription?.transcription || 'your description';
                    addBotMessage(`I heard: "${transcription}". Let me confirm everything lines up.`);
                    pushProgress('Voice analysis', formatPercent(voiceResult?.overall_score));

                    const state = useValidationStore.getState().validationState;
                    if (state.text) {
                        const combined = await validateComplete({
                            voice: audioBlob,
                            text: state.text,
                        });
                        const voiceText = combined?.cross_modal?.voice_text;
                        updateValidationState({
                            crossModalPreview: {
                                ...(state.crossModalPreview ?? {}),
                                voice_text: voiceText,
                            },
                        });

                        if (voiceText?.valid) {
                            addBotMessage('Great! Your voice message adds consistent details. I will now generate the final confidence score.');
                            await finalizeSubmission();
                        } else {
                            addBotMessage('I noticed some differences between what you said and what you wrote. Which version should I use?');
                        }
                    } else {
                        addBotMessage('Thanks! Once you add a text description I will align the two.');
                    }
                } else {
                    const feedback = voiceResult?.quality?.feedback || 'the transcription quality was not sufficient';
                    addBotMessage(`I could not understand the recording because ${feedback}. Could you try again in a quieter space?`);
                    pushProgress('Voice analysis', 'Needs re-recording');
                }
            } catch (error) {
                addBotMessage('I had trouble processing that recording. Please try again in a moment.');
                pushProgress('Voice analysis', 'Failed');
            } finally {
                setIsProcessing(false);
            }
        },
        [validateVoice, validateComplete, addBotMessage, updateValidationState, pushProgress, finalizeSubmission, setIsProcessing]
    );

    const handleUserInput = useCallback(
        async (input: string) => {
            const trimmed = input.trim();
            if (!trimmed || isProcessing) return;

            addUserMessage(trimmed);
            setIsProcessing(true);
            pushProgress('AI Analysis', 'Thinking...');

            try {
                const messages = useValidationStore.getState().messages;
                const history = messages.map(msg => ({
                    role: msg.type === 'user' ? 'user' : 'model',
                    content: msg.content
                }));

                const response = await sendChatMessage(trimmed, history);

                if (response.bot_response) {
                    addBotMessage(response.bot_response, { feedbackRecorded: response.feedback_recorded || false });
                }

                if (response.extracted_info) {
                    const info = response.extracted_info;
                    const updates: Partial<ValidationState> = {};
                    if (info.item_type) updates.itemType = info.item_type;
                    if (info.color) updates.colorHint = info.color;
                    if (info.brand) updates.brandHint = info.brand;

                    const currentState = useValidationStore.getState().validationState;
                    let newText = currentState.text || '';
                    if (info.location && !newText.includes(info.location)) newText += ` at ${info.location}`;
                    if (info.time && !newText.includes(info.time)) newText += ` around ${info.time}`;

                    if (newText !== currentState.text) updates.text = newText;

                    if (Object.keys(updates).length > 0) {
                        updateValidationState(updates);
                        pushProgress('Extracted Details', 'Updated');
                    }

                    if (info.item_type && info.location) {
                        validateContext(info.item_type, info.location, info.time)
                            .then(result => updateValidationState({ spatialTemporalResult: result }))
                            .catch(err => console.error("Context validation failed", err));
                    }
                }

                if (response.next_action === 'ask_for_image') {
                    setConversationState('awaiting_image');
                } else if (response.next_action === 'validate') {
                    const currentState = useValidationStore.getState().validationState;
                    if (currentState.text) {
                        setIsProcessing(true);
                        pushProgress('Description analysis', 'Running');
                        try {
                            const textResult = await validateText(currentState.text, {
                                itemTypeHint: currentState.itemType,
                                colorHint: currentState.colorHint,
                            });
                            updateValidationState({ textResult });
                            if (textResult?.valid) {
                                pushProgress('Description analysis', formatPercent(textResult.overall_score));
                                setConversationState('awaiting_image');
                                addBotMessage("I've got the details. If you have a photo, please upload it now.");
                            } else {
                                pushProgress('Description analysis', 'Needs detail');
                                addBotMessage("I need a bit more detail to verify this report. Could you be more specific?");
                            }
                        } catch (e) {
                            console.error("Validation failed", e);
                        } finally {
                            setIsProcessing(false);
                        }
                    }
                } else if (response.next_action === 'ask_for_details') {
                    setConversationState('item_details');
                }

                if (response.intention && response.intention !== 'unknown') {
                    setUserIntention(response.intention as 'lost' | 'found' | 'inquiry');
                }

            } catch (error) {
                addBotMessage("I'm having trouble connecting right now. Please try again.");
            } finally {
                setIsProcessing(false);
            }
        },
        [sendChatMessage, addBotMessage, addUserMessage, pushProgress, validateContext, validateText, updateValidationState, setConversationState, setIsProcessing, setUserIntention]
    );

    const handleFileUploadWrapper = useCallback(
        async (file: File) => {
            await handleImageUpload(file);
            setIsUploadOpen(false);
        },
        [handleImageUpload]
    );

    // Summary Cards (Memoized)
    const stepSummary = useMemo(() => {
        const steps = [
            { id: 'description', complete: Boolean(validationState.textResult?.valid || validationState.overallResult) },
            { id: 'image', complete: Boolean(validationState.imageResult?.valid) },
            { id: 'voice', complete: Boolean(validationState.voiceResult) },
            { id: 'final', complete: Boolean(validationState.overallResult) },
        ];
        const firstIncomplete = steps.findIndex((step) => !step.complete);
        return steps.map((step, index) => ({ ...step, active: firstIncomplete === index }));
    }, [validationState]);

    const summaryCards = useMemo<SummaryCard[]>(() => {
        const { textResult, imageResult, voiceResult, overallResult, itemType, colorHint, brandHint, crossModalPreview } = validationState;
        const crossModal = overallResult?.cross_modal ?? crossModalPreview ?? {};

        const itemMentions = pickMentions(itemType ? [itemType] : textResult?.entities?.item_mentions, textResult?.completeness?.entities?.item_type || itemType);
        const colorMentions = pickMentions(colorHint ? [colorHint] : textResult?.entities?.color_mentions, textResult?.completeness?.entities?.color || colorHint);
        const brandMentions = pickMentions(brandHint ? [brandHint] : textResult?.entities?.brand_mentions, textResult?.completeness?.entities?.brand || brandHint);

        return [
            {
                id: 'text',
                title: 'Description quality',
                status: textResult ? (textResult.valid ? 'Complete' : 'Needs revision') : 'Waiting',
                metric: formatPercent(textResult?.overall_score),
                details: textResult ? [
                    `Completeness: ${formatPercent(textResult?.completeness?.score ?? textResult?.overall_score)}`,
                    `Mentioned items: ${listOrFallback(itemMentions)}`,
                    `Detected colors: ${listOrFallback(colorMentions)}`,
                    `Brand cues: ${listOrFallback(brandMentions)}`,
                    `Missing details: ${listOrFallback(textResult?.completeness?.missing_info)}`,
                ] : ['Add a descriptive summary of your item to begin.'],
            },
            {
                id: 'image',
                title: 'Image insights',
                status: imageResult ? (imageResult.valid ? 'Clear' : 'Needs retake') : 'Waiting',
                metric: formatPercent(imageResult?.overall_score),
                details: imageResult ? [
                    `Sharpness: ${formatSharpnessScore(imageResult?.sharpness)}`,
                    imageResult?.objects?.detections?.length ? `Detected: ${imageResult.objects.detections.slice(0, 3).map((d: any) => `${d.class} (${Math.round(d.confidence * 100)}%)`).join(', ')}` : 'No objects detected',
                ] : ['Upload a recent photo to boost match accuracy.'],
                actionHint: imageResult && !imageResult.valid ? 'Try retaking the photo: keep the wallet centered and use brighter lighting.' : undefined,
            },
            {
                id: 'voice',
                title: 'Voice transcription',
                status: voiceResult ? (voiceResult.valid ? 'Captured' : 'Retry suggested') : 'Optional',
                metric: formatPercent(voiceResult?.overall_score),
                details: voiceResult ? [
                    `Duration: ${voiceResult?.quality?.duration ? `${voiceResult.quality.duration.toFixed(1)}s` : 'Unknown'}`,
                    `Transcript: ${voiceResult?.transcription?.transcription ?? 'Unavailable'}`,
                ] : ['No voice recording provided (optional).'],
            },
            {
                id: 'confidence',
                title: 'Confidence & routing',
                status: overallResult ? 'Ready' : (validationState.textResult ? 'Pending final check' : 'Waiting'),
                metric: formatPercent(overallResult?.confidence?.overall_confidence),
                details: overallResult ? [
                    `Action: ${overallResult?.confidence?.action ?? 'review'}`,
                    `Routing: ${overallResult?.confidence?.routing ?? 'manual'}`,
                    `Image/Text alignment: ${formatPercent(crossModal?.image_text?.similarity)}`,
                    `Voice/Text alignment: ${formatPercent(crossModal?.voice_text?.similarity)}`,
                ] : ['Run the full validation once you have shared all the evidence.'],
            },
        ];
    }, [validationState]);

    return (
        <div className="app-shell">
            <div className="app-shell__container">

                {/* LEFT PANEL: Wide Chat Interface */}
                <section className="chat-pane">
                    <header className="chat-header">
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h1 className="chat-title">Lost & Found Assistant</h1>
                            <div className="step-indicator">
                                {stepSummary.map((step) => (
                                    <div
                                        key={step.id}
                                        className={[
                                            'step-indicator__dot',
                                            step.complete ? 'step-indicator__dot--complete' : '',
                                            !step.complete && step.active ? 'step-indicator__dot--active' : '',
                                        ].filter(Boolean).join(' ')}
                                    />
                                ))}
                            </div>
                        </div>
                    </header>

                    <ChatInterface messages={messages} isProcessing={isProcessing} />

                    {/* Sticky Chat Input Area with Media Triggers */}
                    {conversationState !== 'completed' && (
                        <div className="chat-input-area">
                            {(conversationState === 'awaiting_image' || conversationState === 'item_details' || conversationState === 'resolving_mismatch') && (
                                <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '0.75rem', paddingLeft: '0.5rem' }}>
                                    <button
                                        className="button button--quiet"
                                        style={{ padding: '0.5rem 1rem', fontSize: '0.85rem', background: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.3)' }}
                                        onClick={() => setIsCameraOpen(true)}
                                    >
                                        📷 Take Photo
                                    </button>
                                    <button
                                        className="button button--quiet"
                                        style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
                                        onClick={() => setIsUploadOpen(true)}
                                    >
                                        📁 Upload File
                                    </button>
                                </div>
                            )}

                            <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end' }}>
                                <div style={{ flex: 1 }}>
                                    <ChatInput
                                        onSend={handleUserInput}
                                        disabled={isProcessing}
                                        placeholder={conversationState === 'awaiting_voice' ? "Record voice..." : "Type your message..."}
                                    />
                                </div>
                                <VoiceRecorder
                                    onRecordingComplete={handleVoiceRecording}
                                    maxDuration={120}
                                    compact={true}
                                />
                            </div>
                        </div>
                    )}

                    {conversationState === 'completed' && (
                        <div style={{ padding: '1rem', textAlign: 'center' }}>
                            <button
                                type="button"
                                className="button"
                                style={{ background: 'var(--success)', color: 'white' }}
                                onClick={() => navigate('/results')}
                            >
                                View Final Report
                            </button>
                        </div>
                    )}
                </section>

                {/* RIGHT PANEL: Validation Sidebar (Narrow) */}
                <div className="workspace-pane">
                    <div className="summary-pane">
                        <h3 className="summary-title" style={{ fontSize: '0.9rem', marginBottom: '1.5rem', opacity: 0.7, borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>
                            Validation Context
                        </h3>

                        <PlausibilityCard result={validationState.spatialTemporalResult} />
                        <div style={{ height: '1rem' }} />
                        <DiscrepancyCard result={validationState.crossModalPreview?.xai_explanation} />
                        <div style={{ height: '1rem' }} />
                        <ValidationSummary
                            cards={summaryCards}
                            wsConnected={wsConnected}
                            progressLog={progressLog}
                            activeTaskId={activeTaskId}
                            overallResult={validationState.overallResult}
                        />

                        {(validationState.imageResult || validationState.textResult) && (
                            <div style={{ marginTop: '2rem', paddingTop: '1rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
                                <button
                                    onClick={() => setFeedbackModalOpen(true)}
                                    style={{ width: '100%', padding: '0.75rem', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', color: '#9ca3af', cursor: 'pointer', fontSize: '0.85rem' }}
                                >
                                    Report Issue
                                </button>
                            </div>
                        )}
                    </div>

                    {/* MEDIA STAGE: Dedicated Validation Input Area */}
                    <div className="media-stage">
                        {validationState.image ? (
                            <div style={{ position: 'relative', width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '1rem' }}>
                                <img
                                    src={URL.createObjectURL(validationState.image)}
                                    alt="Evidence"
                                    className="media-stage__image"
                                />
                                <div className="status-chip status-chip--connected">
                                    ✓ Image Analyzed
                                </div>
                            </div>
                        ) : conversationState === 'awaiting_image' ? (
                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                height: '200px',
                                border: '2px dashed var(--border-soft)',
                                borderRadius: '12px',
                                color: 'var(--text-secondary)'
                            }}>
                                <span style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>📷</span>
                                <p style={{ margin: 0, fontWeight: 500 }}>Awaiting Evidence</p>
                                <p style={{ margin: '0.25rem 0 0', fontSize: '0.8rem', opacity: 0.7 }}>
                                    Use the buttons in the chat to upload
                                </p>
                            </div>
                        ) : (conversationState === 'awaiting_voice' || conversationState === 'resolving_mismatch') ? (
                            <div style={{ width: '100%', maxWidth: '400px' }}>
                                <h3 style={{ textAlign: 'center', marginBottom: '1rem', color: 'var(--text-secondary)' }}>
                                    Voice Validation Active
                                </h3>
                                <VoiceRecorder
                                    onRecordingComplete={handleVoiceRecording}
                                    maxDuration={120}
                                />
                            </div>
                        ) : (
                            <div style={{
                                display: 'flex',
                                flexDirection: 'column',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '0.75rem',
                                opacity: 0.5,
                                height: '100%'
                            }}>
                                <span style={{ fontSize: '2.5rem' }}>🛡️</span>
                                <p style={{ margin: 0, color: 'var(--text-muted)' }}>Secure Verification Workspace</p>
                            </div>
                        )}
                    </div>
                </div>

                {/* MODALS */}
                <Modal
                    isOpen={isCameraOpen}
                    onClose={() => setIsCameraOpen(false)}
                    title="Evidence Capture"
                >
                    <CameraCapture
                        onCapture={handleImageCapture}
                        onCancel={() => setIsCameraOpen(false)}
                    />
                </Modal>

                <Modal
                    isOpen={isUploadOpen}
                    onClose={() => setIsUploadOpen(false)}
                    title="Upload Evidence"
                >
                    <FileUploadZone
                        onUpload={handleFileUploadWrapper}
                        accept="image/*"
                        maxSize={10 * 1024 * 1024}
                    />
                </Modal>

                <FeedbackModal
                    isOpen={feedbackModalOpen}
                    onClose={() => setFeedbackModalOpen(false)}
                    originalInput={validationState.textResult?.text || ''}
                    prediction={{
                        item_type: validationState.itemType,
                        color: validationState.colorHint,
                        brand: validationState.brandHint,
                    }}
                    onSubmit={async (corrections) => {
                        await submitFeedback(
                            validationState.textResult?.text || '',
                            {
                                item_type: validationState.itemType,
                                color: validationState.colorHint,
                                brand: validationState.brandHint,
                            },
                            corrections
                        );
                    }}
                />

            </div>
        </div>
    );
};
