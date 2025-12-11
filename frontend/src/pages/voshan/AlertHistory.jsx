/**
 * Alert History Page
 * Displays historical alerts with filtering and pagination
 */

import React, { useState, useEffect } from 'react';
import { getAlerts, deleteAlert } from '../../services/voshan/detectionApi';
import AlertCard from '../../components/voshan/AlertCard';
import './AlertHistory.css';

const AlertHistory = () => {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    page: 1,
    limit: 20,
    type: '',
    severity: '',
    cameraId: '',
    startDate: '',
    endDate: '',
  });
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total: 0,
    pages: 0,
  });

  useEffect(() => {
    loadAlerts();
  }, [filters]);

  const loadAlerts = async () => {
    try {
      setLoading(true);
      const response = await getAlerts(filters);
      if (response.success) {
        setAlerts(response.data.alerts);
        setPagination(response.data.pagination);
      }
    } catch (error) {
      console.error('Error loading alerts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (field, value) => {
    setFilters((prev) => ({
      ...prev,
      [field]: value,
      page: 1, // Reset to first page on filter change
    }));
  };

  const handlePageChange = (newPage) => {
    setFilters((prev) => ({
      ...prev,
      page: newPage,
    }));
  };

  const handleDelete = async (alertId) => {
    if (window.confirm('Are you sure you want to delete this alert?')) {
      try {
        await deleteAlert(alertId);
        // Remove from local state
        setAlerts((prev) => prev.filter((a) => a._id !== alertId && a.alertId !== alertId));
        loadAlerts(); // Reload to update pagination
      } catch (error) {
        console.error('Error deleting alert:', error);
        alert('Failed to delete alert');
      }
    }
  };

  return (
    <div className="alert-history">
      <div className="alert-history-header">
        <h1>📋 Alert History</h1>
      </div>

      {/* Filters */}
      <div className="filters-section">
        <h3>Filters</h3>
        <div className="filters-grid">
          <div className="filter-item">
            <label>Type</label>
            <select
              value={filters.type}
              onChange={(e) => handleFilterChange('type', e.target.value)}
            >
              <option value="">All Types</option>
              <option value="BAG_UNATTENDED">Unattended Bag</option>
              <option value="LOITER_NEAR_UNATTENDED">Loitering</option>
              <option value="RUNNING">Running</option>
              <option value="OWNER_RETURNED">Owner Returned</option>
            </select>
          </div>

          <div className="filter-item">
            <label>Severity</label>
            <select
              value={filters.severity}
              onChange={(e) => handleFilterChange('severity', e.target.value)}
            >
              <option value="">All Severities</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
              <option value="INFO">Info</option>
            </select>
          </div>

          <div className="filter-item">
            <label>Camera ID</label>
            <input
              type="text"
              value={filters.cameraId}
              onChange={(e) => handleFilterChange('cameraId', e.target.value)}
              placeholder="Filter by camera"
            />
          </div>

          <div className="filter-item">
            <label>Start Date</label>
            <input
              type="date"
              value={filters.startDate}
              onChange={(e) => handleFilterChange('startDate', e.target.value)}
            />
          </div>

          <div className="filter-item">
            <label>End Date</label>
            <input
              type="date"
              value={filters.endDate}
              onChange={(e) => handleFilterChange('endDate', e.target.value)}
            />
          </div>

          <div className="filter-item">
            <label>Per Page</label>
            <select
              value={filters.limit}
              onChange={(e) => handleFilterChange('limit', parseInt(e.target.value))}
            >
              <option value="10">10</option>
              <option value="20">20</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
          </div>
        </div>

        <button className="btn-clear-filters" onClick={() => setFilters({
          page: 1,
          limit: 20,
          type: '',
          severity: '',
          cameraId: '',
          startDate: '',
          endDate: '',
        })}>
          Clear Filters
        </button>
      </div>

      {/* Alerts List */}
      <div className="alerts-section">
        {loading ? (
          <div className="loading">Loading alerts...</div>
        ) : alerts.length === 0 ? (
          <div className="no-alerts">No alerts found matching your filters</div>
        ) : (
          <>
            <div className="alerts-list">
              {alerts.map((alert) => (
                <AlertCard
                  key={alert._id || alert.alertId}
                  alert={alert}
                  onDelete={handleDelete}
                />
              ))}
            </div>

            {/* Pagination */}
            {pagination.pages > 1 && (
              <div className="pagination">
                <button
                  className="btn-page"
                  onClick={() => handlePageChange(pagination.page - 1)}
                  disabled={pagination.page === 1}
                >
                  ← Previous
                </button>
                <span className="page-info">
                  Page {pagination.page} of {pagination.pages} ({pagination.total} total)
                </span>
                <button
                  className="btn-page"
                  onClick={() => handlePageChange(pagination.page + 1)}
                  disabled={pagination.page >= pagination.pages}
                >
                  Next →
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default AlertHistory;

