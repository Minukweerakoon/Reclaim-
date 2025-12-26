import React, {
  useState,
  useEffect,
  useCallback,
  useMemo,
  useRef,
} from 'react';
import { ChatInterface } from './components/Chat/ChatWindow';
import { FileUploadZone } from './components/Uploads/Dropzone';
import { VoiceRecorder } from './components/Uploads/AudioRecorder';
import { CameraCapture } from './components/Uploads/CameraCapture';
import { ImageInputSelector } from './components/Uploads/ImageInputSelector';
import { useWebSocket } from './hooks/useWebSocket';
import { useValidation } from './hooks/useValidation';
import { ChatInput } from './components/Chat/ChatInput';
import {
  ValidationSummary,
  SummaryCard,
} from './components/Validation/ValidationSummary';

const COLOR_KEYWORDS = [
  'black',
  'white',
  'red',
  'blue',
  'green',
  'yellow',
  'brown',
  'gray',
  'grey',
  'purple',
  'orange',
  'pink',
  'silver',
  'gold',
] as const;

const BRAND_KEYWORDS = [
  'gucci',
  'coach',
  'prada',
  'lacoste',
  'nike',
  'adidas',
  'michael kors',
  'samsung',
  'apple',
  'sony'
] as const;

const ITEM_KEYWORDS = [
  'phone',
  'mobile',
  'iphone',
  'samsung',
  'smartphone',
  'cellphone',
  'bag',
  'backpack',
  'purse',
  'wallet',
  'keys',
  'keychain',
  'laptop',
  'tablet',
  'ipad',
  'watch',
  'airpods',
  'headphones',
  'umbrella',
  'camera',
] as const;

type ConversationState =
  | 'welcome'
  | 'item_details'
  | 'awaiting_image'
  | 'awaiting_voice'
  | 'resolving_mismatch'
  | 'completed';

interface Message {
  id: string;
  type: 'bot' | 'user';
  content: string;
  timestamp: Date;
  metadata?: Record<string, unknown>;
}

interface ValidationState {
  itemType?: string;
  colorHint?: string;
  brandHint?: string;
  initialMention?: string;
  text?: string;
  image?: File;
  voice?: Blob;
  textResult?: any;
  imageResult?: any;
  voiceResult?: any;
  crossModalPreview?: any;
  overallResult?: any;
}

