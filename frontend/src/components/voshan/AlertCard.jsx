/**
 * Alert Card Component
 * Displays a single alert in a card format
 */

import React from 'react';
import './AlertCard.css';

const AlertCard = ({ alert, onViewDetails, onDelete, frameSnapshot }) => {
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'HIGH':
        return '#dc3545'; // Red
      case 'MEDIUM':
        return '#ffc107'; // Yellow
      case 'LOW':
        return '#28a745'; // Green
      case 'INFO':
        return '#17a2b8'; // Blue
      default:
        return '#6c757d'; // Gray
    }
  };

  const getTypeLabel = (type) => {
    const labels = {
      BAG_UNATTENDED: 'Unattended Bag',
      LOITER_NEAR_UNATTENDED: 'Loitering Detected',
      RUNNING: 'Running Detected',
      OWNER_RETURNED: 'Owner Returned',
    };
    return labels[type] || type;
  };

  const formatTimestamp = (timestamp) => {
    if (typeof timestamp === 'number') {
      return new Date(timestamp * 1000).toLocaleString();
    }
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="alert-card" style={{ borderLeftColor: getSeverityColor(alert.severity) }}>
      <div className="alert-card-header">
        <div className="alert-card-title">
          <span className="alert-type">{getTypeLabel(alert.type)}</span>
          <span
            className="alert-severity"
            style={{ backgroundColor: getSeverityColor(alert.severity) }}
          >
            {alert.severity}
          </span>
        </div>
        <div className="alert-card-actions">
          {onViewDetails && (
            <button
              className="btn-view"
              onClick={() => onViewDetails(alert)}
              title="View Details"
            >
              👁️
            </button>
          )}
          {onDelete && (
            <button
              className="btn-delete"
              onClick={() => onDelete(alert._id || alert.alertId)}
              title="Delete Alert"
            >
              🗑️
            </button>
          )}
        </div>
      </div>
      <div className="alert-card-body">
        {/* Frame Snapshot */}
        {frameSnapshot ? (
          <div className="alert-snapshot">
            <img
              src={frameSnapshot}
              alt={`Frame ${alert.frame || 'N/A'} - ${getTypeLabel(alert.type)}`}
              className="snapshot-image"
              title={`Frame ${alert.frame || 'N/A'}`}
              onError={(e) => {
                console.error('[AlertCard] Frame image failed to load:', {
                  frameNumber: alert.frame,
                  frameSnapshotLength: frameSnapshot?.length,
                  error: e
                });
              }}
            />
          </div>
        ) : (
          // Debug: Show when frame snapshot is not available
          alert.frame !== undefined && alert.frame !== null && (
            <div style={{ fontSize: '12px', color: '#999', fontStyle: 'italic', marginBottom: '8px' }}>
              ⚠️ Frame snapshot not available for frame {alert.frame}
            </div>
          )
        )}
        <div className="alert-info">
          <span className="alert-time">
            🕐 {formatTimestamp(alert.timestamp)}
          </span>
          {alert.cameraId && (
            <span className="alert-camera">📹 {alert.cameraId}</span>
          )}
          {alert.frame && (
            <span className="alert-frame">🎬 Frame: {alert.frame}</span>
          )}
        </div>
        {alert.details && (
          <div className="alert-details">
            {alert.details.duration_seconds && (
              <div>⏱️ Duration: {alert.details.duration_seconds.toFixed(1)}s</div>
            )}
            {alert.details.dwell_time_seconds && (
              <div>⏱️ Dwell Time: {alert.details.dwell_time_seconds.toFixed(1)}s</div>
            )}
            {alert.details.speed && (
              <div>🏃 Speed: {alert.details.speed.toFixed(1)} px/s</div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertCard;

