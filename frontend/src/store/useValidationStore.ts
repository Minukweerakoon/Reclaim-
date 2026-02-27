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

    // Actions
    setResult: (result: ValidationResponse | null) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    setProgress: (progress: number, message?: string) => void;
    setPendingInputs: (text: string, visualText: string) => void;
    setPendingMedia: (image: File | null, audio: File | null) => void;
    clearPending: () => void;
    reset: () => void;
    intent: string | null;
    setIntent: (intent: string | null) => void;
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
    intent: null,

    setResult: (result) => set({ currentResult: result, isLoading: false, error: null }),
    setLoading: (loading) => set({ isLoading: loading, error: null }),
    setError: (error) => set({ error, isLoading: false }),
    setProgress: (progress, message) => set({ progress, progressMessage: message || null }),
    setPendingInputs: (text, visualText) => set({ pendingText: text, pendingVisualText: visualText }),
    setPendingMedia: (image, audio) => set({ pendingImageFile: image, pendingAudioFile: audio }),
    clearPending: () => set({ pendingText: '', pendingVisualText: '', pendingImageFile: null, pendingAudioFile: null }),
    setIntent: (intent) => set({ intent }),
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
        intent: null,
    }),
}));
