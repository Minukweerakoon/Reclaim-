import React from 'react';

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
          {wsConnected ? 'Realtime link active' : 'Realtime link offline'}
        </span>
      </div>

      <div className="summary-grid">
        {cards.map((card) => (
          <article key={card.id} className="summary-card">
            <div className="summary-card__title">
              <span>{card.title}</span>
              <span className="summary-card__status">{card.status}</span>
            </div>
            <div className="summary-card__metric">{card.metric}</div>
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
          </article>
        ))}
      </div>

      {overallResult && (
        <div className="validation-details">
          <h3 className="validation-details__title">Full response JSON</h3>
          <pre className="validation-details__json">
            {JSON.stringify(overallResult, null, 2)}
          </pre>
        </div>
      )}

      <div className="progress-log">
        {progressLog.length > 0 ? (
          progressLog.map((entry) => (
            <div className="progress-log__item" key={entry.label}>
              <p className="progress-log__message">{entry.label}</p>
              <span className="progress-log__value">{entry.value}</span>
            </div>
          ))
        ) : (
          <p className="progress-log__message">
            Progress updates will appear here as you share more evidence.
          </p>
        )}
        {activeTaskId && (
          <p className="progress-log__message">
            Tracking realtime task: {activeTaskId}
          </p>
        )}
      </div>
    </aside>
  );
};
