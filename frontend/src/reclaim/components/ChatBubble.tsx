// @ts-nocheck
import React from 'react';
import { Bot, User } from 'lucide-react';

export function ChatBubble({ message, sender, timestamp, isTyping, children }) {
    const isAI = sender === 'ai';

    if (isTyping) {
        return (
            <div className="flex w-full justify-start mb-6 animate-fade-in">
                <div className="flex items-end gap-3 max-w-[80%]">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center">
                        <Bot className="w-4 h-4 text-cyan-400" />
                    </div>
                    <div className="px-5 py-4 rounded-2xl rounded-tl-sm bg-cyan-900/10 border border-cyan-500/20 text-white shadow-[0_4px_20px_rgba(0,0,0,0.2)]">
                        <div className="flex gap-1.5 items-center h-5">
                            <div className="w-2 h-2 bg-cyan-400 rounded-full typing-dot"></div>
                            <div className="w-2 h-2 bg-cyan-400 rounded-full typing-dot"></div>
                            <div className="w-2 h-2 bg-cyan-400 rounded-full typing-dot"></div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className={`flex w-full mb-6 animate-fade-in ${isAI ? 'justify-start' : 'justify-end'}`}>
            <div className={`flex items-end gap-3 max-w-[85%] md:max-w-[75%] ${isAI ? 'flex-row' : 'flex-row-reverse'}`}>
                <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${isAI ? 'bg-cyan-500/10 border border-cyan-500/20' : 'bg-indigo-500/10 border border-indigo-500/20'
                    }`}>
                    {isAI ? <Bot className="w-4 h-4 text-cyan-400" /> : <User className="w-4 h-4 text-indigo-400" />}
                </div>

                <div className="flex flex-col gap-1">
                    {isAI && <span className="text-[10px] font-medium text-cyan-400 ml-1">Reclaim AI</span>}
                    <div className={`px-5 py-3.5 shadow-lg backdrop-blur-sm ${isAI
                            ? 'rounded-2xl rounded-tl-sm bg-cyan-900/10 border border-cyan-500/20 text-slate-100'
                            : 'rounded-2xl rounded-tr-sm bg-indigo-600/20 border border-indigo-500/30 text-white'
                        }`}>
                        {message && <p className="text-sm md:text-base leading-relaxed whitespace-pre-wrap">{message}</p>}
                        {children}
                    </div>
                    {timestamp && (
                        <span className={`text-[10px] text-slate-500 ${isAI ? 'text-left ml-1' : 'text-right mr-1'}`}>
                            {timestamp}
                        </span>
                    )}
                </div>
            </div>
        </div>
    );
}

