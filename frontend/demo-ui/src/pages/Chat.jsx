import { useState, useRef, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { chatApi } from '../../../src/api/chat';
import { formatErrorMessage } from '../../../src/components/ErrorMessage';
import { useValidationStore } from '../../../src/store/useValidationStore';

function Chat() {
    const navigate = useNavigate();
    const [input, setInput] = useState('');
    const [messages, setMessages] = useState([
        { role: 'bot', content: "Welcome to the Neural Validation Command Center. I can help you report lost or found items. Describe what happened and I'll guide you through the validation process. You can also attach images or audio recordings." }
    ]);
    const [isTyping, setIsTyping] = useState(false);
    const [attachedImage, setAttachedImage] = useState(null);
    const [attachedAudio, setAttachedAudio] = useState(null);
    const [extractedInfo, setExtractedInfo] = useState({});
    const [intent, setIntent] = useState('');
    const [summaryConfirmed, setSummaryConfirmed] = useState(false);

    const messagesEndRef = useRef(null);
    const fileInputRef = useRef(null);
    const audioInputRef = useRef(null);

    // Store connection for shared state if needed, primarily for results
    const { currentResult, setPendingInputs, setPendingMedia } = useValidationStore();

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const extractedEntries = useMemo(() => {
        return Object.entries(extractedInfo || {}).filter(([_, value]) => value !== null && value !== undefined && value !== '');
    }, [extractedInfo]);

    const summaryText = useMemo(() => {
        if (!extractedEntries.length) return '';
        const parts = extractedEntries.map(([key, value]) => `${key.replace(/_/g, ' ')}: ${String(value)}`);
        return parts.join(', ');
    }, [extractedEntries]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const handleSend = async () => {
        if ((!input.trim() && !attachedImage && !attachedAudio) || isTyping) return;

        const userMessage = { role: 'user', content: input };
        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setIsTyping(true);

        const history = messages;

        try {
            const response = await chatApi.sendMessage({
                message: userMessage.content,
                history: history,
                previous_prediction: currentResult || undefined
            });

            const botMessage = { role: 'bot', content: response.bot_response };
            setMessages(prev => [...prev, botMessage]);

            if (response.extracted_info) {
                setExtractedInfo(response.extracted_info || {});
            }
            if (response.intention) {
                setIntent(response.intention);
            }
            setSummaryConfirmed(false);

        } catch (error) {
            console.error('Chat error:', error);
            let errorMsg = formatErrorMessage(error);
            // Handle structured error objects from API interceptor
            if (error && typeof error === 'object' && 'message' in error) {
                errorMsg = error.message;
            }
            setMessages(prev => [...prev, { 
                role: 'bot', 
                content: `I'm sorry, I encountered an error: ${errorMsg}. Please try again.` 
            }]);
        } finally {
            setIsTyping(false);
            setAttachedImage(null); // Clear attachments after send
            setAttachedAudio(null);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    const handleProceed = () => {
        if (!summaryText) return;
        const visualSeed = extractedInfo?.item_type || extractedInfo?.color || '';
        setPendingInputs(summaryText, visualSeed);
        setPendingMedia(attachedImage, attachedAudio);
        navigate('/validation', {
            state: {
                prefillText: summaryText,
                prefillVisualText: visualSeed,
            },
        });
    };

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-[calc(100vh-140px)]">
            {/* Chat Area */}
            <div className="lg:col-span-2 flex flex-col glass-panel rounded-xl overflow-hidden h-full">
                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {messages.map((msg, idx) => (
                        <div
                            key={idx}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-[80%] rounded-2xl p-4 ${msg.role === 'user'
                                    ? 'bg-primary text-white rounded-br-none'
                                    : 'bg-surface-dark border border-surface-border text-slate-100 rounded-bl-none'
                                    }`}
                            >
                                <div className="whitespace-pre-wrap">{msg.content}</div>
                                <div className={`text-xs mt-2 ${msg.role === 'user' ? 'text-primary-100' : 'text-slate-400'}`}>
                                    {msg.role === 'user' ? 'You' : 'Neural Assistant'} • {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </div>
                            </div>
                        </div>
                    ))}
                    {isTyping && (
                        <div className="flex justify-start">
                            <div className="bg-surface-dark border border-surface-border rounded-2xl rounded-bl-none p-4">
                                <div className="flex gap-2">
                                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                                    <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Refresh Input Area */}
                <div className="p-4 bg-surface-dark border-t border-surface-border">
                    {/* Attachments Preview */}
                    {(attachedImage || attachedAudio) && (
                        <div className="flex gap-2 mb-3 px-2">
                            {attachedImage && (
                                <div className="relative group">
                                    <div className="bg-surface-border rounded px-2 py-1 text-xs flex items-center gap-1">
                                        <span>📸 {attachedImage.name}</span>
                                    </div>
                                    <button
                                        onClick={() => setAttachedImage(null)}
                                        className="absolute -top-2 -right-2 bg-alert-red text-white rounded-full w-4 h-4 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                                    >
                                        ×
                                    </button>
                                </div>
                            )}
                            {attachedAudio && (
                                <div className="relative group">
                                    <div className="bg-surface-border rounded px-2 py-1 text-xs flex items-center gap-1">
                                        <span>🎤 {attachedAudio.name}</span>
                                    </div>
                                    <button
                                        onClick={() => setAttachedAudio(null)}
                                        className="absolute -top-2 -right-2 bg-alert-red text-white rounded-full w-4 h-4 flex items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity"
                                    >
                                        ×
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

                    <div className="flex items-end gap-3">
                        {/* File Upload Buttons */}
                        <div className="flex gap-1 pb-1">
                            <input
                                type="file"
                                ref={fileInputRef}
                                className="hidden"
                                accept="image/*"
                                onChange={(e) => {
                                    const file = e.target.files?.[0] || null;
                                    setAttachedImage(file);
                                }}
                            />
                            <button
                                onClick={() => fileInputRef.current?.click()}
                                className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                                title="Upload Image"
                            >
                                📷
                            </button>

                            <input
                                type="file"
                                ref={audioInputRef}
                                className="hidden"
                                accept="audio/*"
                                onChange={(e) => {
                                    const file = e.target.files?.[0] || null;
                                    setAttachedAudio(file);
                                }}
                            />
                            <button
                                onClick={() => audioInputRef.current?.click()}
                                className="p-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
                                title="Upload Audio"
                            >
                                🎤
                            </button>
                        </div>

                        <div className="flex-1 bg-background-dark rounded-xl border border-surface-border focus-within:border-primary focus-within:ring-1 focus-within:ring-primary transition-all">
                            <textarea
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Describe your lost or found item..."
                                className="w-full bg-transparent border-none text-white placeholder-slate-500 px-4 py-3 focus:ring-0 resize-none h-12 max-h-32"
                                rows={1}
                            />
                        </div>

                        <button
                            onClick={handleSend}
                            disabled={!input.trim() && !attachedImage && !attachedAudio}
                            className="p-3 bg-primary hover:bg-primary/90 text-white rounded-xl disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                        >
                            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                                <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
                            </svg>
                        </button>
                    </div>
                </div>
            </div>

            {/* Sidebar Info Panel */}
            <div className="lg:col-span-1 space-y-6">
                <div className="glass-panel p-6 rounded-xl">
                    <h3 className="text-lg font-semibold mb-4">Conversation Summary</h3>
                    {extractedEntries.length ? (
                        <div className="space-y-3">
                            {extractedEntries.map(([key, value]) => (
                                <div key={key} className="bg-surface-dark/70 border border-surface-border rounded-lg p-3">
                                    <div className="text-[10px] text-slate-500 uppercase tracking-widest">{key.replace(/_/g, ' ')}</div>
                                    <div className="text-sm text-white mt-1">{String(value)}</div>
                                </div>
                            ))}
                            {intent && (
                                <div className="text-[11px] text-primary uppercase tracking-widest">Intent: {intent}</div>
                            )}
                            <label className="flex items-center gap-2 text-xs text-slate-300">
                                <input
                                    type="checkbox"
                                    className="rounded border-surface-border bg-background-dark"
                                    checked={summaryConfirmed}
                                    onChange={(event) => setSummaryConfirmed(event.target.checked)}
                                />
                                Confirm these details are correct
                            </label>
                            <button
                                type="button"
                                onClick={handleProceed}
                                disabled={!summaryConfirmed}
                                className="w-full text-xs uppercase tracking-widest bg-primary/20 text-primary border border-primary/40 py-2 rounded-lg hover:bg-primary/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                            >
                                Proceed to validation
                            </button>
                        </div>
                    ) : (
                        <div className="text-sm text-slate-400">Summary will appear as the assistant extracts details.</div>
                    )}
                </div>

                <div className="glass-panel p-6 rounded-xl">
                    <h3 className="text-lg font-semibold mb-4">Visual Analysis</h3>
                    <div className="aspect-video bg-background-dark rounded-lg flex items-center justify-center border-2 border-dashed border-surface-border">
                        <div className="text-center text-slate-500">
                            <div className="text-4xl mb-2">👁️</div>
                            <p>No visual context active</p>
                        </div>
                    </div>
                    {/* If we had a currentResult from the validation store, we could display it here */}
                    {currentResult && (
                        <div className="mt-4">
                            <p className="text-sm text-slate-400">Context Loaded</p>
                            <div className="text-neon-green text-sm flex items-center gap-1">
                                <span>●</span> {currentResult.confidence.overall_confidence ? `${Math.round(currentResult.confidence.overall_confidence * 100)}% Confidence` : 'Analyzed'}
                            </div>
                        </div>
                    )}
                </div>

                <div className="glass-panel p-6 rounded-xl">
                    <h3 className="text-lg font-semibold mb-4">Context</h3>
                    <div className="space-y-4">
                        <div>
                            <label className="text-xs text-slate-500 uppercase font-bold">Location</label>
                            <div className="text-slate-300">Awaiting data...</div>
                        </div>
                        <div>
                            <label className="text-xs text-slate-500 uppercase font-bold">Category</label>
                            <div className="text-slate-300">Unclassified</div>
                        </div>
                        <div>
                            <label className="text-xs text-slate-500 uppercase font-bold">Condition</label>
                            <div className="text-slate-300">Unknown</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Chat;
