import React from 'react';
import { ScoreCircle } from './ScoreCircle';

interface PlausibilityResult {
    plausibility_score: number;
    valid: boolean;
    location_probability: number;
    time_probability: number;
    explanation: string;
    suggestions: string[];
    confidence_level: string;
    normalized_inputs: {
        item: string;
        location: string;
        time: string;
    };
}

interface PlausibilityCardProps {
    result: PlausibilityResult | null;
    loading?: boolean;
}

export const PlausibilityCard: React.FC<PlausibilityCardProps> = ({ result, loading }) => {
    if (loading) {
        return (
            <div className="plausibility-card plausibility-loading">
                <div className="plausibility-header">
                    <span className="plausibility-icon">🧠</span>
                    <span className="plausibility-title">Spatial-Temporal Analysis</span>
                </div>
                <div className="plausibility-loading-text">Analyzing plausibility...</div>
            </div>
        );
    }

    if (!result) return null;

    const score = result.plausibility_score;
    const getConfidenceColor = () => {
        if (score >= 0.8) return '#22c55e'; // Green
        if (score >= 0.6) return '#84cc16'; // Lime
        if (score >= 0.4) return '#eab308'; // Yellow
        if (score >= 0.2) return '#f97316'; // Orange
        return '#ef4444'; // Red
    };

    const getConfidenceLabel = () => {
        switch (result.confidence_level) {
            case 'very_high': return '✅ Very Plausible';
            case 'high': return '✅ Plausible';
            case 'moderate': return '⚠️ Somewhat Unusual';
            case 'low': return '⚠️ Unusual';
            case 'very_low': return '❌ Highly Unusual';
            default: return '❓ Unknown';
        }
    };

    return (
        <div
            className="plausibility-card"
            style={{ borderLeftColor: getConfidenceColor() }}
        >
            <div className="plausibility-header">
                <div className="plausibility-title-section">
                    <span className="plausibility-icon">🧠</span>
                    <span className="plausibility-title">Spatial-Temporal Analysis</span>
                    <span
                        className="plausibility-badge"
                        style={{ backgroundColor: getConfidenceColor() }}
                    >
                        {getConfidenceLabel()}
                    </span>
                </div>
                <ScoreCircle score={score} size={52} />
            </div>

            <div className="plausibility-explanation">
                {result.explanation}
            </div>

            <div className="plausibility-details">
                <div className="plausibility-detail-item">
                    <span className="detail-label">📍 Location Match:</span>
                    <span className="detail-value">{(result.location_probability * 100).toFixed(0)}%</span>
                </div>
                <div className="plausibility-detail-item">
                    <span className="detail-label">⏰ Time Match:</span>
                    <span className="detail-value">
                        {result.time_probability != null
                            ? `${(result.time_probability * 100).toFixed(0)}%`
                            : 'N/A (not specified)'}
                    </span>
                </div>
                <div className="plausibility-detail-item">
                    <span className="detail-label">🏷️ Item:</span>
                    <span className="detail-value">{result.normalized_inputs.item}</span>
                </div>
                <div className="plausibility-detail-item">
                    <span className="detail-label">📍 Location:</span>
                    <span className="detail-value">{result.normalized_inputs.location}</span>
                </div>
                <div className="plausibility-detail-item">
                    <span className="detail-label">🕐 Time:</span>
                    <span className="detail-value">{result.normalized_inputs.time}</span>
                </div>
            </div>

            {result.suggestions && result.suggestions.length > 0 && (
                <div className="plausibility-suggestions">
                    <div className="suggestions-title">💡 Suggestions:</div>
                    <ul className="suggestions-list">
                        {result.suggestions.map((suggestion, index) => (
                            <li key={index}>{suggestion}</li>
                        ))}
                    </ul>
                </div>
            )}

            <div className="plausibility-footer">
                <span className="research-badge">🎓 Novel Feature #1: Bayesian Plausibility Model</span>
            </div>
        </div>
    );
};
