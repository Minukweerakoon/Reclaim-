import axios from 'axios';
import type { ValidationResponse } from '../types/api';

// Read API key from env; fall back to dev default so local dev still works
const API_KEY = import.meta.env.VITE_API_KEY || 'test-api-key';

// Separate axios instance for /validate/* endpoints (not under /api prefix)
// Use direct URL to bypass Vite proxy issues
const validationClient = axios.create({
    baseURL: 'http://127.0.0.1:8000',
    headers: {
        'X-API-Key': API_KEY,
    },
    timeout: 600000, // 10 minutes - validation can be slow with ML models
});

// Request interceptor for logging
validationClient.interceptors.request.use(
    (config) => {
        if (import.meta.env.DEV) {
            console.log(`[Validation API] ${config.method?.toUpperCase()} ${config.url}`);
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Response interceptor for error handling
validationClient.interceptors.response.use(
    (response) => response,
    (error) => {
        const message = error.response?.data?.detail || error.message || 'Validation request failed';
        console.error('[Validation API] Error:', message);
        return Promise.reject(new Error(message));
    }
);

export interface CompleteValidationParams {
    text?: string;
    visualText?: string;
    imageFile?: File | null;
    audioFile?: File | null;
    language?: string;
    /** 'lost' or 'found' — routes into correct Supabase table */
    intent?: string;
    /** Firebase UID of the authenticated user */
    userId?: string;
    /** Email of the authenticated user */
    userEmail?: string;
    /** Existing ID to update in the DB instead of creating a new one */
    supabaseId?: string;
    /** User phone number for contact details in retrieval cards */
    userPhone?: string;
}

export const validationApi = {
    /**
     * Complete multimodal validation — sends intent + user info so the backend
     * can call save_validated_item into the correct lost_items / found_items table.
     */
    async validateComplete(params: CompleteValidationParams): Promise<ValidationResponse> {
        const formData = new FormData();
        if (params.text) formData.append('text', params.text);
        if (params.visualText) formData.append('visualText', params.visualText);
        if (params.imageFile) formData.append('image_file', params.imageFile);
        if (params.audioFile) formData.append('audio_file', params.audioFile);
        formData.append('language', params.language || 'en');

        if (params.intent) formData.append('intent', params.intent);

        // FIX: backend expects these exact names
        if (params.userId) formData.append('userId', params.userId);
        if (params.userEmail) formData.append('userEmail', params.userEmail);
        if (params.userPhone) formData.append('userPhone', params.userPhone);

        const response = await validationClient.post('/validate/complete', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    /**
     * Text-only validation
     */
    async validateText(text: string, language: string = 'en'): Promise<ValidationResponse> {
        const response = await validationClient.post('/validate/text', {
            text,
            language,
        }, {
            headers: { 'Content-Type': 'application/json' },
        });
        return response.data;
    },

    /**
     * Image-only validation
     */
    async validateImage(file: File, text?: string): Promise<ValidationResponse> {
        const formData = new FormData();
        formData.append('image_file', file);
        if (text) formData.append('text', text);
        const response = await validationClient.post('/validate/image', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    /**
     * Voice-only validation
     */
    async validateVoice(file: File, language: string = 'en'): Promise<ValidationResponse> {
        const formData = new FormData();
        formData.append('audio_file', file);
        formData.append('language', language);
        const response = await validationClient.post('/validate/voice', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    },

    /**
     * Get validation result by request ID
     */
    async getResult(requestId: string): Promise<ValidationResponse> {
        const response = await validationClient.get(`/results/${requestId}`);
        return response.data;
    },
};
