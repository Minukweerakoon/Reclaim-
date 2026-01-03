/**
 * Text-to-Speech Service for Chatbot Voice Responses
 * Uses browser Web Speech API for voice output
 */

export interface TTSSettings {
    autoSpeak: boolean;
    voiceId: string;
    rate: number;  // 0.5 to 2.0
    pitch: number; // 0 to 2.0
    volume: number; // 0 to 1.0
}

export interface Voice {
    id: string;
    name: string;
    lang: string;
    default: boolean;
}

class TextToSpeechService {
    private synthesis: SpeechSynthesis;
    private currentUtterance: SpeechSynthesisUtterance | null = null;
    private settings: TTSSettings;
    private voices: SpeechSynthesisVoice[] = [];
    private onSpeakingChange?: (speaking: boolean) => void;

    constructor() {
        this.synthesis = window.speechSynthesis;

        // Default settings
        this.settings = {
            autoSpeak: false,
            voiceId: '',
            rate: 1.0,
            pitch: 1.0,
            volume: 1.0
        };

        // Load settings from localStorage
        this.loadSettings();

        // Load voices (may be async in some browsers)
        this.loadVoices();
        if (speechSynthesis.onvoiceschanged !== undefined) {
            speechSynthesis.onvoiceschanged = () => this.loadVoices();
        }
    }

    /**
     * Load available voices from browser
     */
    private loadVoices(): void {
        this.voices = this.synthesis.getVoices();

        // If no voice selected, pick a good default
        if (!this.settings.voiceId && this.voices.length > 0) {
            // Prefer English voices
            const englishVoice = this.voices.find(
                v => v.lang.startsWith('en') && (v.name.includes('Google') || v.name.includes('Microsoft'))
            );
            const defaultVoice = englishVoice || this.voices.find(v => v.default) || this.voices[0];
            this.settings.voiceId = defaultVoice.name;
        }
    }

    /**
     * Get list of available voices
     */
    public getVoices(): Voice[] {
        return this.voices.map(v => ({
            id: v.name,
            name: v.name,
            lang: v.lang,
            default: v.default
        }));
    }

    /**
     * Speak text using TTS
     */
    public speak(text: string): Promise<void> {
        return new Promise((resolve, reject) => {
            // Stop any current speech
            this.stop();

            // Clean text for speech
            const cleanText = this.cleanTextForSpeech(text);

            if (!cleanText) {
                resolve();
                return;
            }

            // Create utterance
            const utterance = new SpeechSynthesisUtterance(cleanText);

            // Find selected voice
            const selectedVoice = this.voices.find(v => v.name === this.settings.voiceId);
            if (selectedVoice) {
                utterance.voice = selectedVoice;
            }

            // Apply settings
            utterance.rate = this.settings.rate;
            utterance.pitch = this.settings.pitch;
            utterance.volume = this.settings.volume;

            // Event handlers
            utterance.onstart = () => {
                if (this.onSpeakingChange) {
                    this.onSpeakingChange(true);
                }
            };

            utterance.onend = () => {
                this.currentUtterance = null;
                if (this.onSpeakingChange) {
                    this.onSpeakingChange(false);
                }
                resolve();
            };

            utterance.onerror = (event) => {
                this.currentUtterance = null;
                if (this.onSpeakingChange) {
                    this.onSpeakingChange(false);
                }
                console.error('TTS error:', event);
                reject(event);
            };

            // Speak
            this.currentUtterance = utterance;
            this.synthesis.speak(utterance);
        });
    }

    /**
     * Stop current speech
     */
    public stop(): void {
        if (this.synthesis.speaking) {
            this.synthesis.cancel();
            this.currentUtterance = null;
            if (this.onSpeakingChange) {
                this.onSpeakingChange(false);
            }
        }
    }

    /**
     * Pause speech
     */
    public pause(): void {
        if (this.synthesis.speaking && !this.synthesis.paused) {
            this.synthesis.pause();
        }
    }

    /**
     * Resume paused speech
     */
    public resume(): void {
        if (this.synthesis.paused) {
            this.synthesis.resume();
        }
    }

    /**
     * Check if currently speaking
     */
    public isSpeaking(): boolean {
        return this.synthesis.speaking;
    }

    /**
     * Check if paused
     */
    public isPaused(): boolean {
        return this.synthesis.paused;
    }

    /**
     * Get current settings
     */
    public getSettings(): TTSSettings {
        return { ...this.settings };
    }

    /**
     * Update settings
     */
    public updateSettings(updates: Partial<TTSSettings>): void {
        this.settings = { ...this.settings, ...updates };
        this.saveSettings();
    }

    /**
     * Set auto-speak mode
     */
    public setAutoSpeak(enabled: boolean): void {
        this.settings.autoSpeak = enabled;
        this.saveSettings();
    }

    /**
     * Set voice by ID
     */
    public setVoice(voiceId: string): void {
        this.settings.voiceId = voiceId;
        this.saveSettings();
    }

    /**
     * Set speech rate (0.5 to 2.0)
     */
    public setRate(rate: number): void {
        this.settings.rate = Math.max(0.5, Math.min(2.0, rate));
        this.saveSettings();
    }

    /**
     * Set speech pitch (0 to 2.0)
     */
    public setPitch(pitch: number): void {
        this.settings.pitch = Math.max(0, Math.min(2.0, pitch));
        this.saveSettings();
    }

    /**
     * Set volume (0 to 1.0)
     */
    public setVolume(volume: number): void {
        this.settings.volume = Math.max(0, Math.min(1.0, volume));
        this.saveSettings();
    }

    /**
     * Register callback for speaking state changes
     */
    public onSpeakingChangeCallback(callback: (speaking: boolean) => void): void {
        this.onSpeakingChange = callback;
    }

    /**
     * Clean text for speech (remove emojis, markdown, etc.)
     */
    private cleanTextForSpeech(text: string): string {
        return text
            // Remove emojis
            .replace(/[\u{1F300}-\u{1F9FF}]/gu, '')
            // Remove markdown bold/italic
            .replace(/\*\*(.+?)\*\*/g, '$1')
            .replace(/\*(.+?)\*/g, '$1')
            // Remove special characters
            .replace(/[✓✗⚠️❌]/g, '')
            // Clean whitespace
            .trim();
    }

    /**
     * Save settings to localStorage
     */
    private saveSettings(): void {
        try {
            localStorage.setItem('tts-settings', JSON.stringify(this.settings));
        } catch (e) {
            console.error('Failed to save TTS settings:', e);
        }
    }

    /**
     * Load settings from localStorage
     */
    private loadSettings(): void {
        try {
            const stored = localStorage.getItem('tts-settings');
            if (stored) {
                const parsed = JSON.parse(stored);
                this.settings = { ...this.settings, ...parsed };
            }
        } catch (e) {
            console.error('Failed to load TTS settings:', e);
        }
    }

    /**
     * Check if TTS is supported
     */
    public static isSupported(): boolean {
        return 'speechSynthesis' in window;
    }
}

// Singleton instance
let ttsInstance: TextToSpeechService | null = null;

export const getTTSService = (): TextToSpeechService => {
    if (!ttsInstance) {
        ttsInstance = new TextToSpeechService();
    }
    return ttsInstance;
};

export default getTTSService;
