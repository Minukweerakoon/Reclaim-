import { useState, useCallback } from 'react';
import axios from 'axios';

interface ValidationRequest {
  text?: string;
  image?: File;
  voice?: Blob;
}

interface ValidateTextOptions {
  language?: string;
  itemTypeHint?: string;
  colorHint?: string;
  locationHint?: string;
}

export const useValidation = () => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  const API_KEY = import.meta.env.VITE_API_KEY || 'test-api-key';

  const validate = useCallback(async (endpoint: string, data: FormData | any) => {
    setIsLoading(true);
    setError(null);
    try {
      const headers: Record<string, string> = {
        'X-API-Key': API_KEY,
      };

      const isFormData = data instanceof FormData;
      if (!isFormData) {
        headers['Content-Type'] = 'application/json';
      }

      const response = await axios.post(`${API_BASE_URL}${endpoint}`, data, { headers });
      return response.data;
    } catch (err: any) {
      console.error(`Validation error for ${endpoint}:`, err);
      setError(err.response?.data?.detail || 'An unexpected error occurred');
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, [API_BASE_URL, API_KEY]);

  const validateText = useCallback(async (text: string, options?: ValidateTextOptions) => {
    const payload: Record<string, unknown> = {
      text,
      language: options?.language ?? 'auto',
    };

    if (options?.itemTypeHint) {
      payload.item_type_hint = options.itemTypeHint;
    }
    if (options?.colorHint) {
      payload.color_hint = options.colorHint;
    }
    if (options?.locationHint) {
      payload.location_hint = options.locationHint;
    }

    const data = await validate('/validate/text', payload);
    return data?.text ?? data;
  }, [validate]);

  const validateImage = useCallback(async (image: File, text?: string) => {
    const formData = new FormData();
    formData.append('image_file', image);
    if (text) {
      formData.append('text', text);
    }
    const data = await validate('/validate/image', formData);
    return data?.image ?? data;
  }, [validate]);

  const validateVoice = useCallback(async (voice: Blob) => {
    const formData = new FormData();
    formData.append('audio_file', voice, 'audio.wav');
    const data = await validate('/validate/voice', formData);
    return data?.voice ?? data;
  }, [validate]);

  const validateComplete = useCallback(async (request: ValidationRequest) => {
    const formData = new FormData();
    if (request.text) {
      formData.append('text', request.text);
    }
    if (request.image) {
      formData.append('image_file', request.image);
    }
    if (request.voice) {
      formData.append('audio_file', request.voice, 'audio.wav');
    }
    return validate('/validate/complete', formData);
  }, [validate]);

  // NEW: Gemini-powered chat conversation
  const sendChatMessage = useCallback(async (
    message: string,
    history: Array<{ role: string; content: string }> = []
  ) => {
    const payload = { message, history };
    const response = await axios.post(
      `${API_BASE_URL}/api/chat/message`,
      payload,
      { headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' } }
    );
    return response.data;
  }, [API_BASE_URL, API_KEY]);

  // NEW: Submit feedback for active learning
  const submitFeedback = useCallback(async (
    inputText: string,
    originalPrediction: any,
    userCorrection: any
  ) => {
    const payload = {
      input_text: inputText,
      original_prediction: originalPrediction,
      user_correction: userCorrection,
      feedback_type: "correction"
    };
    const response = await axios.post(
      `${API_BASE_URL}/api/feedback/submit`,
      payload,
      { headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' } }
    );
    return response.data;
  }, [API_BASE_URL, API_KEY]);

  return {
    isLoading,
    error,
    validateText,
    validateImage,
    validateVoice,
    validateComplete,
    sendChatMessage,
    submitFeedback
  };
};
