import { create } from 'zustand';
import type { ValidationResponse } from '../types/api';

interface ValidationState {
    currentResult: ValidationResponse | null;
    isLoading: boolean;
    error: string | null;
    progress: number;
    progressMessage: string | null;
    pendingText: string;
    pendingVisualText: string;
    pendingImageFile: File | null;
    pendingAudioFile: File | null;
    pendingExtractedInfo: Record<string, string> | null;
    intent: string | null;

    // Actions
    setResult: (result: ValidationResponse | null) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    setProgress: (progress: number, message?: string) => void;
    setPendingInputs: (text: string, visualText: string) => void;
    setPendingMedia: (image: File | null, audio: File | null) => void;
    setPendingExtractedInfo: (info: Record<string, string> | null) => void;
    setIntent: (intent: string | null) => void;
    clearPending: () => void;
    reset: () => void;
}

export const useValidationStore = create<ValidationState>((set) => ({
    currentResult: null,
    isLoading: false,
    error: null,
    progress: 0,
    progressMessage: null,
    pendingText: '',
    pendingVisualText: '',
    pendingImageFile: null,
    pendingAudioFile: null,
    pendingExtractedInfo: null,
    intent: null,

    setResult: (result) => set({ currentResult: result, isLoading: false, error: null }),
    setLoading: (loading) => set({ isLoading: loading, error: null }),
    setError: (error) => set({ error, isLoading: false }),
    setProgress: (progress, message) => set({ progress, progressMessage: message || null }),
    setPendingInputs: (text, visualText) => set({ pendingText: text, pendingVisualText: visualText }),
    setPendingMedia: (image, audio) => set({ pendingImageFile: image, pendingAudioFile: audio }),
    setPendingExtractedInfo: (info) => set({ pendingExtractedInfo: info }),
    setIntent: (intent) => set({ intent }),
    clearPending: () => set({
        pendingText: '',
        pendingVisualText: '',
        pendingImageFile: null,
        pendingAudioFile: null,
        pendingExtractedInfo: null,
    }),
    reset: () => set({
        currentResult: null,
        isLoading: false,
        error: null,
        progress: 0,
        progressMessage: null,
        pendingText: '',
        pendingVisualText: '',
        pendingImageFile: null,
        pendingAudioFile: null,
        pendingExtractedInfo: null,
        intent: null,
    }),
}));
