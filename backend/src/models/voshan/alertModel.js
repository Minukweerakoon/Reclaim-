/**
 * Alert Model
 * MongoDB schema for suspicious behavior alerts
 */

const mongoose = require('mongoose');

const alertSchema = new mongoose.Schema({
  alertId: {
    type: String,
    required: true,
    unique: true,
    index: true
  },
  type: {
    type: String,
    required: true,
    enum: ['BAG_UNATTENDED', 'LOITER_NEAR_UNATTENDED', 'RUNNING', 'OWNER_RETURNED'],
    index: true
  },
  severity: {
    type: String,
    required: true,
    enum: ['LOW', 'MEDIUM', 'HIGH', 'INFO'],
    index: true
  },
  timestamp: {
    type: Date,
    required: true,
    index: true
  },
  frame: {
    type: Number,
    required: true
  },
  cameraId: {
    type: String,
    index: true,
    default: null
  },
  details: {
    type: mongoose.Schema.Types.Mixed,
    required: true
  },
  videoInfo: {
    outputVideo: String,
    logJson: String,
    logCsv: String
  },
  acknowledged: {
    type: Boolean,
    default: false
  },
  acknowledgedAt: {
    type: Date,
    default: null
  },
  acknowledgedBy: {
    type: String,
    default: null
  }
}, {
  timestamps: true // Adds createdAt and updatedAt
});

// Indexes for efficient querying
alertSchema.index({ timestamp: -1 });
alertSchema.index({ cameraId: 1, timestamp: -1 });
alertSchema.index({ type: 1, timestamp: -1 });
alertSchema.index({ severity: 1, timestamp: -1 });

// Virtual for alert age in seconds
alertSchema.virtual('ageSeconds').get(function() {
  return Math.floor((Date.now() - this.timestamp.getTime()) / 1000);
});

// Method to acknowledge alert
alertSchema.methods.acknowledge = function(userId) {
  this.acknowledged = true;
  this.acknowledgedAt = new Date();
  this.acknowledgedBy = userId;
  return this.save();
};

const Alert = mongoose.model('Alert', alertSchema, 'voshan_alerts');

module.exports = Alert;

