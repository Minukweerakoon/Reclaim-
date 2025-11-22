import React from 'react';
import { getStatusColor } from '../utils/helpers';

const DeviceCard = ({ device, onUpdateStatus, onCheckAnomaly, onUpdateLocation, isMobile }) => {
  const statusColor = getStatusColor(device.status);

  const handleSimulateMovement = () => {
    // Simulate device movement for demo
    const behavior = {
      action: 'connect',
      area: 'Library', // Different area to trigger anomaly
      time_of_day: new Date().getHours(),
    };
    
    onCheckAnomaly(device._id, behavior);
  };

  const handleSafeStatus = () => {
    onUpdateStatus(device._id, 'safe');
  };

  const handleOfflineStatus = () => {
    onUpdateStatus(device._id, 'offline');
  };

  const handleUpdateRealLocation = () => {
    onUpdateLocation(device._id);
  };

  const getMacSourceInfo = () => {
    if (device.system_info?.mac_source === 'detected') {
      return <span style={styles.macVerified}>✓ Verified MAC</span>;
    } else if (device.system_info?.mac_source === 'generated') {
      return <span style={styles.macGenerated}>⚠ Generated ID</span>;
    }
    return null;
  };

  const getDeviceIcon = () => {
    if (device.type === 'mobile') return '📱';
    if (device.type === 'laptop') return '💻';
    return '🔧';
  };

  return (
    <div style={{
      ...styles.card,
      ...(isMobile ? styles.mobileCard : {})
    }}>
      <div style={styles.cardHeader}>
        <div style={styles.deviceTitle}>
          <span style={styles.deviceIcon}>{getDeviceIcon()}</span>
          <h3 style={styles.deviceName}>{device.name}</h3>
        </div>
        <span 
          style={{
            ...styles.status,
            backgroundColor: statusColor
          }}
        >
          {device.status.toUpperCase()}
        </span>
      </div>
      
      <div style={styles.deviceInfo}>
        <p>
          <strong>Type:</strong> {device.type}
          {device.is_auto_detected && <span style={styles.autoBadge}> 🎯 Auto</span>}
        </p>
        <p>
          <strong>MAC:</strong> {isMobile ? `${device.mac_address.substring(0, 8)}...` : device.mac_address}
          {getMacSourceInfo()}
        </p>
        <p><strong>Last Seen:</strong> {new Date(device.last_seen).toLocaleString()}</p>
        {device.current_location && (
          <div>
            <p><strong>Location:</strong> {device.current_location.area}</p>
            <p style={styles.locationDetails}>
              <small>
                {device.current_location.accuracy} • {device.current_location.method}
                {device.current_location.campus_zone && ` • ${device.current_location.campus_zone}`}
              </small>
            </p>
          </div>
        )}
      </div>

      <div style={{
        ...styles.actions,
        ...(isMobile ? styles.mobileActions : {})
      }}>
        <button 
          onClick={handleSafeStatus}
          style={styles.safeButton}
          disabled={device.status === 'safe'}
        >
          Safe
        </button>
        
        <button 
          onClick={handleOfflineStatus}
          style={styles.offlineButton}
          disabled={device.status === 'offline'}
        >
          Offline
        </button>
        
        <button 
          onClick={handleUpdateRealLocation}
          style={styles.locationButton}
        >
          📍 Locate
        </button>
        
        <button 
          onClick={handleSimulateMovement}
          style={styles.anomalyButton}
        >
          Test Alert
        </button>
      </div>
    </div>
  );
};

const styles = {
  card: {
    backgroundColor: 'white',
    borderRadius: '8px',
    padding: '1.5rem',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    border: '1px solid #e5e7eb',
  },
  mobileCard: {
    padding: '1rem',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '1rem',
    gap: '0.5rem',
  },
  deviceTitle: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    flex: 1,
  },
  deviceIcon: {
    fontSize: '1.2rem',
  },
  deviceName: {
    fontSize: '1.1rem',
    fontWeight: 'bold',
    margin: 0,
    color: '#1f2937',
    wordBreak: 'break-word',
  },
  status: {
    padding: '0.25rem 0.75rem',
    borderRadius: '20px',
    fontSize: '0.7rem',
    fontWeight: 'bold',
    color: 'white',
    whiteSpace: 'nowrap',
  },
  deviceInfo: {
    marginBottom: '1rem',
  },
  deviceInfo: {
    margin: '0.25rem 0',
    fontSize: '0.9rem',
    color: '#6b7280',
    wordBreak: 'break-word',
  },
  autoBadge: {
    color: '#3b82f6',
    fontWeight: 'bold',
    fontSize: '0.7rem',
    marginLeft: '0.5rem',
  },
  macVerified: {
    color: '#10b981',
    fontWeight: 'bold',
    fontSize: '0.6rem',
    marginLeft: '0.5rem',
    backgroundColor: '#d1fae5',
    padding: '0.1rem 0.3rem',
    borderRadius: '4px',
  },
  macGenerated: {
    color: '#f59e0b',
    fontWeight: 'bold',
    fontSize: '0.6rem',
    marginLeft: '0.5rem',
    backgroundColor: '#fef3c7',
    padding: '0.1rem 0.3rem',
    borderRadius: '4px',
  },
  locationDetails: {
    fontSize: '0.65rem',
    color: '#9ca3af',
    marginTop: '0.2rem',
  },
  actions: {
    display: 'flex',
    gap: '0.5rem',
    flexWrap: 'wrap',
  },
  mobileActions: {
    gap: '0.25rem',
  },
  safeButton: {
    backgroundColor: '#10b981',
    color: 'white',
    border: 'none',
    padding: '0.4rem 0.8rem',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.7rem',
    flex: 1,
    minWidth: '60px',
  },
  offlineButton: {
    backgroundColor: '#6b7280',
    color: 'white',
    border: 'none',
    padding: '0.4rem 0.8rem',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.7rem',
    flex: 1,
    minWidth: '60px',
  },
  locationButton: {
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    padding: '0.4rem 0.8rem',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.7rem',
    flex: 1,
    minWidth: '60px',
  },
  anomalyButton: {
    backgroundColor: '#f59e0b',
    color: 'white',
    border: 'none',
    padding: '0.4rem 0.8rem',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.7rem',
    flex: 1,
    minWidth: '60px',
  },
};

export default DeviceCard;