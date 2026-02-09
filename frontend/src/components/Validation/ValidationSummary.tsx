import React, { useState } from 'react';

export interface SummaryCard {
  id: string;
  title: string;
  status: string;
  metric: string;
  details: string[];
  actionHint?: string;
}

interface ValidationSummaryProps {
  cards: SummaryCard[];
  wsConnected: boolean;
  progressLog: { label: string; value: string }[];
  activeTaskId: string | null;
  overallResult?: any;
}

export const ValidationSummary: React.FC<ValidationSummaryProps> = ({
  cards,
  wsConnected,
  progressLog,
  activeTaskId,
  overallResult,
}) => {
  const [expandedCard, setExpandedCard] = useState<string | null>(null);

  const toggleCard = (cardId: string) => {
    setExpandedCard(expandedCard === cardId ? null : cardId);
  };

  const logEndRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    // Only scroll if the log container is actually overflowing or user is near bottom
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [progressLog]);

  return (
    <aside className="summary-pane">
      <div className="summary-header">
        <h2 className="summary-title">Validation Summary</h2>
        <span
          className={[
            'status-chip',
            wsConnected ? 'status-chip--connected' : 'status-chip--disconnected',
          ].join(' ')}
        >
          {wsConnected ? 'Realtime link active' : 'Connecting...'}
        </span>
      </div>

      <div className="summary-grid">
        {cards.map((card) => {
          const isExpanded = expandedCard === card.id;
          const isProcessing = card.status === 'WAITING' || card.status === 'Thinking...' || card.status === 'Processing';
          const cardClasses = [
            'summary-card',
            isExpanded ? 'summary-card--expanded' : '',
            isProcessing ? 'summary-card-scanning' : ''
          ].filter(Boolean).join(' ');

          return (
            <article
              key={card.id}
              className={cardClasses}
              onClick={() => toggleCard(card.id)}
              style={{ cursor: 'pointer' }}
            >
              <div className="summary-card__header">
                <div className="summary-card__title">
                  <span>{card.title}</span>
                  <span className={`summary-card__status ${isProcessing ? 'text-accent animate-pulse' : ''}`}>
                    {card.status}
                  </span>
                </div>
                <div className="summary-card__top-row">
                  <div className="summary-card__metric">{card.metric}</div>
                  <div className="summary-card__chevron">
                    {isExpanded ? '▼' : '▶'}
                  </div>
                </div>
              </div>

              {isExpanded && (
                <div className="summary-card__details">
                  <div className="summary-card__meta">
                    {card.details[0]}
                    {card.details.length > 1 && (
                      <ul className="summary-card__list">
                        {card.details.slice(1).map((detail, index) => (
                          <li key={`${card.id}-detail-${index}`}>{detail}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                  {card.actionHint && (
                    <p className="summary-card__action">{card.actionHint}</p>
                  )}
                </div>
              )}
            </article>
          );
        })}
      </div>

      {overallResult && (
        <div className="validation-details">
          <h3 className="validation-details__title">Final Analysis</h3>
          <div className="validation-details__content">
            {/* Show a more user-friendly summary than just JSON */}
            {overallResult.confidence?.explanation && (
              <p className="text-sm text-gray-300 mb-2">{overallResult.confidence.explanation}</p>
            )}
            <details>
              <summary className="text-xs text-blue-400 cursor-pointer">View Raw Data</summary>
              <pre className="validation-details__json mt-2">
                {JSON.stringify(overallResult, null, 2)}
              </pre>
            </details>
          </div>
        </div>
      )}

      <div className="progress-log">
        <h3 className="text-xs uppercase tracking-wider text-gray-500 mb-2">Live Progress</h3>
        {progressLog.length > 0 ? (
          progressLog.map((entry, index) => (
            <div className="progress-log__item" key={`${entry.label}-${index}`}>
              <span className="progress-log__icon">{entry.value === 'Processing' || entry.value === 'Running' || entry.value.includes('Thinking') ? '⏳' : '✓'}</span>
              <div className="flex-1 ml-2">
                <p className="progress-log__message text-xs">{entry.label}</p>
                <span className="progress-log__value text-xs font-mono">{entry.value}</span>
              </div>
            </div>
          ))
        ) : (
          <p className="progress-log__message italic opacity-50">
            Waiting for input...
          </p>
        )}
        <div ref={logEndRef} />
      </div>
    </aside>
  );
};
