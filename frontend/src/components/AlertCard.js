import React from 'react';
import { formatDate } from '../utils/helpers';

const AlertCard = ({ alert, onResolve, isSecurity, onBlacklist }) => {
  const isResolved = alert.resolved;

  return (
    <div style={{
      ...styles.alert,
      borderLeftColor: isResolved ? '#10b981' : '#ef4444'
    }}>
      <div style={styles.alertHeader}>
        <h4 style={styles.alertTitle}>
          {alert.alert_type === 'suspicious_behavior' ? '🚨 Suspicious Behavior' : '⚠️ Device Alert'}
        </h4>
        <span style={styles.alertStatus}>
          {isResolved ? 'RESOLVED' : 'ACTIVE'}
        </span>
      </div>
      
      <p style={styles.alertMessage}>{alert.message}</p>
      
      <div style={styles.alertDetails}>
        <p><strong>Device:</strong> {alert.device_name}</p>
        <p><strong>Time:</strong> {formatDate(alert.timestamp)}</p>
        {alert.location && (
          <p><strong>Location:</strong> {alert.location.area}</p>
        )}
      </div>

      {!isResolved && (
        <div style={styles.alertActions}>
          <button 
            onClick={() => onResolve(alert._id)}
            style={styles.resolveButton}
          >
            Mark Resolved
          </button>
          
          {isSecurity && (
            <button 
              onClick={() => onBlacklist(alert.device_id)}
              style={styles.blacklistButton}
            >
              Blacklist Device
            </button>
          )}
        </div>
      )}
    </div>
  );
};

const styles = {
  alert: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '1.5rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    borderLeft: '4px solid',
    marginBottom: '1rem',
  },
  alertHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '1rem',
  },
  alertTitle: {
    fontSize: '1.1rem',
    fontWeight: 'bold',
    margin: 0,
    color: '#1f2937',
  },
  alertStatus: {
    fontSize: '0.8rem',
    fontWeight: 'bold',
    color: '#6b7280',
    textTransform: 'uppercase',
  },
  alertMessage: {
    marginBottom: '1rem',
    color: '#374151',
    fontSize: '0.95rem',
  },
  alertDetails: {
    backgroundColor: '#f9fafb',
    padding: '1rem',
    borderRadius: '4px',
    marginBottom: '1rem',
  },
  alertDetails : {
    margin: '0.25rem 0',
    fontSize: '0.9rem',
    color: '#6b7280',
  },
  alertActions: {
    display: 'flex',
    gap: '0.5rem',
    flexWrap: 'wrap',
  },
  resolveButton: {
    backgroundColor: '#10b981',
    color: 'white',
    border: 'none',
    padding: '0.5rem 1rem',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.8rem',
  },
  blacklistButton: {
    backgroundColor: '#ef4444',
    color: 'white',
    border: 'none',
    padding: '0.5rem 1rem',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.8rem',
  },
};

export default AlertCard;