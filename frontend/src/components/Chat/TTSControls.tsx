/**
 * TTS Controls Component
 * Provides UI for controlling Text-to-Speech settings
 */

import React, { useState } from 'react'
import { useTTS } from '../../hooks/useTTS'

export const TTSControls: React.FC = () => {
    const { settings, voices, isSupported, toggleAutoSpeak, setVoice, setRate } = useTTS()
    const [isExpanded, setIsExpanded] = useState(false)

    if (!isSupported) {
        return (
            <div className="tts-controls tts-controls--unsupported">
                <span>🔇 Voice responses not supported in this browser</span>
            </div>
        )
    }

    if (!settings) {
        return null
    }

    // Filter to English voices
    const englishVoices = voices.filter(v => v.lang.startsWith('en'))

    return (
        <div className="tts-controls">
            {/* Collapsible header */}
            <div className="tts-controls__header" onClick={() => setIsExpanded(!isExpanded)}>
                <span className="tts-controls__title">
                    🔊 Voice Responses
                </span>
                <span className="tts-controls__toggle">
                    {isExpanded ? '▼' : '▶'}
                </span>
            </div>

            {/* Settings panel (collapsible) */}
            {isExpanded && (
                <div className="tts-controls__panel">
                    {/* Auto-speak toggle */}
                    <div className="tts-control-item">
                        <label className="tts-control-label">
                            <input
                                type="checkbox"
                                checked={settings.autoSpeak}
                                onChange={toggleAutoSpeak}
                                className="tts-checkbox"
                            />
                            <span>Auto-speak responses</span>
                        </label>
                        <p className="tts-control-hint">
                            Automatically read bot messages aloud
                        </p>
                    </div>

                    {/* Voice selection */}
                    <div className="tts-control-item">
                        <label className="tts-control-label" htmlFor="tts-voice-select">
                            Voice
                        </label>
                        <select
                            id="tts-voice-select"
                            value={settings.voiceId}
                            onChange={(e) => setVoice(e.target.value)}
                            className="tts-select"
                        >
                            {englishVoices.map((voice) => (
                                <option key={voice.id} value={voice.id}>
                                    {voice.name}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Speech rate */}
                    <div className="tts-control-item">
                        <label className="tts-control-label" htmlFor="tts-rate-slider">
                            Speed: {settings.rate.toFixed(1)}x
                        </label>
                        <input
                            id="tts-rate-slider"
                            type="range"
                            min="0.5"
                            max="2"
                            step="0.1"
                            value={settings.rate}
                            onChange={(e) => setRate(parseFloat(e.target.value))}
                            className="tts-slider"
                        />
                        <div className="tts-slider-labels">
                            <span>Slow</span>
                            <span>Fast</span>
                        </div>
                    </div>

                    {/* Info text */}
                    <div className="tts-control-info">
                        <p>
                            💡 Click the 🔈 button on any bot message to hear it spoken aloud.
                        </p>
                    </div>
                </div>
            )}
        </div>
    )
}
