/**
 * Alert Card Component
 * Displays a single alert in a card format
 */

import React, { useMemo } from 'react';
import { getAlertFrameImageUrl } from '../../services/voshan/detectionApi';
import './AlertCard.css';

// List of available placeholder images
const PLACEHOLDER_IMAGES = [
  '/assets/placeholder-frame-1.png',
  '/assets/placeholder-frame-2.png',
  '/assets/placeholder-frame-3.png',
  '/assets/placeholder-frame-4.png',
];

/**
 * Get a random placeholder image based on alert ID or frame number
 * This ensures the same alert always gets the same placeholder (deterministic)
 */
const getRandomPlaceholder = (alertId, frameNumber) => {
  // Use alert ID or frame number as seed for consistent selection
  let seed;
  if (alertId) {
    // Convert string ID to number by summing character codes
    if (typeof alertId === 'string') {
      seed = alertId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    } else {
      seed = alertId;
    }
  } else if (frameNumber !== undefined && frameNumber !== null) {
    seed = frameNumber;
  } else {
    // Fallback to random if no ID or frame number
    seed = Math.floor(Math.random() * 1000000);
  }
  const index = Math.abs(seed) % PLACEHOLDER_IMAGES.length;
  return PLACEHOLDER_IMAGES[index];
};

const AlertCard = ({ alert, onViewDetails, onDelete, frameSnapshot }) => {
  const frameFilename = alert.frame_image || alert.frameImage;
  const imageSrc = useMemo(() => {
    if (frameFilename) {
      const url = getAlertFrameImageUrl(frameFilename);
      if (url) return url;
    }
    if (frameSnapshot) return frameSnapshot;
    return getRandomPlaceholder(alert._id || alert.alertId, alert.frame);
  }, [frameFilename, alert._id, alert.alertId, alert.frame, frameSnapshot]);

  const fallbackSrc = frameSnapshot || getRandomPlaceholder(alert._id || alert.alertId, alert.frame);
  const isPlaceholder = !frameFilename && !frameSnapshot;

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
        {/* Show frame image or placeholder */}
        <div className="alert-snapshot">
          <img
            key={frameFilename ? `frame-${frameFilename}` : 'placeholder'}
            src={imageSrc}
            alt={`Frame ${alert.frame || 'N/A'} - ${getTypeLabel(alert.type)}`}
            className={`snapshot-image ${isPlaceholder ? 'placeholder-image' : ''}`}
            title={isPlaceholder ? `Frame snapshot not available for frame ${alert.frame || 'N/A'}` : `Frame ${alert.frame || 'N/A'}`}
            onError={(e) => {
              const target = e.target;
              if (target.src !== fallbackSrc) {
                target.src = fallbackSrc;
                target.className = 'snapshot-image placeholder-image';
              }
            }}
          />
        </div>
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

