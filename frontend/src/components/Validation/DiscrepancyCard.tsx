import React from 'react';
import './AttentionCard.css';

interface DiscrepancyDetail {
    has_mismatch: boolean;
    explanation: string;
    severity?: 'low' | 'medium' | 'high';
    suggestions?: string[];
}

interface XAIExplanation {
    has_discrepancy: boolean;
    explanation: string;
    details?: {
        brand?: DiscrepancyDetail;
        location?: DiscrepancyDetail;
        condition?: DiscrepancyDetail;
    };
}

interface DiscrepancyCardProps {
    result?: XAIExplanation;
}

export const DiscrepancyCard: React.FC<DiscrepancyCardProps> = ({ result }) => {
    if (!result || !result.has_discrepancy) {
        return null;
    }

    const details = result.details;

    return (
        <div className="attention-card warning" style={{ borderLeft: '4px solid #f59e0b', background: '#fffbeb', color: '#78350f' }}>
            <h3 style={{ color: '#78350f' }}>⚠️ Discrepancy Analysis</h3>

            <p style={{ marginBottom: '1rem', fontWeight: 500, color: '#374151' }}>{result.explanation}</p>

            <div className="discrepancy-list">
                {/* Brand Mismatch */}
                {details?.brand?.has_mismatch && (
                    <div className="discrepancy-item" style={{ background: 'rgba(255,255,255,0.6)', padding: '0.75rem', borderRadius: '6px', marginBottom: '0.5rem', border: '1px solid rgba(0,0,0,0.05)' }}>
                        <div className="d-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.9rem' }}>
                            <span>🏷️</span>
                            <span>Brand Mismatch</span>
                            <span style={{ marginLeft: 'auto', fontSize: '0.7rem', textTransform: 'uppercase', background: '#fef3c7', color: '#92400e', padding: '2px 6px', borderRadius: '4px' }}>Medium</span>
                        </div>
                        <p style={{ margin: 0, fontSize: '0.85rem', color: '#4b5563' }}>{details.brand.explanation}</p>
                    </div>
                )}

                {/* Location Mismatch */}
                {details?.location?.has_mismatch && (
                    <div className="discrepancy-item" style={{ background: 'rgba(255,255,255,0.6)', padding: '0.75rem', borderRadius: '6px', marginBottom: '0.5rem', border: '1px solid rgba(0,0,0,0.05)' }}>
                        <div className="d-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.9rem' }}>
                            <span>📍</span>
                            <span>Location Inconsistency</span>
                            <span style={{ marginLeft: 'auto', fontSize: '0.7rem', textTransform: 'uppercase', background: '#fee2e2', color: '#991b1b', padding: '2px 6px', borderRadius: '4px' }}>High</span>
                        </div>
                        <p style={{ margin: 0, fontSize: '0.85rem', color: '#4b5563' }}>{details.location.explanation}</p>
                    </div>
                )}

                {/* Condition Mismatch */}
                {details?.condition?.has_mismatch && (
                    <div className="discrepancy-item" style={{ background: 'rgba(255,255,255,0.6)', padding: '0.75rem', borderRadius: '6px', marginBottom: '0.5rem', border: '1px solid rgba(0,0,0,0.05)' }}>
                        <div className="d-header" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem', fontWeight: 600, fontSize: '0.9rem' }}>
                            <span>✨</span>
                            <span>Condition Mismatch</span>
                            <span style={{ marginLeft: 'auto', fontSize: '0.7rem', textTransform: 'uppercase', background: '#fef3c7', color: '#92400e', padding: '2px 6px', borderRadius: '4px' }}>Medium</span>
                        </div>
                        <p style={{ margin: 0, fontSize: '0.85rem', color: '#4b5563' }}>{details.condition.explanation}</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default DiscrepancyCard;
