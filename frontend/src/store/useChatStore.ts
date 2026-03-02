import { create } from 'zustand';
import type { ChatMessage } from '../types/api';

interface ChatState {
    messages: ChatMessage[];
    isTyping: boolean;
    extractedInfo: Record<string, any>;
    summaryConfirmed: boolean;
    intent: string;
    pendingImage: File | null;
    imagePreview: string | null;

    setMessages: (messages: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])) => void;
    setIsTyping: (isTyping: boolean) => void;
    setExtractedInfo: (info: Record<string, any> | ((prev: Record<string, any>) => Record<string, any>)) => void;
    setSummaryConfirmed: (confirmed: boolean) => void;
    setIntent: (intent: string) => void;
    setPendingImage: (file: File | null, preview: string | null) => void;
    resetChat: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
    messages: [],
    isTyping: false,
    extractedInfo: {},
    summaryConfirmed: false,
    intent: '',
    pendingImage: null,
    imagePreview: null,

    setMessages: (update) => set((state) => ({
        messages: typeof update === 'function' ? update(state.messages) : update
    })),
    setIsTyping: (isTyping) => set({ isTyping }),
    setExtractedInfo: (update) => set((state) => ({
        extractedInfo: typeof update === 'function' ? update(state.extractedInfo) : update
    })),
    setSummaryConfirmed: (summaryConfirmed) => set({ summaryConfirmed }),
    setIntent: (intent) => set({ intent }),
    setPendingImage: (pendingImage, imagePreview) => set({ pendingImage, imagePreview }),
    resetChat: () => set({
        messages: [],
        isTyping: false,
        extractedInfo: {},
        summaryConfirmed: false,
        intent: '',
        pendingImage: null,
        imagePreview: null
    }),
}));
