import { create } from 'zustand';

// --- Types (Migrated from App.tsx) ---

export type ConversationState =
    | 'welcome'
    | 'item_details'
    | 'awaiting_image'
    | 'awaiting_voice'
    | 'resolving_mismatch'
    | 'completed';

export interface Message {
    id: string;
    type: 'bot' | 'user';
    content: string;
    timestamp: Date;
    metadata?: Record<string, unknown>;
}

export interface ValidationState {
    itemType?: string;
    colorHint?: string;
    brandHint?: string;
    initialMention?: string;
    text?: string;
    originalMessage?: string;
    image?: File;
    voice?: Blob;
    textResult?: any;
    imageResult?: any;
    voiceResult?: any;
    crossModalPreview?: any;
    overallResult?: any;
    spatialTemporalResult?: any;
    attentionResult?: any;
}

export interface ProgressEntry {
    label: string;
    value: string;
}

interface ValidationStoreState {
    // State
    messages: Message[];
    conversationState: ConversationState;
    userIntention: 'lost' | 'found' | 'inquiry' | null;
    validationState: ValidationState;
    isProcessing: boolean;
    progressLog: ProgressEntry[];
    activeTaskId: string | null;

    // Actions
    addBotMessage: (content: string, metadata?: any) => void;
    addUserMessage: (content: string) => void;
    setConversationState: (state: ConversationState) => void;
    setUserIntention: (intention: 'lost' | 'found' | 'inquiry' | null) => void;
    updateValidationState: (updates: Partial<ValidationState>) => void;
    setIsProcessing: (isProcessing: boolean) => void;
    pushProgress: (label: string, value: string) => void;
    setActiveTaskId: (id: string | null) => void;
    resetStore: () => void;
}

export const useValidationStore = create<ValidationStoreState>((set) => ({
    // Initial State
    messages: [],
    conversationState: 'welcome',
    userIntention: null,
    validationState: {},
    isProcessing: false,
    progressLog: [],
    activeTaskId: null,

    // Actions
    addBotMessage: (content, metadata) =>
        set((state) => ({
            messages: [
                ...state.messages,
                {
                    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
                    type: 'bot',
                    content,
                    timestamp: new Date(),
                    metadata,
                },
            ],
        })),

    addUserMessage: (content) =>
        set((state) => ({
            messages: [
                ...state.messages,
                {
                    id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
                    type: 'user',
                    content,
                    timestamp: new Date(),
                },
            ],
        })),

    setConversationState: (conversationState) => set({ conversationState }),

    setUserIntention: (userIntention) => set({ userIntention }),

    updateValidationState: (updates) =>
        set((state) => ({
            validationState: { ...state.validationState, ...updates },
        })),

    setIsProcessing: (isProcessing) => set({ isProcessing }),

    pushProgress: (label, value) =>
        set((state) => {
            const filtered = state.progressLog.filter((entry) => entry.label !== label);
            const next = [...filtered, { label, value }];
            return { progressLog: next.slice(-7) };
        }),

    setActiveTaskId: (activeTaskId) => set({ activeTaskId }),

    resetStore: () =>
        set({
            messages: [],
            conversationState: 'welcome',
            userIntention: null,
            validationState: {},
            isProcessing: false,
            progressLog: [],
            activeTaskId: null,
        }),
}));
