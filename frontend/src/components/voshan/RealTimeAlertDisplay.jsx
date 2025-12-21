/**
 * Real-time Alert Display Component
 * Shows real-time alerts from WebSocket
 */

import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../../hooks/voshan/useWebSocket';
import AlertCard from './AlertCard';
import './RealTimeAlertDisplay.css';

const RealTimeAlertDisplay = ({ maxAlerts = 10, onAlertClick }) => {
  const { isConnected, alerts, connectionError, clearAlerts } = useWebSocket({
    autoConnect: true,
  });

  const [displayAlerts, setDisplayAlerts] = useState([]);

  useEffect(() => {
    // Keep only the most recent alerts
    const recentAlerts = alerts.slice(0, maxAlerts);
    setDisplayAlerts(recentAlerts);
  }, [alerts, maxAlerts]);

  const handleDelete = async (alertId) => {
    // Remove from local state
    setDisplayAlerts((prev) => prev.filter((a) => a._id !== alertId && a.alertId !== alertId));
  };

  return (
    <div className="realtime-alert-display">
      <div className="realtime-alert-header">
        <h3>🔔 Real-time Alerts</h3>
        <div className="connection-status">
          <span
            className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}
          >
            {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
          </span>
          {displayAlerts.length > 0 && (
            <button className="btn-clear" onClick={clearAlerts}>
              Clear All
            </button>
          )}
        </div>
      </div>

      {connectionError && (
        <div className="connection-error">
          ⚠️ Connection Error: {connectionError}
        </div>
      )}

      {!isConnected && !connectionError && (
        <div className="connection-status-message">
          Connecting to WebSocket...
        </div>
      )}

      <div className="alerts-container">
        {displayAlerts.length === 0 ? (
          <div className="no-alerts">
            {isConnected ? 'No alerts yet. Waiting for detections...' : 'Not connected'}
          </div>
        ) : (
          displayAlerts.map((alert, index) => (
            <AlertCard
              key={alert.alertId || alert._id || index}
              alert={alert}
              onViewDetails={onAlertClick}
              onDelete={handleDelete}
            />
          ))
        )}
      </div>
    </div>
  );
};

export default RealTimeAlertDisplay;

