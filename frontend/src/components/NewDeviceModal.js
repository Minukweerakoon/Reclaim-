import React, { useState } from 'react';

const NewDeviceModal = ({ isOpen, deviceInfo, onRegister, onSkip }) => {
  const [deviceName, setDeviceName] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    onRegister(deviceName || deviceInfo.name);
  };

  const getDeviceIcon = () => {
    if (deviceInfo?.type === 'mobile') return '📱';
    if (deviceInfo?.type === 'laptop') return '💻';
    return '🔧';
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.modal}>
        <div style={styles.header}>
          <h2 style={styles.title}>New Device Detected!</h2>
          <p style={styles.subtitle}>We found a new device accessing your account</p>
        </div>
        
        <div style={styles.deviceInfo}>
          <div style={styles.deviceIcon}>{getDeviceIcon()}</div>
          <div style={styles.deviceDetails}>
            <h3 style={styles.deviceName}>{deviceInfo?.name}</h3>
            <p style={styles.deviceType}>{deviceInfo?.type} Device</p>
            <p style={styles.deviceMac}><strong>MAC:</strong> {deviceInfo?.mac_address}</p>
            <p style={styles.deviceLocation}><strong>Location:</strong> {deviceInfo?.location?.area}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.inputGroup}>
            <label style={styles.label}>Device Name</label>
            <input
              type="text"
              value={deviceName}
              onChange={(e) => setDeviceName(e.target.value)}
              placeholder={deviceInfo?.name}
              style={styles.input}
            />
          </div>

          <div style={styles.actions}>
            <button 
              type="submit" 
              style={styles.registerButton}
            >
              ✅ Add This Device
            </button>
            <button 
              type="button" 
              onClick={onSkip}
              style={styles.skipButton}
            >
              ❌ Skip for Now
            </button>
          </div>
        </form>

        <div style={styles.note}>
          <p><strong>Note:</strong> Adding this device will enable real-time tracking and security monitoring.</p>
        </div>
      </div>
    </div>
  );
};

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 1000,
    padding: '1rem',
  },
  modal: {
    backgroundColor: 'white',
    borderRadius: '12px',
    padding: '2rem',
    maxWidth: '500px',
    width: '100%',
    boxShadow: '0 10px 25px rgba(0, 0, 0, 0.2)',
  },
  header: {
    textAlign: 'center',
    marginBottom: '2rem',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: 'bold',
    color: '#1f2937',
    margin: '0 0 0.5rem 0',
  },
  subtitle: {
    color: '#6b7280',
    margin: 0,
  },
  deviceInfo: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
    backgroundColor: '#f9fafb',
    padding: '1.5rem',
    borderRadius: '8px',
    marginBottom: '2rem',
  },
  deviceIcon: {
    fontSize: '3rem',
  },
  deviceDetails: {
    flex: 1,
  },
  deviceName: {
    fontSize: '1.2rem',
    fontWeight: 'bold',
    margin: '0 0 0.25rem 0',
    color: '#1f2937',
  },
  deviceType: {
    color: '#3b82f6',
    fontWeight: 'bold',
    margin: '0 0 0.5rem 0',
  },
  deviceMac: {
    fontSize: '0.9rem',
    color: '#6b7280',
    margin: '0.25rem 0',
  },
  deviceLocation: {
    fontSize: '0.9rem',
    color: '#6b7280',
    margin: '0.25rem 0',
  },
  form: {
    marginBottom: '1.5rem',
  },
  inputGroup: {
    marginBottom: '1.5rem',
  },
  label: {
    display: 'block',
    marginBottom: '0.5rem',
    fontWeight: 'bold',
    color: '#374151',
  },
  input: {
    width: '100%',
    padding: '0.75rem',
    border: '1px solid #d1d5db',
    borderRadius: '6px',
    fontSize: '1rem',
  },
  actions: {
    display: 'flex',
    gap: '1rem',
  },
  registerButton: {
    flex: 1,
    padding: '0.75rem',
    backgroundColor: '#10b981',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '1rem',
    fontWeight: 'bold',
    cursor: 'pointer',
  },
  skipButton: {
    flex: 1,
    padding: '0.75rem',
    backgroundColor: '#6b7280',
    color: 'white',
    border: 'none',
    borderRadius: '6px',
    fontSize: '1rem',
    cursor: 'pointer',
  },
  note: {
    backgroundColor: '#fef3c7',
    padding: '1rem',
    borderRadius: '6px',
    border: '1px solid #f59e0b',
  },
};

export default NewDeviceModal;