/**
 * Detection Dashboard Page
 * Main dashboard for suspicious behavior detection
 */

import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../../hooks/voshan/useWebSocket';
import { getAlerts, checkMLServiceHealth } from '../../services/voshan/detectionApi';
import RealTimeAlertDisplay from '../../components/voshan/RealTimeAlertDisplay';
import AlertCard from '../../components/voshan/AlertCard';
import './DetectionDashboard.css';

const DetectionDashboard = () => {
  const [mlServiceStatus, setMlServiceStatus] = useState(null);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState({
    total: 0,
    high: 0,
    medium: 0,
    low: 0,
  });

  const { isConnected } = useWebSocket({
    autoConnect: true,
    onAlert: (alert) => {
      // Update stats when new alert arrives
      updateStats();
    },
  });

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);

      // Check ML service health
      const health = await checkMLServiceHealth();
      setMlServiceStatus(health);

      // Load recent alerts
      const alertsResponse = await getAlerts({ page: 1, limit: 10 });
      if (alertsResponse.success) {
        setRecentAlerts(alertsResponse.data.alerts);
        updateStatsFromAlerts(alertsResponse.data.alerts);
      }
    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const updateStats = async () => {
    try {
      const response = await getAlerts({ limit: 1000 });
      if (response.success) {
        updateStatsFromAlerts(response.data.alerts);
      }
    } catch (error) {
      console.error('Error updating stats:', error);
    }
  };

  const updateStatsFromAlerts = (alerts) => {
    const newStats = {
      total: alerts.length,
      high: alerts.filter((a) => a.severity === 'HIGH').length,
      medium: alerts.filter((a) => a.severity === 'MEDIUM').length,
      low: alerts.filter((a) => a.severity === 'LOW').length,
    };
    setStats(newStats);
  };

  return (
    <div className="detection-dashboard">
      <div className="dashboard-header">
        <h1>🛡️ Suspicious Behavior Detection Dashboard</h1>
        <button className="btn-refresh" onClick={loadData} disabled={loading}>
          {loading ? '⏳ Loading...' : '🔄 Refresh'}
        </button>
      </div>

      {/* ML Service Status */}
      {mlServiceStatus && (
        <div className="ml-service-status">
          <h3>ML Service Status</h3>
          <div className="status-grid">
            <div className="status-item">
              <span className="status-label">Status:</span>
              <span
                className={`status-value ${
                  mlServiceStatus.healthy ? 'healthy' : 'unhealthy'
                }`}
              >
                {mlServiceStatus.healthy ? '✅ Healthy' : '❌ Unhealthy'}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">Model Loaded:</span>
              <span className="status-value">
                {mlServiceStatus.modelLoaded ? '✅ Yes' : '❌ No'}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">GPU Available:</span>
              <span className="status-value">
                {mlServiceStatus.gpuAvailable ? '✅ Yes' : '❌ No'}
              </span>
            </div>
            <div className="status-item">
              <span className="status-label">WebSocket:</span>
              <span className={`status-value ${isConnected ? 'connected' : 'disconnected'}`}>
                {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Statistics */}
      <div className="stats-section">
        <h3>Statistics</h3>
        <div className="stats-grid">
          <div className="stat-card total">
            <div className="stat-value">{stats.total}</div>
            <div className="stat-label">Total Alerts</div>
          </div>
          <div className="stat-card high">
            <div className="stat-value">{stats.high}</div>
            <div className="stat-label">High Severity</div>
          </div>
          <div className="stat-card medium">
            <div className="stat-value">{stats.medium}</div>
            <div className="stat-label">Medium Severity</div>
          </div>
          <div className="stat-card low">
            <div className="stat-value">{stats.low}</div>
            <div className="stat-label">Low Severity</div>
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="dashboard-content">
        <div className="dashboard-column">
          <h3>Recent Alerts</h3>
          <div className="recent-alerts">
            {loading ? (
              <div className="loading">Loading alerts...</div>
            ) : recentAlerts.length === 0 ? (
              <div className="no-alerts">No alerts found</div>
            ) : (
              recentAlerts.map((alert) => (
                <AlertCard key={alert._id || alert.alertId} alert={alert} />
              ))
            )}
          </div>
        </div>

        <div className="dashboard-column">
          <RealTimeAlertDisplay maxAlerts={10} />
        </div>
      </div>
    </div>
  );
};

export default DetectionDashboard;

