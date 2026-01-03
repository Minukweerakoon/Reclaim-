/**
 * React Hook for Text-to-Speech functionality
 * Provides easy access to TTS features in React components
 */

import { useState, useEffect, useCallback } from 'react';
import { getTTSService, TTSSettings, Voice } from '../services/tts';

export const useTTS = () => {
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [settings, setSettings] = useState<TTSSettings | null>(null);
    const [voices, setVoices] = useState<Voice[]>([]);
    const [isSupported, setIsSupported] = useState(true);

    const ttsService = getTTSService();

    // Initialize
    useEffect(() => {
        // Check support
        const supported = 'speechSynthesis' in window;
        setIsSupported(supported);

        if (!supported) {
            console.warn('Text-to-Speech not supported in this browser');
            return;
        }

        // Load initial settings
        setSettings(ttsService.getSettings());

        // Load voices
        const loadVoices = () => {
            const availableVoices = ttsService.getVoices();
            setVoices(availableVoices);
        };

        loadVoices();

        // Listen for voice list updates
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = loadVoices;
        }

        // Listen for speaking state changes
        ttsService.onSpeakingChangeCallback((speaking) => {
            setIsSpeaking(speaking);
        });

        return () => {
            ttsService.stop();
        };
    }, []);

    /**
     * Speak text
     */
    const speak = useCallback(async (text: string) => {
        if (!text || !isSupported) return;

        try {
            await ttsService.speak(text);
        } catch (error) {
            console.error('TTS speak error:', error);
        }
    }, [isSupported]);

    /**
     * Stop speaking
     */
    const stop = useCallback(() => {
        ttsService.stop();
    }, []);

    /**
     * Pause speaking
     */
    const pause = useCallback(() => {
        ttsService.pause();
    }, []);

    /**
     * Resume speaking
     */
    const resume = useCallback(() => {
        ttsService.resume();
    }, []);

    /**
     * Update settings
     */
    const updateSettings = useCallback((updates: Partial<TTSSettings>) => {
        ttsService.updateSettings(updates);
        setSettings(ttsService.getSettings());
    }, []);

    /**
     * Toggle auto-speak
     */
    const toggleAutoSpeak = useCallback(() => {
        const newValue = !settings?.autoSpeak;
        ttsService.setAutoSpeak(newValue);
        setSettings(ttsService.getSettings());
    }, [settings]);

    /**
     * Set voice
     */
    const setVoice = useCallback((voiceId: string) => {
        ttsService.setVoice(voiceId);
        setSettings(ttsService.getSettings());
    }, []);

    /**
     * Set speech rate
     */
    const setRate = useCallback((rate: number) => {
        ttsService.setRate(rate);
        setSettings(ttsService.getSettings());
    }, []);

    /**
     * Set speech pitch
     */
    const setPitch = useCallback((pitch: number) => {
        ttsService.setPitch(pitch);
        setSettings(ttsService.getSettings());
    }, []);

    /**
     * Set volume
     */
    const setVolume = useCallback((volume: number) => {
        ttsService.setVolume(volume);
        setSettings(ttsService.getSettings());
    }, []);

    return {
        // State
        isSpeaking,
        settings,
        voices,
        isSupported,

        // Actions
        speak,
        stop,
        pause,
        resume,
        updateSettings,
        toggleAutoSpeak,
        setVoice,
        setRate,
        setPitch,
        setVolume,
    };
};
