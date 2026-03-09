/**
 * Notification Service
 * Handles alert notifications (email, SMS, push, etc.)
 * Currently implements basic logging - can be extended for actual notifications
 */

class NotificationService {
  constructor() {
    this.enabled = process.env.NOTIFICATIONS_ENABLED === 'true' || false;
  }

  /**
   * Send notification for alert
   * @param {Object} alert - Alert object
   * @param {Array} channels - Notification channels ['email', 'sms', 'push']
   */
  async sendNotification(alert, channels = ['log']) {
    if (!this.enabled) {
      console.log('📧 Notifications disabled, skipping notification');
      return;
    }

    const notification = {
      alertId: alert.alertId,
      type: alert.type,
      severity: alert.severity,
      timestamp: alert.timestamp,
      cameraId: alert.cameraId,
      message: this.formatMessage(alert)
    };

    for (const channel of channels) {
      try {
        switch (channel) {
          case 'email':
            await this.sendEmail(notification);
            break;
          case 'sms':
            await this.sendSMS(notification);
            break;
          case 'push':
            await this.sendPush(notification);
            break;
          case 'log':
          default:
            this.logNotification(notification);
            break;
        }
      } catch (error) {
        console.error(`❌ Error sending ${channel} notification:`, error);
      }
    }
  }

  /**
   * Format alert message for notifications
   * @param {Object} alert - Alert object
   * @returns {String} Formatted message
   */
  formatMessage(alert) {
    const severityEmoji = {
      'LOW': '🟢',
      'MEDIUM': '🟡',
      'HIGH': '🔴',
      'INFO': 'ℹ️'
    };

    const typeMessages = {
      'BAG_UNATTENDED': 'Unattended item detected',
      'LOITER_NEAR_UNATTENDED': 'Person loitering near unattended item',
      'RUNNING': 'Person running detected',
      'OWNER_RETURNED': 'Owner returned to unattended item',
      'INTERACTION_WITH_BAG': 'Person interacting with unattended item'
    };

    const emoji = severityEmoji[alert.severity] || '⚠️';
    let message = typeMessages[alert.type] || 'Suspicious behavior detected';
    const itemType = alert.itemType || alert.details?.item_type;
    if (itemType) {
      const item = String(itemType).replace(/_/g, ' ');
      message = message.replace('item', item);
    }
    const camera = alert.cameraId ? ` (Camera: ${alert.cameraId})` : '';

    return `${emoji} ${message}${camera}`;
  }

  /**
   * Log notification (default channel)
   * @param {Object} notification - Notification object
   */
  logNotification(notification) {
    console.log('📧 NOTIFICATION:', notification.message);
    console.log('   Alert ID:', notification.alertId);
    console.log('   Type:', notification.type);
    console.log('   Severity:', notification.severity);
    if (notification.cameraId) {
      console.log('   Camera:', notification.cameraId);
    }
  }

  /**
   * Send email notification (placeholder - implement with email service)
   * @param {Object} notification - Notification object
   */
  async sendEmail(notification) {
    // TODO: Implement email sending (e.g., using nodemailer, SendGrid, etc.)
    console.log('📧 EMAIL (not implemented):', notification.message);
  }

  /**
   * Send SMS notification (placeholder - implement with SMS service)
   * @param {Object} notification - Notification object
   */
  async sendSMS(notification) {
    // TODO: Implement SMS sending (e.g., using Twilio, AWS SNS, etc.)
    console.log('📱 SMS (not implemented):', notification.message);
  }

  /**
   * Send push notification (placeholder - implement with push service)
   * @param {Object} notification - Notification object
   */
  async sendPush(notification) {
    // TODO: Implement push notifications (e.g., using Firebase Cloud Messaging, etc.)
    console.log('🔔 PUSH (not implemented):', notification.message);
  }

  /**
   * Send high-priority alert notification
   * @param {Object} alert - Alert object
   */
  async sendHighPriorityAlert(alert) {
    if (alert.severity === 'HIGH') {
      await this.sendNotification(alert, ['log', 'email', 'sms']);
    } else {
      await this.sendNotification(alert, ['log']);
    }
  }
}

module.exports = new NotificationService();

