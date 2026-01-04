/**
 * Alert Notification Component
 * Notification icon in header with popup to show real-time alerts
 */

import React, { useState, useEffect, useRef } from 'react';
import { useWebSocket } from '../../hooks/voshan/useWebSocket';
import AlertCard from './AlertCard';
import './AlertNotification.css';

const AlertNotification = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [unreadCount, setUnreadCount] = useState(0);
  const [alerts, setAlerts] = useState([]);
  const popupRef = useRef(null);

  const { isConnected, alerts: wsAlerts } = useWebSocket({
    autoConnect: true,
  });

  // Update alerts when WebSocket alerts change
  useEffect(() => {
    if (wsAlerts && wsAlerts.length > 0) {
      setAlerts(wsAlerts);
      // Increase unread count if popup is closed
      if (!isOpen) {
        setUnreadCount(wsAlerts.length);
      }
    }
  }, [wsAlerts, isOpen]);

  // Reset unread count when popup opens
  useEffect(() => {
    if (isOpen) {
      setUnreadCount(0);
    }
  }, [isOpen]);

  // Close popup when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (popupRef.current && !popupRef.current.contains(event.target)) {
        // Check if click is not on the notification icon
        const notificationIcon = event.target.closest('.notification-icon-wrapper');
        if (!notificationIcon) {
          setIsOpen(false);
        }
      }
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isOpen]);

  // Close popup on Escape key
  useEffect(() => {
    const handleEscape = (event) => {
      if (event.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen]);

  const togglePopup = () => {
    setIsOpen(!isOpen);
    if (!isOpen) {
      setUnreadCount(0);
    }
  };

  const handleDeleteAlert = (alertId) => {
    setAlerts((prev) => prev.filter((a) => a.alertId !== alertId && a._id !== alertId));
  };

  const handleClearAll = () => {
    setAlerts([]);
    setUnreadCount(0);
  };

  return (
    <div className="notification-container" ref={popupRef}>
      <button
        className="notification-icon-wrapper"
        onClick={togglePopup}
        aria-label="View alerts"
        aria-expanded={isOpen}
      >
        <div className="notification-icon">
          🔔
          {unreadCount > 0 && (
            <span className="notification-badge">{unreadCount > 99 ? '99+' : unreadCount}</span>
          )}
          {!isConnected && <span className="notification-offline-indicator" title="WebSocket disconnected" />}
        </div>
      </button>

      {isOpen && (
        <div className="notification-popup">
          <div className="notification-popup-header">
            <h3>🔔 Real-time Alerts</h3>
            <div className="notification-popup-actions">
              {alerts.length > 0 && (
                <button className="btn-clear-all" onClick={handleClearAll} title="Clear all alerts">
                  Clear All
                </button>
              )}
              <button className="btn-close-popup" onClick={() => setIsOpen(false)} aria-label="Close">
                ✕
              </button>
            </div>
          </div>

          <div className="notification-popup-content">
            {!isConnected ? (
              <div className="notification-status-message">
                <span className="status-indicator disconnected">🔴</span>
                WebSocket disconnected. Alerts will appear when connected.
              </div>
            ) : alerts.length === 0 ? (
              <div className="notification-empty">
                No alerts yet. Waiting for detections...
              </div>
            ) : (
              <div className="notification-alerts-list">
                {alerts.slice(0, 10).map((alert, index) => (
                  <AlertCard
                    key={alert.alertId || alert._id || index}
                    alert={alert}
                    onDelete={handleDeleteAlert}
                  />
                ))}
                {alerts.length > 10 && (
                  <div className="notification-more-alerts">
                    +{alerts.length - 10} more alerts
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AlertNotification;

