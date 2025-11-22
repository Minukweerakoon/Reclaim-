import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { devicesAPI, alertsAPI } from '../services/api';
import DeviceCard from '../components/DeviceCard';
import AlertCard from '../components/AlertCard';
import DeviceRegistration from '../components/DeviceRegistration';
import CampusMap from '../components/CampusMap';
import NewDeviceModal from '../components/NewDeviceModal';

const useMobileDetection = () => {
  const [isMobile, setIsMobile] = React.useState(false);
  
  React.useEffect(() => {
    const checkMobile = () => {
      const userAgent = navigator.userAgent.toLowerCase();
      const mobile = /mobile|android|iphone|ipad|windows phone/.test(userAgent);
      const smallScreen = window.innerWidth < 768;
      setIsMobile(mobile || smallScreen);
    };
    
    checkMobile();
    window.addEventListener('resize', checkMobile);
    
    return () => window.removeEventListener('resize', checkMobile);
  }, []);
  
  return isMobile;
};

const Dashboard = () => {
  const { user, isSecurity } = useAuth();
  const [devices, setDevices] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [activeTab, setActiveTab] = useState('devices');
  const [loading, setLoading] = useState(true);
  const [macDebugInfo, setMacDebugInfo] = useState(null);
  const [showNewDeviceModal, setShowNewDeviceModal] = useState(false);
  const [newDeviceInfo, setNewDeviceInfo] = useState(null);
  const [deviceCheckDone, setDeviceCheckDone] = useState(false);
  const isMobile = useMobileDetection();

  useEffect(() => {
    if (user) {
      loadData();
    }
  }, [user]);

  useEffect(() => {
    if (user && !deviceCheckDone) {
      checkForNewDevice();
    }
  }, [user, deviceCheckDone]);

  const checkForNewDevice = async () => {
    try {
      console.log('Checking for new device...');
      const response = await devicesAPI.checkNewDevice();
      console.log('New device check response:', response.data);
      
      if (response.data.is_new_device) {
        console.log('New device detected:', response.data.device_info);
        
        // If it's a mobile device, auto-register it immediately
        if (response.data.device_info.type === 'mobile') {
          console.log('Auto-registering mobile device...');
          await devicesAPI.autoRegisterMobile();
          console.log('Mobile device auto-registered');
          loadData();
        } else {
          // For laptops, show the modal
          setNewDeviceInfo(response.data.device_info);
          setShowNewDeviceModal(true);
        }
      } else {
        console.log('Device already registered');
      }
      setDeviceCheckDone(true);
    } catch (error) {
      console.error('Error checking for new device:', error);
      setDeviceCheckDone(true);
    }
  };

  const handleRegisterNewDevice = async (deviceName) => {
    try {
      console.log('Registering new device:', deviceName);
      const deviceData = {
        name: deviceName || newDeviceInfo.name
      };
      await devicesAPI.autoRegisterDevice(deviceData);
      setShowNewDeviceModal(false);
      setNewDeviceInfo(null);
      loadData();
    } catch (error) {
      console.error('Error registering new device:', error);
    }
  };

  const handleSkipNewDevice = () => {
    console.log('Skipping new device registration');
    setShowNewDeviceModal(false);
    setNewDeviceInfo(null);
  };

  const loadData = async () => {
    try {
      console.log('Loading dashboard data...');
      const [devicesResponse, alertsResponse] = await Promise.all([
        devicesAPI.getUserDevices(),
        alertsAPI.getAlerts()
      ]);
      
      setDevices(devicesResponse.data);
      setAlerts(alertsResponse.data);
      console.log('Data loaded successfully');
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDebugMacAddress = async () => {
    try {
      const response = await devicesAPI.debugMacAddress();
      setMacDebugInfo(response.data);
    } catch (error) {
      console.error('Error debugging MAC:', error);
    }
  };

  const handleUpdateStatus = async (deviceId, status) => {
    try {
      await devicesAPI.updateDeviceStatus(deviceId, status);
      loadData();
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  const handleUpdateLocation = async (deviceId) => {
    try {
      await devicesAPI.updateDeviceLocation(deviceId);
      loadData();
    } catch (error) {
      console.error('Error updating location:', error);
    }
  };

  const handleCheckAnomaly = async (deviceId, behavior) => {
    try {
      await devicesAPI.checkAnomaly(deviceId, behavior);
      loadData();
    } catch (error) {
      console.error('Error checking anomaly:', error);
    }
  };

  const handleResolveAlert = async (alertId) => {
    try {
      await alertsAPI.resolveAlert(alertId);
      loadData();
    } catch (error) {
      console.error('Error resolving alert:', error);
    }
  };

  const handleBlacklistDevice = async (deviceId) => {
    try {
      await alertsAPI.blacklistDevice(deviceId);
      loadData();
    } catch (error) {
      console.error('Error blacklisting device:', error);
    }
  };

  if (loading) {
    return <div style={styles.loading}>Loading...</div>;
  }

  const activeAlerts = alerts.filter(alert => !alert.resolved);
  const resolvedAlerts = alerts.filter(alert => alert.resolved);
  const autoDetectedDevice = devices.find(device => device.is_auto_detected);
  const mobileDevices = devices.filter(device => device.type === 'mobile');
  const laptopDevices = devices.filter(device => device.type === 'laptop');

  return (
    <div style={{
      ...styles.container,
      ...(isMobile ? styles.mobileContainer : {})
    }}>
      <NewDeviceModal
        isOpen={showNewDeviceModal}
        deviceInfo={newDeviceInfo}
        onRegister={handleRegisterNewDevice}
        onSkip={handleSkipNewDevice}
      />
      
      <div style={styles.welcomeSection}>
        <h2 style={isMobile ? styles.mobileTitle : {}}>Welcome back, {user.username}!</h2>
        <p style={isMobile ? styles.mobileSubtitle : {}}>Monitor your devices and stay protected</p>
        
        {autoDetectedDevice && (
          <div style={{
            ...styles.autoDetectedBanner,
            ...(isMobile ? styles.mobileAutoDetectedBanner : {})
          }}>
            <div>
              <strong>📱 Auto-detected {autoDetectedDevice.type}:</strong> {autoDetectedDevice.name}
            </div>
            <button 
              onClick={handleDebugMacAddress}
              style={styles.debugButton}
            >
              Debug
            </button>
          </div>
        )}
        
        {macDebugInfo && (
          <div style={styles.debugInfo}>
            <h4>Device Debug Info:</h4>
            <p><strong>Detected MAC:</strong> {macDebugInfo.detected_mac}</p>
            <p><strong>Source:</strong> {macDebugInfo.mac_source}</p>
            <p><strong>Device Type:</strong> {macDebugInfo.device_type}</p>
            <p><strong>System:</strong> {macDebugInfo.system_info?.system}</p>
            <button 
              onClick={() => setMacDebugInfo(null)}
              style={styles.closeButton}
            >
              Close
            </button>
          </div>
        )}
        
        <div style={{
          ...styles.stats,
          ...(isMobile ? styles.mobileStats : {})
        }}>
          <div style={styles.stat}>
            <h3>{devices.length}</h3>
            <p>Total Devices</p>
          </div>
          <div style={styles.stat}>
            <h3>{laptopDevices.length}</h3>
            <p>Laptops</p>
          </div>
          <div style={styles.stat}>
            <h3>{mobileDevices.length}</h3>
            <p>Mobiles</p>
          </div>
          <div style={styles.stat}>
            <h3>{activeAlerts.length}</h3>
            <p>Alerts</p>
          </div>
        </div>
      </div>

      <div style={{
        ...styles.tabs,
        ...(isMobile ? styles.mobileTabs : {})
      }}>
        <button 
          style={{
            ...styles.tab,
            ...(activeTab === 'devices' ? styles.activeTab : {}),
            ...(isMobile ? styles.mobileTab : {})
          }}
          onClick={() => setActiveTab('devices')}
        >
          📱 Devices ({devices.length})
        </button>
        <button 
          style={{
            ...styles.tab,
            ...(activeTab === 'alerts' ? styles.activeTab : {}),
            ...(isMobile ? styles.mobileTab : {})
          }}
          onClick={() => setActiveTab('alerts')}
        >
          🚨 Alerts ({activeAlerts.length})
        </button>
        <button 
          style={{
            ...styles.tab,
            ...(activeTab === 'map' ? styles.activeTab : {}),
            ...(isMobile ? styles.mobileTab : {})
          }}
          onClick={() => setActiveTab('map')}
        >
          🗺️ Live Map
        </button>
        <button 
          style={{
            ...styles.tab,
            ...(activeTab === 'register' ? styles.activeTab : {}),
            ...(isMobile ? styles.mobileTab : {})
          }}
          onClick={() => setActiveTab('register')}
        >
          ➕ Add Device
        </button>
      </div>

      <div style={styles.content}>
        {activeTab === 'devices' && (
          <div style={{
            ...styles.devicesGrid,
            ...(isMobile ? styles.mobileDevicesGrid : {})
          }}>
            {devices.length === 0 ? (
              <div style={styles.emptyState}>
                <h3>No devices registered</h3>
                <p>Register your first device to start monitoring</p>
              </div>
            ) : (
              devices.map(device => (
                <DeviceCard
                  key={device._id}
                  device={device}
                  onUpdateStatus={handleUpdateStatus}
                  onCheckAnomaly={handleCheckAnomaly}
                  onUpdateLocation={handleUpdateLocation}
                  isMobile={isMobile}
                />
              ))
            )}
          </div>
        )}

        {activeTab === 'alerts' && (
          <div>
            <h3 style={styles.sectionTitle}>Active Alerts</h3>
            {activeAlerts.length === 0 ? (
              <div style={styles.emptyState}>
                <p>No active alerts. All devices are safe.</p>
              </div>
            ) : (
              activeAlerts.map(alert => (
                <AlertCard
                  key={alert._id}
                  alert={alert}
                  onResolve={handleResolveAlert}
                  onBlacklist={handleBlacklistDevice}
                  isSecurity={isSecurity}
                  isMobile={isMobile}
                />
              ))
            )}

            {resolvedAlerts.length > 0 && (
              <>
                <h3 style={styles.sectionTitle}>Resolved Alerts</h3>
                {resolvedAlerts.map(alert => (
                  <AlertCard
                    key={alert._id}
                    alert={alert}
                    onResolve={handleResolveAlert}
                    onBlacklist={handleBlacklistDevice}
                    isSecurity={isSecurity}
                    isMobile={isMobile}
                  />
                ))}
              </>
            )}
          </div>
        )}

        {activeTab === 'map' && (
          <CampusMap 
            devices={devices} 
            alerts={activeAlerts} 
            onUpdateLocation={handleUpdateLocation}
            isMobile={isMobile}
          />
        )}

        {activeTab === 'register' && (
          <DeviceRegistration onDeviceRegistered={loadData} isMobile={isMobile} />
        )}
      </div>
    </div>
  );
};

const styles = {
  container: {
    padding: '2rem',
    maxWidth: '1200px',
    margin: '0 auto',
  },
  mobileContainer: {
    padding: '1rem',
  },
  loading: {
    textAlign: 'center',
    padding: '2rem',
    fontSize: '1.2rem',
  },
  welcomeSection: {
    marginBottom: '2rem',
  },
  mobileTitle: {
    fontSize: '1.3rem',
  },
  mobileSubtitle: {
    fontSize: '0.9rem',
  },
  autoDetectedBanner: {
    backgroundColor: '#dbeafe',
    color: '#1e40af',
    padding: '0.75rem 1rem',
    borderRadius: '4px',
    margin: '1rem 0',
    border: '1px solid #93c5fd',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  mobileAutoDetectedBanner: {
    padding: '0.5rem',
    fontSize: '0.8rem',
    flexDirection: 'column',
    gap: '0.5rem',
    textAlign: 'center',
  },
  debugButton: {
    backgroundColor: '#f59e0b',
    color: 'white',
    border: 'none',
    padding: '0.3rem 0.6rem',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.7rem',
  },
  debugInfo: {
    backgroundColor: '#f3f4f6',
    padding: '1rem',
    borderRadius: '4px',
    margin: '1rem 0',
    border: '1px solid #d1d5db',
  },
  closeButton: {
    backgroundColor: '#6b7280',
    color: 'white',
    border: 'none',
    padding: '0.3rem 0.6rem',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.7rem',
    marginTop: '0.5rem',
  },
  stats: {
    display: 'flex',
    gap: '1rem',
    marginTop: '1rem',
  },
  mobileStats: {
    gap: '0.5rem',
    flexWrap: 'wrap',
  },
  stat: {
    textAlign: 'center',
    padding: '1rem',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    flex: 1,
    minWidth: '80px',
  },
  tabs: {
    display: 'flex',
    gap: '0.5rem',
    marginBottom: '2rem',
    borderBottom: '1px solid #e5e7eb',
  },
  mobileTabs: {
    flexWrap: 'wrap',
    gap: '0.25rem',
  },
  tab: {
    padding: '0.75rem 1.5rem',
    border: 'none',
    backgroundColor: 'transparent',
    cursor: 'pointer',
    borderRadius: '4px 4px 0 0',
    fontSize: '0.9rem',
    flex: 1,
  },
  mobileTab: {
    padding: '0.5rem 0.75rem',
    fontSize: '0.8rem',
    minWidth: '80px',
  },
  activeTab: {
    backgroundColor: '#3b82f6',
    color: 'white',
  },
  content: {
    minHeight: '400px',
  },
  devicesGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
    gap: '1.5rem',
  },
  mobileDevicesGrid: {
    gridTemplateColumns: '1fr',
    gap: '1rem',
  },
  sectionTitle: {
    marginBottom: '1rem',
    color: '#1f2937',
  },
  emptyState: {
    textAlign: 'center',
    padding: '3rem',
    backgroundColor: 'white',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
    color: '#6b7280',
  },
};

export default Dashboard;