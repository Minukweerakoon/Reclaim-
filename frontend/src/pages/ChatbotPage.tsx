import { useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { chatApi } from '../api/chat';
import { formatErrorMessage } from '../components/ErrorMessage';
import type { ChatMessage } from '../types/api';
import { useValidationStore } from '../store/useValidationStore';
import { useChatStore } from '../store/useChatStore';

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

function ChatbotPage() {
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();
    const initialIntent = searchParams.get('intent') || '';

    const [input, setInput] = useState('');
    const {
        messages, setMessages,
        isTyping, setIsTyping,
        extractedInfo, setExtractedInfo,
        intent, setIntent,
        summaryConfirmed, setSummaryConfirmed,
        pendingImage, imagePreview, setPendingImage
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
        if (initialIntent && !intent) {
            setIntent(initialIntent);
        }
    }, [initialIntent, intent, setIntent]);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const { currentResult, setPendingInputs, setPendingMedia, setPendingExtractedInfo, setIntent: setStoreIntent } = useValidationStore();

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
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const summaryText = useMemo(() => summarizeExtractedInfo(extractedInfo, intent), [extractedInfo, intent]);

    const handleSend = async () => {
        if (!input.trim() || isTyping) return;

        const userMessage: ChatMessage = {
            role: 'user',
            content: input,
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

            const botMessage: ChatMessage = {
                role: 'bot',
                content: response.bot_response,
                timestamp: new Date()
            };
            setMessages((prev) => [...prev, botMessage]);
            setExtractedInfo((prev) => ({
                ...prev,
                ...response.extracted_info,
            }));
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

    const handleConfirm = () => {
        setStoreIntent(intent);
        setPendingInputs(
            summarizeExtractedInfo(extractedInfo, intent), // The structured facts
            buildVisualSeed(extractedInfo)                 // The visual hint for CLIP
        );
        setPendingExtractedInfo(extractedInfo);
        if (pendingImage) {
            setPendingMedia(pendingImage, null);
        }
        navigate('/validation', {
            state: {
                prefillText: summarizeExtractedInfo(extractedInfo, intent),
                prefillVisualText: buildVisualSeed(extractedInfo)
            }
        });
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-6 min-h-[calc(100vh-160px)] animate-fade-in">
            {/* ── Chat Panel ── */}
            <section className="glass-panel rounded-2xl p-6 flex flex-col">
                {/* Header */}
                <div className="flex items-center justify-between mb-5 pb-4"
                    style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                    <div>
                        <div className="text-[11px] uppercase tracking-[0.3em] font-semibold"
                            style={{ color: 'var(--accent-secondary)' }}>
                            Conversation Phase
                        </div>
                        <div className="text-xs text-slate-400 mt-1">Gemini-guided intake and clarification</div>
                    </div>
                    <div className="text-[10px] uppercase tracking-widest text-slate-500 px-2 py-1 rounded"
                        style={{ background: 'rgba(255,255,255,0.04)' }}>
                        Intent: {intent || 'pending'}
                    </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto space-y-4 pr-1">
                    {messages.map((message, index) => (
                        <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fade-in`}>
                            <div
                                className={`max-w-[72%] rounded-2xl px-4 py-3 ${message.role === 'user'
                                    ? 'text-white rounded-br-none'
                                    : 'text-slate-100 rounded-bl-none'
                                    }`}
                                style={message.role === 'user'
                                    ? { background: 'var(--accent-primary)', boxShadow: '0 4px 16px rgba(99,102,241,0.25)' }
                                    : { background: 'var(--bg-card)', border: '1px solid rgba(255,255,255,0.07)' }}
                            >
                                <div className="whitespace-pre-wrap text-sm leading-relaxed">{message.content}</div>
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
                    disabled={!summaryText || summaryConfirmed}
                    className="w-full text-[10px] uppercase tracking-widest py-3 rounded-lg font-semibold transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed"
                    style={{ border: '1px solid rgba(99,102,241,0.45)', color: '#a5b4fc' }}
                    onMouseEnter={e => !summaryConfirmed && ((e.currentTarget as HTMLElement).style.background = 'rgba(99,102,241,0.15)')}
                    onMouseLeave={e => ((e.currentTarget as HTMLElement).style.background = 'transparent')}
                >
                    {summaryConfirmed ? '✓ Confirmed' : 'Confirm and Continue'}
                </button>
            </aside>
        </div>
    );
}

export default ChatbotPage;
