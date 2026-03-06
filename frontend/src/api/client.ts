import axios from 'axios';
import { supabase } from '../supabaseClient';

// Create axios instance with base configuration
// Use direct URL to backend to avoid Vite proxy issues
const apiClient = axios.create({
    baseURL: 'http://127.0.0.1:8000/api',
    headers: {
        'Content-Type': 'application/json',
        'X-API-Key': 'test-api-key',
    },
});

// Request interceptor: attach Supabase JWT token + dev logging
apiClient.interceptors.request.use(
    async (config) => {
        // Attach Supabase Bearer token if a session exists
        const { data: { session } } = await supabase.auth.getSession();
        if (session?.access_token) {
            config.headers.Authorization = `Bearer ${session.access_token}`;
        }
        if (import.meta.env.DEV) {
            console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data);
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
    (response) => {
        if (import.meta.env.DEV) {
            console.log(`[API] Response from ${response.config.url}:`, response.data);
        }
        return response;
    },
    (error) => {
        const errorMsg = error.response?.data?.detail || error.response?.data?.message || error.message || 'Unknown error';

        if (error.response) {
            console.error(`[API] HTTP ${error.response.status}:`, errorMsg);
        } else if (error.request) {
            console.error('[API] No response received (network error):', error.message);
        } else {
            console.error('[API] Error setting up request:', error.message);
        }

        return Promise.reject({
            status: error.response?.status,
            message: errorMsg,
            data: error.response?.data,
            originalError: error
        });
    }
);

export default apiClient;
