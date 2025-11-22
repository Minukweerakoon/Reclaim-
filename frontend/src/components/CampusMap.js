import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { getStatusColor } from '../utils/helpers';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in react-leaflet
import L from 'leaflet';
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Component to auto-center map on user's device
const MapUpdater = ({ devices, onUpdateLocation }) => {
  const map = useMap();
  const [initialized, setInitialized] = useState(false);

  useEffect(() => {
    const autoDetectedDevice = devices.find(device => device.is_auto_detected);
    if (autoDetectedDevice && autoDetectedDevice.current_location) {
      const { latitude, longitude } = autoDetectedDevice.current_location;
      if (latitude && longitude) {
        map.setView([latitude, longitude], 16);
        setInitialized(true);
        
        // Auto-update location every 30 seconds for auto-detected device
        if (!initialized) {
          const interval = setInterval(() => {
            onUpdateLocation(autoDetectedDevice._id);
          }, 30000);
          
          return () => clearInterval(interval);
        }
      }
    }
  }, [devices, map, initialized, onUpdateLocation]);

  return null;
};

const CampusMap = ({ devices, alerts, onUpdateLocation }) => {
  // Default campus location (NYU as example)
  const defaultCenter = [40.7295, -73.9965];
  
  // Campus building locations for demo
  const campusBuildings = [
    { name: 'Library', position: [40.7295, -73.9965] },
    { name: 'Academic Building', position: [40.7300, -73.9970] },
    { name: 'Student Center', position: [40.7290, -73.9955] },
    { name: 'Sports Complex', position: [40.7310, -73.9980] },
    { name: 'Dormitory A', position: [40.7285, -73.9990] },
    { name: 'Dormitory B', position: [40.7320, -73.9945] },
  ];

  const getDeviceIcon = (device) => {
    const color = getStatusColor(device.status);
    const isAutoDetected = device.is_auto_detected;
    
    return L.divIcon({
      html: `
        <div style="
          background-color: ${color};
          width: ${isAutoDetected ? '25px' : '20px'};
          height: ${isAutoDetected ? '25px' : '20px'};
          border-radius: 50%;
          border: 3px solid white;
          box-shadow: 0 2px 6px rgba(0,0,0,0.3);
          position: relative;
        ">
          ${isAutoDetected ? '<div style="position: absolute; top: -2px; right: -2px; background: #3b82f6; width: 8px; height: 8px; border-radius: 50%; border: 1px solid white;"></div>' : ''}
        </div>
      `,
      className: 'custom-marker',
      iconSize: isAutoDetected ? [25, 25] : [20, 20],
    });
  };

  const handleUpdateLocation = (deviceId) => {
    if (onUpdateLocation) {
      onUpdateLocation(deviceId);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.mapContainer}>
        <MapContainer
          center={defaultCenter}
          zoom={16}
          style={styles.map}
          scrollWheelZoom={true}
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          
          <MapUpdater devices={devices} onUpdateLocation={handleUpdateLocation} />
          
          {/* Campus buildings */}
          {campusBuildings.map((building, index) => (
            <Marker key={index} position={building.position}>
              <Popup>
                <strong>{building.name}</strong>
                <br />
                Campus Building
              </Popup>
            </Marker>
          ))}
          
          {/* Device markers */}
          {devices.map(device => {
            if (!device.current_location) return null;
            
            const position = [
              device.current_location.latitude || defaultCenter[0],
              device.current_location.longitude || defaultCenter[1]
            ];

            return (
              <Marker
                key={device._id}
                position={position}
                icon={getDeviceIcon(device)}
              >
                <Popup>
                  <div style={styles.popup}>
                    <strong>{device.name}</strong>
                    {device.is_auto_detected && <span style={styles.autoBadge}> 🖥️ THIS DEVICE</span>}
                    <br />
                    <strong>Status:</strong> {device.status.toUpperCase()}
                    <br />
                    <strong>Type:</strong> {device.type}
                    <br />
                    <strong>Location:</strong> {device.current_location.area || 'Unknown'}
                    <br />
                    <strong>Accuracy:</strong> {device.current_location.accuracy || 'unknown'}
                    <br />
                    <small>Last updated: {new Date(device.last_seen).toLocaleTimeString()}</small>
                    <br />
                    {device.is_auto_detected && (
                      <button 
                        onClick={() => handleUpdateLocation(device._id)}
                        style={styles.updateButton}
                      >
                        Update Location Now
                      </button>
                    )}
                  </div>
                </Popup>
              </Marker>
            );
          })}
        </MapContainer>
      </div>

      <div style={styles.legend}>
        <h4>Live Map Legend</h4>
        <div style={styles.legendItem}>
          <div style={{...styles.statusDot, backgroundColor: '#10b981'}}></div>
          <span>Safe Device</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{...styles.statusDot, backgroundColor: '#f59e0b'}}></div>
          <span>Suspicious Device</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{...styles.statusDot, backgroundColor: '#ef4444'}}></div>
          <span>Stolen Device</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{...styles.statusDot, backgroundColor: '#6b7280'}}></div>
          <span>Offline Device</span>
        </div>
        <div style={styles.legendItem}>
          <div style={{...styles.statusDot, backgroundColor: '#3b82f6', width: '16px', height: '16px'}}>
            <div style={styles.autoDot}></div>
          </div>
          <span>This Device (Auto-tracked)</span>
        </div>
        
        <div style={styles.stats}>
          <h4>Live Tracking</h4>
          <p>Total Devices: {devices.length}</p>
          <p>Auto-tracked: {devices.filter(d => d.is_auto_detected).length}</p>
          <p>Active Alerts: {alerts.length}</p>
          <p>Last Update: {new Date().toLocaleTimeString()}</p>
        </div>

        <div style={styles.instructions}>
          <h4>How it works:</h4>
          <p>• System auto-detects your device on first load</p>
          <p>• Real location is tracked via IP geolocation</p>
          <p>• Map auto-centers on your current location</p>
          <p>• Location updates every 30 seconds</p>
        </div>
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    gap: '2rem',
    height: '600px',
  },
  mapContainer: {
    flex: 1,
    borderRadius: '8px',
    overflow: 'hidden',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  map: {
    height: '100%',
    width: '100%',
  },
  popup: {
    minWidth: '200px',
  },
  autoBadge: {
    color: '#3b82f6',
    fontWeight: 'bold',
    fontSize: '0.8rem',
  },
  updateButton: {
    backgroundColor: '#3b82f6',
    color: 'white',
    border: 'none',
    padding: '0.25rem 0.5rem',
    borderRadius: '4px',
    fontSize: '0.7rem',
    cursor: 'pointer',
    marginTop: '0.5rem',
  },
  legend: {
    width: '280px',
    backgroundColor: 'white',
    padding: '1.5rem',
    borderRadius: '8px',
    boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
  },
  legendItem: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    marginBottom: '0.5rem',
  },
  statusDot: {
    width: '12px',
    height: '12px',
    borderRadius: '50%',
    position: 'relative',
  },
  autoDot: {
    position: 'absolute',
    top: '-2px',
    right: '-2px',
    backgroundColor: '#3b82f6',
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    border: '1px solid white',
  },
  stats: {
    marginTop: '1.5rem',
    paddingTop: '1.5rem',
    borderTop: '1px solid #e5e7eb',
  },
  instructions: {
    marginTop: '1.5rem',
    paddingTop: '1.5rem',
    borderTop: '1px solid #e5e7eb',
    fontSize: '0.8rem',
    color: '#6b7280',
  },
};

export default CampusMap;