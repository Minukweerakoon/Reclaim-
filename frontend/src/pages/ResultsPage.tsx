import React, { useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useValidationStore } from '../store/useValidationStore';
import { CheckCircle, AlertTriangle, ArrowRight, Home, RefreshCw } from 'lucide-react';

export const ResultsPage: React.FC = () => {
    const navigate = useNavigate();
    const overallResult = useValidationStore((state) => state.validationState.overallResult);
    const textResult = useValidationStore((state) => state.validationState.textResult);
    const imageResult = useValidationStore((state) => state.validationState.imageResult);
    const voiceResult = useValidationStore((state) => state.validationState.voiceResult);
    const crossModal = useValidationStore((state) => state.validationState.crossModalPreview);

    // Derived values
    const confidence = overallResult?.confidence?.overall_confidence || 0;
    const isHighQuality = confidence >= 0.85;
    const isMediumQuality = confidence >= 0.70 && confidence < 0.85;

    // Actions
    const handleRetry = () => {
        useValidationStore.getState().resetStore();
        navigate('/validate');
    };

    const handleHome = () => {
        useValidationStore.getState().resetStore();
        navigate('/');
    };

    if (!overallResult) {
        return (
            <div className="results-page flex-center">
                <div className="text-center">
                    <p className="text-xl mb-4 text-slate-400">No results found.</p>
                    <button onClick={handleHome} className="btn-secondary">Return Home</button>
                </div>
            </div>
        );
    }

    return (
        <div className="results-page">
            <div className="results-container">

                {/* Header Card */}
                <div className={`results-header ${isHighQuality ? 'bg-success' : isMediumQuality ? 'bg-warning' : 'bg-error'}`}>
                    <div className="header-icon">
                        {isHighQuality || isMediumQuality ? <CheckCircle size={48} /> : <AlertTriangle size={48} />}
                    </div>
                    <div className="header-content">
                        <h1>{isHighQuality ? 'Validation Complete!' : 'Submission Needs Review'}</h1>
                        <p>
                            {isHighQuality
                                ? 'Your submission has been successfully validated and forwarded for matching.'
                                : 'Your submission confidence is lower than optimal. Review the issues below.'}
                        </p>
                    </div>
                    <div className="confidence-badge">
                        <span className="score">{Math.round(confidence * 100)}%</span>
                        <span className="label">Confidence</span>
                    </div>
                </div>

                {/* Breakdown Grid */}
                <div className="breakdown-grid">
                    {/* Scores */}
                    <div className="card score-card">
                        <h3>Breakdown</h3>
                        <div className="score-row">
                            <span>📷 Image Quality</span>
                            <span className="score-val">{imageResult ? Math.round(imageResult.overall_score * 100) : '--'}%</span>
                        </div>
                        <div className="score-row">
                            <span>📝 Description</span>
                            <span className="score-val">{textResult ? Math.round(textResult.overall_score * 100) : '--'}%</span>
                        </div>
                        <div className="score-row">
                            <span>🎤 Voice Analysis</span>
                            <span className="score-val">{voiceResult ? Math.round(voiceResult.overall_score * 100) : '--'}%</span>
                        </div>
                        <div className="score-row">
                            <span>🔗 Consistency</span>
                            <span className="score-val">{crossModal?.image_text?.similarity ? Math.round(crossModal.image_text.similarity * 100) : '--'}%</span>
                        </div>
                    </div>

                    {/* Next Steps */}
                    <div className="card actions-card">
                        <h3>What happens next?</h3>
                        <ul className="next-steps-list">
                            {isHighQuality ? (
                                <>
                                    <li>✓ Report forwarded to matching engine</li>
                                    <li>✓ Database search initiated</li>
                                    <li>✓ You will be notified via email on match</li>
                                </>
                            ) : (
                                <>
                                    <li>⚠️ Manual review required</li>
                                    <li>⚠️ Matching may be delayed</li>
                                    <li>💡 Tip: Upload a clearer photo for faster results</li>
                                </>
                            )}
                        </ul>
                    </div>
                </div>

                {/* Footer Actions */}
                <div className="results-footer">
                    <button onClick={handleHome} className="btn-secondary">
                        <Home size={18} /> Home
                    </button>
                    <button onClick={handleRetry} className="btn-primary">
                        {isHighQuality ? 'Report Another Item' : 'Improve & Retry'} <ArrowRight size={18} />
                    </button>
                </div>

            </div>

            <style>{`
                .results-page {
                    min-height: 100vh;
                    background: #0f172a;
                    padding: 2rem;
                    color: white;
                    display: flex;
                    justify-content: center;
                }
                .flex-center { align-items: center; }
                .results-container {
                    width: 100%;
                    max-width: 800px;
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                }
                
                /* Header */
                .results-header {
                    background: rgba(30, 41, 59, 0.5);
                    border: 1px solid rgba(255,255,255,0.1);
                    border-radius: 20px;
                    padding: 2.5rem;
                    display: flex;
                    align-items: center;
                    gap: 2rem;
                    position: relative;
                    overflow: hidden;
                }
                .bg-success { background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(6, 95, 70, 0.2)); border-color: rgba(16, 185, 129, 0.3); }
                .bg-warning { background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(180, 83, 9, 0.2)); border-color: rgba(245, 158, 11, 0.3); }
                .bg-error { background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(153, 27, 27, 0.2)); border-color: rgba(239, 68, 68, 0.3); }
                
                .header-content h1 { font-size: 1.8rem; font-weight: 700; margin-bottom: 0.5rem; }
                .header-content p { color: rgba(255,255,255,0.8); line-height: 1.5; }
                
                .confidence-badge {
                    margin-left: auto;
                    text-align: center;
                    background: rgba(0,0,0,0.2);
                    padding: 1rem;
                    border-radius: 12px;
                    min-width: 100px;
                }
                .confidence-badge .score { display: block; font-size: 2rem; font-weight: 800; }
                .confidence-badge .label { font-size: 0.75rem; text-transform: uppercase; opacity: 0.7; }

                /* Grid */
                .breakdown-grid {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1.5rem;
                }
                .card {
                    background: #1e293b;
                    border-radius: 16px;
                    padding: 1.5rem;
                    border: 1px solid #334155;
                }
                .card h3 { font-size: 1.1rem; font-weight: 600; margin-bottom: 1rem; color: #94a3b8; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }
                
                .score-row {
                    display: flex;
                    justify-content: space-between;
                    padding: 0.75rem 0;
                    border-bottom: 1px solid rgba(255,255,255,0.05);
                }
                .score-row:last-child { border-bottom: none; }
                .score-val { font-weight: 700; }
                
                .next-steps-list li {
                    margin-bottom: 0.75rem;
                    color: rgba(255,255,255,0.8);
                    font-size: 0.95rem;
                }
                
                /* Footer */
                .results-footer {
                    display: flex;
                    justify-content: space-between;
                    margin-top: 1rem;
                }
                .btn-primary, .btn-secondary {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    padding: 0.85rem 1.5rem;
                    border-radius: 10px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: all 0.2s;
                    font-size: 1rem;
                }
                .btn-primary { background: #3b82f6; color: white; border: none; }
                .btn-primary:hover { background: #2563eb; transform: translateY(-1px); }
                
                .btn-secondary { background: transparent; border: 1px solid #475569; color: #cbd5e1; }
                .btn-secondary:hover { background: rgba(255,255,255,0.05); color: white; }
                
                @media (max-width: 640px) {
                    .breakdown-grid { grid-template-columns: 1fr; }
                    .results-header { flex-direction: column; text-align: center; }
                    .confidence-badge { margin: 0 auto; width: 100%; }
                }
            `}</style>
        </div>
    );
};
