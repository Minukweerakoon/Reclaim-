import React, { useState } from 'react';
import { devicesAPI } from '../services/api';

const DeviceRegistration = ({ onDeviceRegistered }) => {
  const [formData, setFormData] = useState({
    name: '',
    mac_address: '',
    type: 'laptop'
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      await devicesAPI.registerDevice(formData);
      setMessage('Device registered successfully!');
      setFormData({ name: '', mac_address: '', type: 'laptop' });
      onDeviceRegistered(); // Refresh the device list
    } catch (error) {
      setMessage(error.response?.data?.error || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.container}>
      <h3 style={styles.title}>Register New Device</h3>
      
      <form onSubmit={handleSubmit} style={styles.form}>
        <div style={styles.inputGroup}>
          <label style={styles.label}>Device Name</label>
          <input
            type="text"
            value={formData.name}
            onChange={(e) => setFormData({...formData, name: e.target.value})}
            placeholder="e.g., My Laptop, John's Phone"
            style={styles.input}
            required
          />
        </div>

        <div style={styles.inputGroup}>
          <label style={styles.label}>MAC Address</label>
          <input
            type="text"
            value={formData.mac_address}
            onChange={(e) => setFormData({...formData, mac_address: e.target.value})}
            placeholder="e.g., 00:1B:44:11:3A:B7"
            style={styles.input}
            required
          />
        </div>

        <div style={styles.inputGroup}>
          <label style={styles.label}>Device Type</label>
          <select
            value={formData.type}
            onChange={(e) => setFormData({...formData, type: e.target.value})}
            style={styles.input}
          >
            <option value="laptop">Laptop</option>
            <option value="mobile">Mobile Phone</option>
            <option value="tablet">Tablet</option>
            <option value="other">Other</option>
          </select>
        </div>

        <button 
          type="submit" 
          style={styles.button}
          disabled={loading}
        >
          {loading ? 'Registering...' : 'Register Device'}
        </button>
      </form>

      {message && (
        <div style={{
          ...styles.message,
          backgroundColor: message.includes('success') ? '#d1fae5' : '#fee2e2',
          color: message.includes('success') ? '#065f46' : '#991b1b'
        }}>
          {message}
        </div>
      )}

      <div style={styles.demoInfo}>
        <h4>Demo MAC Addresses:</h4>
        <p>• 00:1B:44:11:3A:B7</p>
        <p>• 00:1A:2B:3C:4D:5E</p>
        <p>• 08:00:27:12:34:56</p>
      </div>
    </div>
  );
};

const styles = {
  container: {
    backgroundColor: 'white',
    padding: '2rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    maxWidth: '500px',
  },
  title: {
    marginBottom: '1.5rem',
    color: '#1f2937',
  },
  form: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1.5rem',
  },
  inputGroup: {
    display: 'flex',
    flexDirection: 'column',
    gap: '0.5rem',
  },
  label: {
    fontWeight: 'bold',
    color: '#374151',
    fontSize: '0.9rem',
  },
  input: {
    padding: '0.75rem',
    border: '1px solid #d1d5db',
    borderRadius: '4px',
    fontSize: '1rem',
  },
  button: {
    padding: '0.75rem',
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    borderRadius: '4px',
    fontSize: '1rem',
    cursor: 'pointer',
  },
  message: {
    padding: '0.75rem',
    borderRadius: '4px',
    marginTop: '1rem',
    textAlign: 'center',
  },
  demoInfo: {
    marginTop: '2rem',
    padding: '1rem',
    backgroundColor: '#f9fafb',
    borderRadius: '4px',
    fontSize: '0.8rem',
  },
};

export default DeviceRegistration;