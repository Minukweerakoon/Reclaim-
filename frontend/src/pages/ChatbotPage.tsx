import { useEffect, useMemo, useRef, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { chatApi } from '../api/chat';
import { validationApi } from '../api/validation';
import { formatErrorMessage } from '../components/ErrorMessage';
import type { ChatMessage } from '../types/api';
import { useValidationStore } from '../store/useValidationStore';
import { useChatStore } from '../store/useChatStore';
import { useAuth } from '../contexts/AuthContext';
import { MatchResultCard } from '../reclaim/components/MatchResultCard';

const summarizeExtractedInfo = (info: Record<string, any>, intentValue: string) => {
    const parts: string[] = [];
    if (intentValue) parts.push(`intent: ${intentValue}`);
    Object.entries(info || {}).forEach(([key, value]) => {
        if (value === null || value === undefined || value === '') return;
        parts.push(`${key.replace(/_/g, ' ')}: ${String(value)}`);
    });
    return parts.join(', ');
};

const buildVisualSeed = (info: Record<string, any>) => {
    const values = [info?.color, info?.brand, info?.item_type].filter(Boolean);
    return values.join(' ');
};

const buildValidationNarrative = (info: Record<string, any>, intentValue: string) => {
    const item = info?.item_type || 'item';
    const color = info?.color ? `${info.color} ` : '';
    const brand = info?.brand ? `${info.brand} ` : '';
    const location = info?.location || 'unknown location';
    const time = info?.time || 'unknown time';

    if (intentValue === 'lost') {
        return `I lost a ${color}${brand}${item}. Last seen at ${location} around ${time}.`;
    }

    return `I found a ${color}${brand}${item} at ${location} around ${time}.`;
};

const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

const detectExplicitIntent = (message: string): 'lost' | 'found' | null => {
    const text = message.toLowerCase();
    const foundMatch = /\b(i\s+)?found\b/.test(text);
    const lostMatch = /\b(i\s+)?lost\b/.test(text);

    if (foundMatch && !lostMatch) return 'found';
    if (lostMatch && !foundMatch) return 'lost';
    return null;
};

function ChatbotPage() {
    const [searchParams] = useSearchParams();
    const initialIntent = searchParams.get('intent') || '';
    const { user, phoneNumber } = useAuth();

    const [input, setInput] = useState('');
    const [isProcessingReport, setIsProcessingReport] = useState(false);
    const [selectedMatch, setSelectedMatch] = useState<any | null>(null);
    const {
        messages, setMessages,
        isTyping, setIsTyping,
        extractedInfo, setExtractedInfo,
        intent, setIntent,
        summaryConfirmed, setSummaryConfirmed,
        pendingImage, imagePreview, setPendingImage,
        resetChat
    } = useChatStore();

    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = () => setPendingImage(file, reader.result as string);
            reader.readAsDataURL(file);
        }
    };

    const removeImage = () => {
        setPendingImage(null, null);
        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    useEffect(() => {
        if (!initialIntent) return;

        // Always trust explicit URL intent. If it differs from the store,
        // start a fresh chat session to avoid stale "found/lost" carry-over.
        if (initialIntent !== intent) {
            resetChat();
            setIntent(initialIntent);
        }
    }, [initialIntent, intent, resetChat, setIntent]);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const confirmInFlightRef = useRef(false);
    const {
        currentResult,
        setResult,
        setIntent: setStoreIntent,
        setPendingInputs,
        setPendingMedia,
        setPendingExtractedInfo,
        reset: resetValidationState,
    } = useValidationStore();

    // Prefer Vite proxy for consistency with dev server/backends.
    const processEndpoint = import.meta.env.VITE_AI_PROCESS_URL || '/items/process';

    const runLostRetrieval = async (payload: {
        item_id: string;
        image_url: string;
        user_category?: string;
    }) => {
        if (!payload.item_id || !payload.image_url) {
            throw new Error('Missing retrieval metadata (item_id/image_url)');
        }

        let processData: any = null;
        let lastError: unknown = null;

        for (let attempt = 1; attempt <= 2; attempt += 1) {
            const controller = new AbortController();
            const timeout = window.setTimeout(() => controller.abort(), 20000);

            try {
                const processResponse = await fetch(processEndpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        item_id: payload.item_id,
                        item_type: 'lost',
                        image_url: payload.image_url,
                        user_category: payload.user_category || undefined,
                        k: 5,
                    }),
                    signal: controller.signal,
                });

                if (!processResponse.ok) {
                    const errorBody = await processResponse.text();
                    throw new Error(`AI search failed (${processResponse.status}): ${errorBody || 'no error body'}`);
                }

                processData = await processResponse.json();
                window.clearTimeout(timeout);
                lastError = null;
                break;
            } catch (e) {
                window.clearTimeout(timeout);
                lastError = e;
                if (attempt < 2) {
                    await delay(1000);
                }
            }
        }

        if (!processData) {
            throw lastError instanceof Error ? lastError : new Error('AI search temporarily unavailable');
        }

        return processData;
    };

    const handleRetryMatch = async (messageId: string, retryMatch: { item_id: string; image_url: string; user_category?: string }) => {
        setMessages((prev) => prev.map((msg) => {
            if (msg.id !== messageId) return msg;
            return {
                ...msg,
                loading: true,
                content: 'Retrying matching for your lost item...',
            };
        }));

        try {
            const processData = await runLostRetrieval(retryMatch);
            const results = Array.isArray(processData?.results) ? processData.results : [];

            setMessages((prev) => prev.map((msg) => {
                if (msg.id !== messageId) return msg;
                if (!results.length) {
                    return {
                        ...msg,
                        loading: false,
                        content: 'No matching items were found yet, but we will notify you if something similar appears.',
                        matchResults: [],
                    };
                }
                return {
                    ...msg,
                    loading: false,
                    content: 'We found possible matches for your lost item:',
                    matchResults: results,
                    retryMatch: undefined,
                };
            }));
        } catch (err) {
            const errorText = formatErrorMessage(err);
            console.error('[ChatbotPage] Retry retrieval failed:', errorText);
            setMessages((prev) => prev.map((msg) => {
                if (msg.id !== messageId) return msg;
                return {
                    ...msg,
                    loading: false,
                    content: 'Matching is still delayed. Please retry in a few seconds.',
                    retryMatch,
                };
            }));
        }
    };

    useEffect(() => {
        if (messages.length === 0) {
            const greeting = intent === 'found'
                ? "You found something. Tell me what it is and where you picked it up."
                : intent === 'lost'
                    ? "I'm here to help. Describe what you lost and where you last saw it."
                    : "Describe the lost or found item, and I'll guide you through the report.";

            setMessages([{
                role: 'bot',
                content: greeting,
                timestamp: new Date()
            }]);
        }
    }, [intent, messages.length, setMessages]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const summaryText = useMemo(() => summarizeExtractedInfo(extractedInfo, intent), [extractedInfo, intent]);

    const handleSend = async () => {
        if (!input.trim() || isTyping) return;

        const trimmedInput = input.trim();
        const explicitIntent = detectExplicitIntent(trimmedInput);
        const hasCompletedFlow = summaryConfirmed || Boolean(currentResult);
        const shouldRestartFlow = Boolean(
            explicitIntent && (
                explicitIntent !== intent ||
                hasCompletedFlow
            )
        );

        if (explicitIntent && shouldRestartFlow) {
            resetChat();
            resetValidationState();
            confirmInFlightRef.current = false;
            setIsProcessingReport(false);
            setIntent(explicitIntent);

            const restartMessage = explicitIntent === 'found'
                ? "Starting a fresh found-item report. Tell me what you found and where you picked it up."
                : "Starting a fresh lost-item report. Tell me what you lost and where you last saw it.";

            setMessages([
                {
                    role: 'user',
                    content: trimmedInput,
                    timestamp: new Date(),
                },
                {
                    role: 'bot',
                    content: restartMessage,
                    timestamp: new Date(),
                },
            ]);
            setInput('');
            return;
        }

        const userMessage: ChatMessage = {
            role: 'user',
            content: trimmedInput,
            timestamp: new Date()
        };
        setMessages((prev) => [...prev, userMessage]);
        setInput('');
        setIsTyping(true);

        const history = messages;

        try {
            const response = await chatApi.sendMessage({
                message: userMessage.content,
                history,
                previous_prediction: currentResult || undefined,
                extracted_info: extractedInfo,
            });

            // Update extracted info first
            let updatedExtractedInfo = { ...extractedInfo };
            if (response.extracted_info) {
                Object.entries(response.extracted_info).forEach(([key, value]) => {
                    // Only overwrite if the new value is actually provided (non-empty string)
                    if (value !== null && value !== undefined && value !== '') {
                        updatedExtractedInfo[key] = value;
                    }
                });
            }
            setExtractedInfo(updatedExtractedInfo);

            // Check if user explicitly said they don't know (expanded patterns)
            const userText = userMessage.content.toLowerCase().trim();
            const dontKnowPatterns = /^(no|nope|nah|not?|don'?t know|not sure|can'?t remember|no idea|don'?t have|unknown|forgot|unsure|not found|nothing|none|i don'?t|don'?t remember)$/i;
            const userDoesntKnow = dontKnowPatterns.test(userText) || /\b(don'?t know|not sure|can'?t remember|no idea|don'?t have|unknown|forgot|unsure|not found|nothing)\b/i.test(userText);

            // Generate follow-up question if fields are missing (but skip if user doesn't know)
            let followUpQuestion = '';
            if (response.intention) {
                const requiredFields = [
                    { key: 'item_type', label: 'What kind of item is this?', critical: true },
                    { key: 'location', label: 'Can you mention the location?', critical: true },
                    { key: 'time', label: 'Can you tell me approximately what time this was?', critical: false },
                    { key: 'color', label: 'What color is the item?', critical: false },
                    { key: 'brand', label: 'Do you know the brand or make?', critical: false },
                ];

                // Check critical fields (item_type and location must be present)
                const criticalFieldsFilled = requiredFields
                    .filter(f => f.critical)
                    .every(f => updatedExtractedInfo[f.key] && updatedExtractedInfo[f.key].trim() !== '');

                if (!userDoesntKnow) {
                    // Find first missing field
                    for (const field of requiredFields) {
                        if (!updatedExtractedInfo[field.key] || updatedExtractedInfo[field.key].trim() === '') {
                            followUpQuestion = ` ${field.label}`;
                            break;
                        }
                    }
                } else {
                    // User doesn't know current field, skip to next missing one
                    let skippedOne = false;
                    for (const field of requiredFields) {
                        if (!updatedExtractedInfo[field.key] || updatedExtractedInfo[field.key].trim() === '') {
                            if (skippedOne) {
                                // Ask for the next field after the skipped one
                                followUpQuestion = ` ${field.label}`;
                                break;
                            }
                            skippedOne = true; // Skip current field
                        }
                    }
                }

                // If all critical fields are filled and no more questions, prompt to confirm
                if (!followUpQuestion && criticalFieldsFilled && pendingImage) {
                    followUpQuestion = ' Now you can confirm and proceed with the report!';
                }
            }

            const botMessage: ChatMessage = {
                role: 'bot',
                content: response.bot_response + followUpQuestion,
                timestamp: new Date()
            };
            setMessages((prev) => [...prev, botMessage]);

            if (response.intention) {
                setIntent(response.intention);
            }
            setSummaryConfirmed(false);
        } catch (error) {
            const errorMsg = formatErrorMessage(error);
            const errorBotMsg: ChatMessage = {
                role: 'bot',
                content: `Sorry, I hit a snag: ${errorMsg}`,
                timestamp: new Date()
            };
            setMessages((prev) => [...prev, errorBotMsg]);
        } finally {
            setIsTyping(false);
        }
    };

    const handleKeyDown = (event: React.KeyboardEvent) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            handleSend();
        }
    };

    const handleConfirm = async () => {
        if (!summaryText || !pendingImage || !intent || (intent !== 'lost' && intent !== 'found')) {
            return;
        }
        if (confirmInFlightRef.current) {
            return;
        }

        confirmInFlightRef.current = true;
        setIsProcessingReport(true);
        setSummaryConfirmed(true);
        setStoreIntent(intent);

        const validationText = buildValidationNarrative(extractedInfo, intent);
        const visualSeed = buildVisualSeed(extractedInfo);
        setPendingInputs(validationText, visualSeed);
        setPendingExtractedInfo(extractedInfo as Record<string, string>);
        setPendingMedia(pendingImage, null);

        const loadingMessageId = `processing-${Date.now()}`;
        const processingText = intent === 'lost'
            ? 'Validating and searching for possible matches...'
            : 'Validating and saving your found item...';
        setMessages((prev) => [
            ...prev,
            {
                id: loadingMessageId,
                role: 'bot',
                content: processingText,
                loading: true,
                timestamp: new Date(),
            },
        ]);

        try {
            const validationResult = await validationApi.validateComplete({
                text: validationText || undefined,
                visualText: visualSeed || undefined,
                imageFile: pendingImage,
                language: 'en',
                intent,
                userId: user?.id,
                userEmail: user?.email ?? undefined,
                userPhone: phoneNumber || undefined,
            });

            // Keep ValidationHub in sync with chat-side processing.
            setResult(validationResult);

            const itemId = validationResult.supabase_id;
            const imageUrl = validationResult.image_url;
            const userCategory = extractedInfo?.item_type || '';

            if (!itemId || !imageUrl) {
                setMessages((prev) => prev.map((msg) => {
                    if (msg.id !== loadingMessageId) return msg;
                    return {
                        ...msg,
                        loading: false,
                        content: 'Validation completed, but search metadata is incomplete. Please try again.',
                    };
                }));
                return;
            }

            // Bidirectional matching: BOTH found and lost items get retrieval results
            const searchingFor = intent === 'found' ? 'lost' : 'found';
            setMessages((prev) => prev.map((msg) => {
                if (msg.id !== loadingMessageId) return msg;
                return {
                    ...msg,
                    loading: true,
                    content: `Validation complete. Searching for possible ${searchingFor} items...`,
                };
            }));

            const retrievalPayload = {
                item_id: itemId,
                image_url: imageUrl,
                user_category: userCategory || undefined,
            };

            // Run retrieval asynchronously so the UI does not appear frozen.
            void (async () => {
                let processData: any = null;
                try {
                    processData = await runLostRetrieval(retrievalPayload);
                } catch (err) {
                    const errorText = formatErrorMessage(err);
                    console.error('[ChatbotPage] Retrieval flow failed:', errorText);
                    setMessages((prev) => prev.map((msg) => {
                        if (msg.id !== loadingMessageId) return msg;
                        return {
                            ...msg,
                            loading: false,
                            content: 'Validation completed. Matching is taking longer than expected, please check again shortly.',
                            retryMatch: retrievalPayload,
                        };
                    }));
                    return;
                }

                const results = Array.isArray(processData?.results) ? processData.results : [];

                setMessages((prev) => prev.map((msg) => {
                    if (msg.id !== loadingMessageId) return msg;
                    if (!results.length) {
                        const noMatchMessage = intent === 'found'
                            ? 'Your found item has been indexed. No lost reports match yet, but we will notify you if someone reports it as lost.'
                            : 'No matching items were found yet, but we will notify you if something similar appears.';
                        return {
                            ...msg,
                            loading: false,
                            content: noMatchMessage,
                            matchResults: [],
                        };
                    }
                    const matchMessage = intent === 'found'
                        ? 'We found people who reported similar lost items:'
                        : 'We found possible matches for your lost item:';
                    return {
                        ...msg,
                        loading: false,
                        content: matchMessage,
                        matchResults: results,
                        retryMatch: undefined,
                    };
                }));
            })();
        } catch (err) {
            const errorText = formatErrorMessage(err);
            console.error('[ChatbotPage] Retrieval flow failed:', errorText);
            setSummaryConfirmed(false);
            setMessages((prev) => prev.map((msg) => {
                if (msg.id !== loadingMessageId) return msg;
                return {
                    ...msg,
                    loading: false,
                    content: 'Validation completed, but matching is temporarily delayed. Please try again in a moment.',
                };
            }));
        } finally {
            confirmInFlightRef.current = false;
            setIsProcessingReport(false);
        }
    };

    return (
        <div className="animate-fade-in">
            {/* Page Title */}
            <div className="mb-8 text-center">
                <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-xs font-medium mb-4">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-indigo-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-indigo-500"></span>
                    </span>
                    Conversation Phase
                </div>
                <h1 className="text-4xl md:text-5xl font-bold mb-3 tracking-tight bg-clip-text text-transparent bg-gradient-to-b from-white to-slate-400">
                    Describe Your Item
                </h1>
                <p className="text-slate-400 max-w-2xl mx-auto">
                    Tell me about the {intent === 'lost' ? 'lost' : intent === 'found' ? 'found' : ''} item. I'll guide you through gathering the details.
                </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6">
                {/* ── Chat Panel ── */}
                <section className="glass-panel rounded-2xl p-6 flex flex-col">
                    {/* Header */}
                    <div className="flex items-center justify-between mb-5 pb-4 border-b border-white/10">
                        <div>
                            <div className="text-xs uppercase tracking-wider text-indigo-400 font-semibold">
                                Chat Interface
                            </div>
                            <div className="text-xs text-slate-400 mt-1">Gemini-guided intake and clarification</div>
                        </div>
                        <div className="text-[10px] uppercase tracking-widest text-slate-300 px-3 py-1.5 rounded-lg bg-white/5 border border-white/10">
                            Intent: {intent || 'pending'}
                        </div>
                    </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto space-y-4 pr-1">
                    {messages.map((message, index) => (
                        <div key={message.id || index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
                            <div
                                className={`${message.role === 'user' ? 'max-w-[72%]' : Array.isArray(message.matchResults) && message.matchResults.length > 0 ? 'max-w-[88%]' : 'max-w-[72%]'} rounded-2xl px-4 py-3 ${message.role === 'user'
                                    ? 'text-white rounded-br-none'
                                    : 'text-slate-100 rounded-bl-none'
                                    }`}
                                style={message.role === 'user'
                                    ? { background: 'var(--accent-primary)', boxShadow: '0 4px 16px rgba(99,102,241,0.25)' }
                                    : { background: 'var(--bg-card)', border: '1px solid rgba(255,255,255,0.07)' }}
                            >
                                <div className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</div>
                                {message.loading && (
                                    <div className="mt-3 flex gap-1.5 items-center h-4">
                                        <div className="typing-dot w-2 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.4)' }} />
                                        <div className="typing-dot w-2 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.4)' }} />
                                        <div className="typing-dot w-2 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.4)' }} />
                                    </div>
                                )}
                                {Array.isArray(message.matchResults) && message.matchResults.length > 0 && (
                                    <div className="mt-3 space-y-3">
                                        {message.matchResults.map((match, matchIndex) => (
                                            <MatchResultCard
                                                key={match.id || `${match.rank || matchIndex}`}
                                                image_url={match.image_url}
                                                final_category={match.model_category || match.category || match.final_category}
                                                score={match.score}
                                                location={match.location || 'Location not provided'}
                                                reported_time={match.reported_time || 'Recently reported'}
                                                isBestMatch={matchIndex === 0}
                                                onContact={() => setSelectedMatch(match)}
                                            />
                                        ))}
                                    </div>
                                )}
                                {message.retryMatch && !message.loading && (!message.matchResults || message.matchResults.length === 0) && (
                                    <button
                                        type="button"
                                        onClick={() => handleRetryMatch(message.id || '', message.retryMatch!)}
                                        className="mt-3 text-xs font-semibold uppercase tracking-wider px-3 py-2 rounded-lg border border-indigo-400/50 text-indigo-300 hover:bg-indigo-500/20 transition-colors"
                                    >
                                        Retry Matching
                                    </button>
                                )}
                                <div className={`text-[9px] mt-2 opacity-50 flex items-center gap-1 ${message.role === 'user' ? 'text-white' : 'text-slate-400'}`}>
                                    <span>{message.role === 'user' ? 'You' : 'Assistant'}</span>
                                    <span>•</span>
                                    <span>{new Date(message.timestamp || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* Typing indicator */}
                    {isTyping && (
                        <div className="flex justify-start">
                            <div className="rounded-2xl rounded-bl-none px-4 py-3"
                                style={{ background: 'var(--bg-card)', border: '1px solid rgba(255,255,255,0.07)' }}>
                                <div className="flex gap-1.5 items-center h-4">
                                    <div className="typing-dot w-2 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.4)' }} />
                                    <div className="typing-dot w-2 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.4)' }} />
                                    <div className="typing-dot w-2 h-2 rounded-full" style={{ background: 'rgba(255,255,255,0.4)' }} />
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Image Preview Area */}
                {imagePreview && (
                    <div className="mt-4 flex">
                        <div className="relative rounded-xl overflow-hidden" style={{ border: '1px solid rgba(255,255,255,0.1)' }}>
                            <img src={imagePreview} alt="Attached preview" className="h-20 w-auto object-cover opacity-90" />
                            <button
                                onClick={removeImage}
                                className="absolute top-1 right-1 bg-black/50 hover:bg-black/80 text-white rounded-full p-1 transition-colors backdrop-blur-sm"
                            >
                                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
                                    <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
                                </svg>
                            </button>
                        </div>
                    </div>
                )}

                {/* Input bar */}
                <div className="mt-3 flex items-end gap-3">
                    <input
                        type="file"
                        accept="image/*"
                        className="hidden"
                        ref={fileInputRef}
                        onChange={handleImageChange}
                    />
                    <button
                        type="button"
                        onClick={() => fileInputRef.current?.click()}
                        className="h-12 w-12 rounded-xl flex items-center justify-center transition-all duration-200 text-slate-400 hover:text-white"
                        style={{ background: 'var(--bg-input)', border: '1px solid rgba(255,255,255,0.08)' }}
                        title="Attach image"
                    >
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                            <path strokeLinecap="round" strokeLinejoin="round" d="M18.375 12.739l-7.693 7.693a4.5 4.5 0 01-6.364-6.364l10.94-10.94A3 3 0 1119.5 7.372L8.552 18.32m.009-.01l-.01.01m5.699-9.941l-7.81 7.81a1.5 1.5 0 002.112 2.13" />
                        </svg>
                    </button>
                    <div className="flex-1 rounded-xl transition-all duration-200"
                        style={{ background: 'var(--bg-input)', border: '1px solid rgba(255,255,255,0.08)' }}
                        onFocusCapture={e => (e.currentTarget.style.borderColor = 'rgba(99,102,241,0.55)')}
                        onBlurCapture={e => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.08)')}>
                        <textarea
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={handleKeyDown}
                            placeholder="Describe the item, location, and any details..."
                            className="w-full bg-transparent border-none text-white placeholder-slate-500 px-4 py-3 focus:ring-0 resize-none h-12 max-h-32 text-sm"
                            rows={1}
                        />
                    </div>
                    <button
                        type="button"
                        onClick={handleSend}
                        disabled={isTyping || !input.trim()}
                        className="px-5 py-3 text-[10px] font-bold uppercase tracking-[0.2em] text-white rounded-xl transition-all duration-200 flex items-center gap-2 disabled:opacity-40 disabled:cursor-not-allowed"
                        style={{ background: 'var(--accent-primary)', boxShadow: '0 4px 16px rgba(99,102,241,0.3)' }}
                    >
                        <span>Send</span>
                        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3 h-3">
                            <path d="M3.105 2.289a.75.75 0 00-.826.95l1.414 4.925A1.5 1.5 0 005.135 9.25h6.115a.75.75 0 010 1.5H5.135a1.5 1.5 0 00-1.442 1.086l-1.414 4.926a.75.75 0 00.826.95 28.896 28.896 0 0015.293-7.154.75.75 0 000-1.115A28.897 28.897 0 003.105 2.289z" />
                        </svg>
                    </button>
                </div>
            </section>

            {/* ── Sidebar: Collected Summary ── */}
            <aside className="glass-panel rounded-2xl p-6 flex flex-col gap-5">
                {/* Summary */}
                <div>
                    <div className="text-[11px] uppercase tracking-[0.3em] text-slate-400 mb-2">Collected Summary</div>
                    <div className="text-xs text-slate-300 leading-relaxed min-h-[56px]">
                        {summaryText || 'Awaiting details from the conversation.'}
                    </div>
                </div>

                {/* Field Status */}
                <div className="rounded-xl p-4 flex-1"
                    style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                    <div className="text-[11px] uppercase tracking-[0.3em] text-slate-400 mb-3">Field Status</div>
                    <div className="flex flex-wrap gap-2">
                        {['item_type', 'color', 'brand', 'location', 'time'].map((field) => {
                            const isCaptured = !!extractedInfo?.[field];
                            return (
                                <span
                                    key={field}
                                    className="text-[10px] uppercase tracking-wider px-2.5 py-1 rounded-full font-medium transition-colors"
                                    style={isCaptured
                                        ? { background: 'rgba(99,102,241,0.2)', color: '#a5b4fc', border: '1px solid rgba(99,102,241,0.35)' }
                                        : { background: 'rgba(255,255,255,0.04)', color: 'rgba(255,255,255,0.3)', border: '1px solid rgba(255,255,255,0.08)' }}
                                >
                                    {isCaptured ? '✓ ' : '× '}{field.replace('_', ' ')}
                                </span>
                            );
                        })}
                    </div>
                </div>

                {/* Confirm Button */}
                <button
                    type="button"
                    onClick={handleConfirm}
                    disabled={isProcessingReport || !summaryText || summaryConfirmed || !pendingImage || (intent !== 'lost' && intent !== 'found')}
                    className="w-full text-[10px] uppercase tracking-widest py-3 rounded-lg font-semibold transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                    style={{ border: '1px solid rgba(99,102,241,0.45)', color: '#a5b4fc' }}
                    onMouseEnter={e => !summaryConfirmed && ((e.currentTarget as HTMLElement).style.background = 'rgba(99,102,241,0.15)')}
                    onMouseLeave={e => ((e.currentTarget as HTMLElement).style.background = 'transparent')}
                >
                    {isProcessingReport ? 'Processing...' : summaryConfirmed ? '✓ Confirmed' : 'Confirm and Process'}
                </button>
                {!pendingImage && (
                    <p className="text-[10px] text-slate-500">Attach an image to run validation and matching.</p>
                )}
            </aside>
            </div>

            {/* Global Contact Details Modal */}
            {selectedMatch && (
                <div className="fixed inset-0 z-[110] flex items-center justify-center bg-black/70 backdrop-blur-sm px-4">
                    <div className="w-full max-w-3xl rounded-2xl border border-white/10 bg-[#111827] shadow-[0_24px_80px_rgba(0,0,0,0.55)] overflow-hidden animate-fade-in">
                        <div className="flex items-center justify-between px-5 py-3 border-b border-white/10">
                            <h3 className="text-white font-semibold text-lg">Matched Item Contact Details</h3>
                            <button
                                onClick={() => setSelectedMatch(null)}
                                className="text-slate-300 hover:text-white text-sm px-2 py-1 rounded hover:bg-white/10"
                            >
                                Close
                            </button>
                        </div>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-0">
                            <div className="p-4 border-r border-white/10">
                                <div className="w-full aspect-square rounded-xl overflow-hidden bg-black/30 border border-white/10">
                                    <img
                                        src={selectedMatch.image_url}
                                        alt={selectedMatch.final_category || selectedMatch.category || 'Matched item'}
                                        className="w-full h-full object-cover"
                                    />
                                </div>
                            </div>
                            <div className="p-5 space-y-3">
                                <div>
                                    <div className="text-xs uppercase tracking-wider text-slate-400">Category</div>
                                    <div className="text-white font-medium">{selectedMatch.final_category || selectedMatch.category || 'Unknown'}</div>
                                </div>
                                <div>
                                    <div className="text-xs uppercase tracking-wider text-slate-400">Location</div>
                                    <div className="text-white">{selectedMatch.location || 'Not provided'}</div>
                                </div>
                                <div>
                                    <div className="text-xs uppercase tracking-wider text-slate-400">Time</div>
                                    <div className="text-white">{selectedMatch.reported_time || 'Not provided'}</div>
                                </div>
                                <div>
                                    <div className="text-xs uppercase tracking-wider text-slate-400">Reported By (Email)</div>
                                    <div className="text-white break-all">{selectedMatch.user_email || 'Not available'}</div>
                                </div>
                                <div>
                                    <div className="text-xs uppercase tracking-wider text-slate-400">Reporter Profile</div>
                                    <div className="text-white break-all">{selectedMatch.user_id || 'Not available'}</div>
                                </div>
                                <div>
                                    <div className="text-xs uppercase tracking-wider text-slate-400">Phone Number</div>
                                    {selectedMatch.phone_number ? (
                                        <div className="flex items-center gap-2">
                                            <div className="text-white font-mono">{selectedMatch.phone_number}</div>
                                            <button
                                                onClick={() => {
                                                    navigator.clipboard.writeText(selectedMatch.phone_number);
                                                }}
                                                className="px-2 py-1 text-xs bg-white/10 hover:bg-white/20 text-white rounded transition-colors"
                                                title="Copy to clipboard"
                                            >
                                                Copy
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="text-slate-500">Not available</div>
                                    )}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default ChatbotPage;