interface ProgressEntry {
  label: string;
  value: string;
}

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

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationState, setConversationState] =
    useState<ConversationState>('welcome');
  const [validationState, setValidationState] = useState<ValidationState>({});
  const validationStateRef = useRef<ValidationState>({});
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [progressLog, setProgressLog] = useState<ProgressEntry[]>([]);
  const [activeTaskId, setActiveTaskId] = useState<string | null>(null);
  const [imageInputMode, setImageInputMode] = useState<'select' | 'camera' | 'file'>('select');


  const { sendMessage, wsConnected, lastMessage } = useWebSocket();
  const { validateComplete, validateImage, validateText, validateVoice, sendChatMessage } =
    useValidation();

  const addBotMessage = useCallback((content: string, metadata?: any) => {
    setMessages((prev) => [
      ...prev,
      {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        type: 'bot',
        content,
        timestamp: new Date(),
        metadata,
      },
    ]);
  }, []);

  const addUserMessage = useCallback((content: string) => {
    setMessages((prev) => [
      ...prev,
      {
        id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
        type: 'user',
        content,
        timestamp: new Date(),
      },
    ]);
  }, []);

  const updateValidationState = useCallback((updates: Partial<ValidationState>) => {
    validationStateRef.current = {
      ...validationStateRef.current,
      ...updates,
    };
    setValidationState(validationStateRef.current);
  }, []);

  const pushProgress = useCallback((label: string, value: string) => {
    setProgressLog((prev) => {
      const filtered = prev.filter((entry) => entry.label !== label);
      const next = [...filtered, { label, value }];
      return next.slice(-7);
    });
  }, []);

  useEffect(() => {
    addBotMessage(
      "Hi! I'm here to help you report your lost item using our multimodal validation system. What did you lose today?"
    );
  }, [addBotMessage]);

  useEffect(() => {
    if (!lastMessage) {
      return;
    }

    if (typeof lastMessage.progress === 'number') {
      const messageDetails =
        lastMessage.message && lastMessage.message.length > 0
          ? ` — ${lastMessage.message}`
          : '';
      pushProgress(
        'Realtime validation',
        `${Math.max(-1, lastMessage.progress)}%${messageDetails}`
      );
    }

    if (typeof lastMessage.task_id === 'string') {
      setActiveTaskId(lastMessage.task_id);
    }

    if (lastMessage.result) {
      updateValidationState({ overallResult: lastMessage.result });
      if (conversationState !== 'completed') {
        addBotMessage(
          'Realtime validation is complete. I have applied the final confidence score to your report.'
        );
        setConversationState('completed');
      }
    }
  }, [
    lastMessage,
    pushProgress,
    updateValidationState,
    addBotMessage,
    conversationState,
  ]);


  const detectColorFromText = useCallback((text: string): string | undefined => {
    const lower = text.toLowerCase();
    const match = COLOR_KEYWORDS.find((color) =>
      lower.includes(color.toLowerCase())
    );
    return match;
  }, []);

  const detectBrandFromText = useCallback((text: string): string | undefined => {
    const lower = text.toLowerCase();
    const match = BRAND_KEYWORDS.find((brand) =>
      lower.includes(brand.toLowerCase())
    );
    return match;
  }, []);

  const containsItemKeyword = useCallback((text: string): boolean => {
    const lower = text.toLowerCase();
    return ITEM_KEYWORDS.some((keyword) => lower.includes(keyword));
  }, []);

  const handleItemTypeInput = useCallback(
    async (itemType: string) => {
      const inferredColor = detectColorFromText(itemType);
      updateValidationState({
        itemType,
        colorHint: inferredColor ?? validationStateRef.current.colorHint,
      });
      pushProgress('Item category', itemType);
      addBotMessage(
        `Great! Let's capture the details of your ${itemType}. Please describe it including the color, brand, where you last saw it, and any unique features.`
      );
      setConversationState('item_details');
    },
    [updateValidationState, addBotMessage, pushProgress, detectColorFromText]
  );

  const handleDescriptionInput = useCallback(
    async (description: string) => {
      // Context Awareness: Append new description to existing text
      const currentText = validationStateRef.current.text || '';
      const separator = currentText ? ' ' : '';
      const fullText = currentText + separator + description;

      updateValidationState({ text: fullText });
      setIsProcessing(true);
      pushProgress('Description analysis', 'Running');

      try {
        // Validate the accumulated text
        const textResult = await validateText(fullText, {
          itemTypeHint: validationStateRef.current.itemType,
          colorHint: validationStateRef.current.colorHint,
        });
        updateValidationState({ textResult });

        if (textResult?.valid) {
          const mentions =
            textResult?.entities?.item_mentions?.length > 0
              ? textResult.entities.item_mentions.join(', ')
              : 'the item';

          // Check for clarification questions (plausibility check)
          if (textResult?.clarification_questions && textResult.clarification_questions.length > 0) {
            addBotMessage(textResult.clarification_questions.join(' '));
            // Don't advance state yet if clarification is needed, or maybe we do?
            // For now, let's keep it in the same state or maybe 'resolving_mismatch' if we had that logic.
            // But to keep it simple and allow flow to continue (since it IS valid), we'll just show the warning
            // and still ask for the image.
            addBotMessage(
              `I noted ${mentions}, but please clarify the above if needed. If you have a photo of the item, upload it so I can verify the visual details.`
            );
          } else {
            addBotMessage(
              `Excellent description! I noted ${mentions}. If you have a photo of the item, upload it so I can verify the visual details.`
            );
          }

          pushProgress(
            'Description analysis',
            formatPercent(textResult.overall_score)
          );
          setConversationState('awaiting_image');
        } else {
          const completenessFeedback =
            textResult?.completeness?.feedback ??
            'This description is too vague to evaluate.';
          if (textResult?.completeness?.is_vague) {
            addBotMessage(completenessFeedback);
          } else {
            const missingDetails = listOrFallback(
              textResult?.completeness?.missing_info,
              'more context'
            );
            addBotMessage(
              `Thanks! Could you expand the description by adding: ${missingDetails}? This helps match your report faster.`
            );
          }
          pushProgress('Description analysis', 'Needs more detail');
        }
      } catch (error) {
        addBotMessage(
          'I could not analyse that description. Please try again or simplify the text.'
        );
        pushProgress('Description analysis', 'Failed');
      } finally {
        setIsProcessing(false);
      }
    },
    [validateText, updateValidationState, addBotMessage, pushProgress]
  );

  const handleImageUpload = useCallback(
    async (file: File) => {
      updateValidationState({ image: file });
      setIsProcessing(true);
      addBotMessage('Analyzing your photo now...');
      pushProgress('Image analysis', 'Processing');

      try {
        // Build complete description including item type for better detection
        const itemType = validationStateRef.current.itemType || '';
        const textDescription = validationStateRef.current.text || '';
        const fullDescription = itemType
          ? `${itemType} ${textDescription}`.trim()
          : textDescription;

        console.log('[DEBUG] Sending to validateImage - Full description:', fullDescription);

        const imageResult = await validateImage(
          file,
          fullDescription  // Include item type (e.g., "iPhone 15") in description
        );
        updateValidationState({ imageResult });
        pushProgress(
          'Image analysis',
          formatPercent(imageResult?.overall_score)
        );

        if (imageResult?.valid) {
          const detected =
            imageResult?.objects?.detections?.[0]?.class || 'your item';

          if (validationStateRef.current.text) {
            const combined = await validateComplete({
              image: file,
              text: validationStateRef.current.text,
            });

            updateValidationState({
              crossModalPreview: combined.cross_modal,
            });

            const imageText = combined?.cross_modal?.image_text;

            if (imageText?.valid) {
              addBotMessage(
                `Nice! The photo clearly shows ${detected} and matches your description. A quick voice note can add even more context if you have time.`
              );
              setConversationState('awaiting_voice');
            } else {
              const similarity = formatPercent(imageText?.similarity);
              // Use backend feedback if available for explainable AI
              const feedbackMsg = imageText?.feedback || `The photo highlights ${detected}, but it does not quite align with the written description (similarity ${similarity}).`;

              addBotMessage(
                `${feedbackMsg} Could you clarify or update the description?`
              );
              setConversationState('resolving_mismatch');
            }
          } else {
            addBotMessage(
              `Great shot! I can see ${detected}. If you have not already, please describe the item so I can link the visual details.`
            );
          }
        } else {
          const issues: string[] = [];
          if (!imageResult?.sharpness?.valid) {
            issues.push('the image looks blurry');
          }
          if (!imageResult?.objects?.valid) {
            issues.push('the main item is difficult to recognise');
          }
          addBotMessage(
            `I could not confirm the photo because ${issues.join(
              ' and '
            )}. Try retaking the photo with better lighting and focus.`
          );
        }
      } catch (error) {
        addBotMessage(
          'Something went wrong while processing that photo. Please try again with a different image.'
        );
        pushProgress('Image analysis', 'Failed');
      } finally {
        setIsProcessing(false);
      }
    },
    [
      validateImage,
      validateComplete,
      addBotMessage,
      updateValidationState,
      pushProgress,
    ]
  );

  const handleImageCapture = useCallback(
    async (blob: Blob, dataUrl: string) => {
      // Convert blob to File
      const file = new File([blob], 'camera_capture.jpg', { type: 'image/jpeg' });

      // Use existing handleImageUpload logic
      await handleImageUpload(file);

      // Reset mode to select
      setImageInputMode('select');
    },
    [handleImageUpload]
  );


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
          const transcription =
            voiceResult?.transcription?.transcription || 'your description';
          addBotMessage(
            `I heard: "${transcription}". Let me confirm everything lines up.`
          );
          pushProgress(
            'Voice analysis',
            formatPercent(voiceResult?.overall_score)
          );

          if (validationStateRef.current.text) {
            const combined = await validateComplete({
              voice: audioBlob,
              text: validationStateRef.current.text,
            });

            const voiceText = combined?.cross_modal?.voice_text;
            updateValidationState({
              crossModalPreview: {
                ...(validationStateRef.current.crossModalPreview ?? {}),
                voice_text: voiceText,
              },
            });

            if (voiceText?.valid) {
              addBotMessage(
                'Great! Your voice message adds consistent details. I will now generate the final confidence score.'
              );
              await finalizeSubmission();
            } else {
              addBotMessage(
                'I noticed some differences between what you said and what you wrote. Which version should I use?'
              );
            }
          } else {
            addBotMessage(
              'Thanks! Once you add a text description I will align the two.'
            );
          }
        } else {
          const feedback =
            voiceResult?.quality?.feedback ||
            'the transcription quality was not sufficient';
          addBotMessage(
            `I could not understand the recording because ${feedback}. Could you try again in a quieter space?`
          );
          pushProgress('Voice analysis', 'Needs re-recording');
        }
      } catch (error) {
        addBotMessage(
          'I had trouble processing that recording. Please try again in a moment.'
        );
        pushProgress('Voice analysis', 'Failed');
      } finally {
        setIsProcessing(false);
      }
    },
    [
      validateVoice,
      validateComplete,
      addBotMessage,
      updateValidationState,
      pushProgress,
    ]
  );

  const finalizeSubmission = useCallback(async () => {
    if (!validationStateRef.current.text) {
      addBotMessage('Please provide a description before finalising the report.');
      return;
    }

    setIsProcessing(true);
    pushProgress('Full validation', 'Running');

    try {
      const payload: {
        text?: string;
        image?: File;
        voice?: Blob;
      } = {
        text: validationStateRef.current.text,
      };

      if (validationStateRef.current.image) {
        payload.image = validationStateRef.current.image;
      }
      if (validationStateRef.current.voice) {
        payload.voice = validationStateRef.current.voice;
      }

      if (wsConnected) {
        sendMessage({
          type: 'validate',
          text: validationStateRef.current.text,
          image_path: validationStateRef.current.imageResult?.image_path,
          audio_path: validationStateRef.current.voiceResult?.audio_path,
          language: 'en',
        });
      }

      const completeResult = await validateComplete(payload);
      updateValidationState({ overallResult: completeResult });

      const confidenceScore =
        completeResult?.confidence?.overall_confidence ?? null;
      const action = completeResult?.confidence?.action ?? 'review';

      addBotMessage(
        `All set! Your report scored ${formatPercent(
          confidenceScore
        )} confidence and will be ${action.replace('_', ' ')}. We will notify you as soon as we find a match.`
      );

      pushProgress('Full validation', formatPercent(confidenceScore));
      setConversationState('completed');
    } catch (error) {
      addBotMessage(
        'I was unable to finalise the report. Please try again once more.'
      );
      pushProgress('Full validation', 'Failed');
    } finally {
      setIsProcessing(false);
    }
  }, [
    validateComplete,
    wsConnected,
    sendMessage,
    updateValidationState,
    addBotMessage,
    pushProgress,
  ]);

  const handleUserInput = useCallback(
    async (input: string) => {
      const trimmed = input.trim();
      if (!trimmed || isProcessing) {
        return;
      }

      addUserMessage(trimmed);
      setIsProcessing(true);
      pushProgress('AI Analysis', 'Thinking...');

      try {
        // Prepare conversation history for context
        const history = messages.map(msg => ({
          role: msg.type === 'user' ? 'user' : 'model',
          content: msg.content
        }));

        console.log('[DEBUG] Calling sendChatMessage with:', { message: trimmed, historyLength: history.length });

        // Call Gemini-powered chat API
        const response = await sendChatMessage(trimmed, history);

        console.log('[DEBUG] Received response from sendChatMessage:', response);

        // 1. Show Bot Response
        if (response.bot_response) {
          console.log('[DEBUG] Adding bot message:', response.bot_response);
          addBotMessage(response.bot_response);
        } else {
          console.warn('[DEBUG] No response.bot_response field in:', response);
        }

        // 2. Update Extracted Info
        if (response.extracted_info) {
          const info = response.extracted_info;
          const updates: Partial<ValidationState> = {};

          if (info.item_type) updates.itemType = info.item_type;
          if (info.color) updates.colorHint = info.color;
          if (info.brand) updates.brandHint = info.brand;

          // Append location/time to text description if present
          let newText = validationStateRef.current.text || '';
          if (info.location && !newText.includes(info.location)) {
            newText += ` at ${info.location}`;
          }
          if (info.time && !newText.includes(info.time)) {
            newText += ` around ${info.time}`;
          }
          if (newText !== validationStateRef.current.text) {
            updates.text = newText;
          }

          if (Object.keys(updates).length > 0) {
            updateValidationState(updates);
            pushProgress('Extracted Details', 'Updated');
          }
        }

        // 3. Handle Next Actions
        if (response.next_action === 'ask_for_image') {
          setConversationState('awaiting_image');
        } else if (response.next_action === 'validate') {
          // Trigger validation if we have enough info
          if (validationStateRef.current.text) {
            setIsProcessing(true);
            pushProgress('Description analysis', 'Running');
            try {
              const textResult = await validateText(validationStateRef.current.text, {
                itemTypeHint: validationStateRef.current.itemType,
                colorHint: validationStateRef.current.colorHint,
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

        // 4. Handle Intention (Lost vs Found)
        if (response.intention && response.intention !== 'unknown') {
          // Could update UI theme or context based on this
          console.log("Detected intention:", response.intention);
        }

      } catch (error) {
        console.error("Chat error:", error);
        addBotMessage("I'm having trouble connecting to my brain right now. Please try again.");
        pushProgress('AI Analysis', 'Failed');
      } finally {
        setIsProcessing(false);
      }
    },
    [
      addUserMessage,
      messages,
      isProcessing,
      sendChatMessage,
      addBotMessage,
      updateValidationState,
      pushProgress,
      handleDescriptionInput
    ]
  );

  const stepSummary = useMemo(() => {
    const steps = [
      {
        id: 'describe',
        complete: Boolean(validationState.textResult),
      },
      {
        id: 'image',
        complete: Boolean(validationState.imageResult),
      },
      {
        id: 'voice',
        complete: Boolean(validationState.voiceResult),
      },
      {
        id: 'final',
        complete: Boolean(validationState.overallResult),
      },
    ];

    const firstIncomplete = steps.findIndex((step) => !step.complete);
    return steps.map((step, index) => ({
      ...step,
      active: firstIncomplete === index,
    }));
  }, [validationState]);

  const summaryCards = useMemo<SummaryCard[]>(() => {
    const textResult = validationState.textResult;
    const imageResult = validationState.imageResult;
    const voiceResult = validationState.voiceResult;
    const overall = validationState.overallResult;
    const crossModal =
      overall?.cross_modal ?? validationState.crossModalPreview ?? {};

    const itemMentions = pickMentions(
      textResult?.entities?.item_mentions,
      textResult?.completeness?.entities?.item_type
    );
    const colorMentions = pickMentions(
      textResult?.entities?.color_mentions,
      textResult?.completeness?.entities?.color
    );

    const brandMentions = pickMentions(
      textResult?.entities?.brand_mentions,
      textResult?.completeness?.entities?.brand
    );

    return [
      {
        id: 'text',
        title: 'Description quality',
        status: textResult
          ? textResult.valid
            ? 'Complete'
            : 'Needs revision'
          : 'Waiting',
        metric: formatPercent(textResult?.overall_score),
        details: textResult
          ? [
            `Completeness: ${formatPercent(
              textResult?.completeness?.score ?? textResult?.overall_score
            )}`,
            `Mentioned items: ${listOrFallback(itemMentions)}`,
            `Detected colors: ${listOrFallback(colorMentions)}`,
            `Brand cues: ${listOrFallback(brandMentions)}`,
            `Missing details: ${listOrFallback(
              textResult?.completeness?.missing_info
            )}`,
          ]
          : ['Add a descriptive summary of your item to begin.'],
      },
      {
        id: 'image',
        title: 'Image insights',
        status: imageResult
          ? imageResult.valid
            ? 'Clear'
            : 'Needs retake'
          : 'Waiting',
        metric: formatPercent(imageResult?.overall_score),
        details: imageResult
          ? [
            `Sharpness: ${formatSharpnessScore(imageResult?.sharpness)}`,
            imageResult?.objects?.detections?.length
              ? `Detected: ${imageResult.objects.detections[0].class} (${Math.round(
                imageResult.objects.detections[0].confidence * 100
              )}%)`
              : 'No objects detected',
          ]
          : ['Upload a recent photo to boost match accuracy.'],
        actionHint: imageResult && !imageResult.valid
          ? 'Try retaking the photo: keep the wallet centered and use brighter lighting.'
          : undefined,
      },
      {
        id: 'voice',
        title: 'Voice transcription',
        status: voiceResult
          ? voiceResult.valid
            ? 'Captured'
            : 'Retry suggested'
          : 'Optional',
        metric: formatPercent(voiceResult?.overall_score),
        details: voiceResult
          ? [
            `Duration: ${voiceResult?.quality?.duration
              ? `${voiceResult.quality.duration.toFixed(1)}s`
              : 'Unknown'
            }`,
            `Transcript: ${voiceResult?.transcription?.transcription ?? 'Unavailable'
            }`,
          ]
          : ['No voice recording provided (optional).'],
      },
      {
        id: 'confidence',
        title: 'Confidence & routing',
        status: overall
          ? 'Ready'
          : validationState.textResult
            ? 'Pending final check'
            : 'Waiting',
        metric: formatPercent(overall?.confidence?.overall_confidence),
        details: overall
          ? [
            `Action: ${overall?.confidence?.action ?? 'review'}`,
            `Routing: ${overall?.confidence?.routing ?? 'manual'}`,
            `Image/Text alignment: ${formatPercent(
              crossModal?.image_text?.similarity
            )}`,
            `Voice/Text alignment: ${formatPercent(
              crossModal?.voice_text?.similarity
            )}`,
          ]
          : ['Run the full validation once you have shared all the evidence.'],
      },
    ];
  }, [validationState]);

  return (
    <div className="app-shell">
      <div className="app-shell__container">
        <section className="chat-pane">
          <header className="chat-header">
            <h1 className="chat-title">Lost &amp; Found Smart Assistant</h1>
            <p className="chat-subtitle">
              Powered by multimodal validation technology
            </p>
            <div className="step-indicator">
              {stepSummary.map((step) => (
                <div
                  key={step.id}
                  className={[
                    'step-indicator__dot',
                    step.complete ? 'step-indicator__dot--complete' : '',
                    !step.complete && step.active
                      ? 'step-indicator__dot--active'
                      : '',
                  ]
                    .filter(Boolean)
                    .join(' ')}
                />
              ))}
            </div>
          </header>

          <ChatInterface messages={messages} isProcessing={isProcessing} />

          {conversationState === 'awaiting_image' && (
            <>
              {imageInputMode === 'select' && (
                <ImageInputSelector
                  onCameraSelect={() => setImageInputMode('camera')}
                  onFileSelect={() => setImageInputMode('file')}
                />
              )}

              {imageInputMode === 'camera' && (
                <CameraCapture
                  onCapture={handleImageCapture}
                  onCancel={() => setImageInputMode('select')}
                />
              )}

              {imageInputMode === 'file' && (
                <FileUploadZone
                  onUpload={handleImageUpload}
                  accept="image/*"
                  maxSize={10 * 1024 * 1024}
                />
              )}
            </>
          )}

          {(conversationState === 'awaiting_voice' || conversationState === 'resolving_mismatch') && (
            <VoiceRecorder
              onRecordingComplete={handleVoiceRecording}
              maxDuration={120}
            />
          )}

          {conversationState === 'completed' && (
            <button
              type="button"
              className="button button--quiet"
              onClick={() =>
                addBotMessage(
                  'Report saved. If you need to resubmit, please refresh to start a new session.'
                )
              }
            >
              Report saved
            </button>
          )}

          {!['awaiting_image', 'awaiting_voice', 'resolving_mismatch', 'completed'].includes(
            conversationState
          ) && (
              <div className="chat-input">
                <ChatInput
                  onSend={handleUserInput}
                  disabled={isProcessing}
                  placeholder="Share the details here..."
                />
              </div>
            )}
        </section>

        <ValidationSummary
          cards={summaryCards}
          wsConnected={wsConnected}
          progressLog={progressLog}
          activeTaskId={activeTaskId}
          overallResult={validationState.overallResult}
        />
      </div>
    </div>
  );
};

export default App;

