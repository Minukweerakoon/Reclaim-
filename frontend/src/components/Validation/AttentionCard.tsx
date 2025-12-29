import React from 'react';
import './AttentionCard.css';

interface AttentionCardProps {
    heatmapUrl?: string;
    explanation: string;
    topRegions: Array<{ region: string; score: number }>;
    attentionScores?: number[];
    error?: string;
}

export const AttentionCard: React.FC<AttentionCardProps> = ({
    heatmapUrl,
    explanation,
    topRegions,
    error
}) => {
    if (error) {
        return (
            <div className="attention-card error">
                <h3>🔍 Visual Attention Analysis</h3>
                <p className="error-message">{error}</p>
            </div>
        );
    }

    return (
        <div className="attention-card">
            <h3>🔍 Visual Attention Analysis</h3>

            {/* Heatmap Image */}
            {heatmapUrl && (
                <div className="heatmap-container">
                    <img
                        src={heatmapUrl}
                        alt="Attention Heatmap"
                        className="heatmap-image"
                    />
                    <p className="caption">
                        <span className="red-indicator">Red areas:</span> High attention |
                        <span className="blue-indicator"> Blue:</span> Low attention
                    </p>
                </div>
            )}

            {/* Top Regions */}
            {topRegions && topRegions.length > 0 && (
                <div className="top-regions">
                    <h4>Most Important Regions:</h4>
                    <div className="regions-list">
                        {topRegions.slice(0, 3).map((region, idx) => (
                            <div key={idx} className="region-item">
                                <span className="region-name">{region.region}</span>
                                <div className="score-bar">
                                    <div
                                        className="score-fill"
                                        style={{ width: `${region.score * 100}%` }}
                                    />
                                </div>
                                <span className="score-value">
                                    {(region.score * 100).toFixed(0)}%
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Explanation */}
            {explanation && (
                <div className="explanation">
                    <p>{explanation}</p>
                </div>
            )}
        </div>
    );
};

export default AttentionCard;
