# Step 5: Real-time Features - Complete ✅

## Overview

Real-time features for suspicious behavior detection have been implemented using WebSocket (Socket.IO) for live alert broadcasting and a notification service for alert management.

## Features Implemented

### 1. WebSocket Service (`services/voshan/websocketService.js`)
- Real-time alert broadcasting to connected clients
- Camera-specific rooms for targeted alerts
- Connection management and health monitoring
- Client subscription management

### 2. Notification Service (`services/voshan/notificationService.js`)
- Alert notification system (extensible for email, SMS, push)
- Severity-based notification routing
- High-priority alert handling
- Logging for all notifications

### 3. WebSocket Controller (`controllers/voshan/websocketController.js`)
- WebSocket status endpoint
- Connection monitoring

### 4. Integration Updates
- Detection controller now broadcasts alerts via WebSocket
- Detection controller sends notifications for new alerts
- Server.js updated to initialize WebSocket server

## WebSocket Events

### Client → Server

#### Join Camera Room
```javascript
socket.emit('join-camera', 'CAM_001');
```

#### Leave Camera Room
```javascript
socket.emit('leave-camera', 'CAM_001');
```

#### Subscribe to All Alerts
```javascript
socket.emit('subscribe-alerts');
```

#### Unsubscribe from Alerts
```javascript
socket.emit('unsubscribe-alerts');
```

#### Ping (Health Check)
```javascript
socket.emit('ping');
```

### Server → Client

#### New Alert
```javascript
socket.on('new-alert', (alert) => {
  console.log('New alert:', alert);
  // {
  //   alertId: 'BAG_UNATTENDED_123_1234567890',
  //   type: 'BAG_UNATTENDED',
  //   severity: 'MEDIUM',
  //   timestamp: 1234567890,
  //   cameraId: 'CAM_001',
  //   details: { ... }
  // }
});
```

#### Joined Camera
```javascript
socket.on('joined-camera', (data) => {
  console.log('Joined camera:', data.cameraId);
});
```

#### Subscribed to Alerts
```javascript
socket.on('subscribed-alerts', (data) => {
  console.log('Subscribed:', data.success);
});
```

#### Pong (Response to Ping)
```javascript
socket.on('pong', (data) => {
  console.log('Pong received:', data.timestamp);
});
```

## API Endpoints

### WebSocket Status
```
GET /api/voshan/detection/websocket/status
```

Response:
```json
{
  "success": true,
  "data": {
    "enabled": true,
    "connectedClients": 3,
    "clientIds": ["socket-id-1", "socket-id-2", "socket-id-3"]
  }
}
```

## Frontend Integration Example

### Connect to WebSocket
```javascript
import { io } from 'socket.io-client';

const socket = io('http://localhost:5000', {
  path: '/api/voshan/socket.io'
});

// Subscribe to all alerts
socket.emit('subscribe-alerts');

// Listen for new alerts
socket.on('new-alert', (alert) => {
  console.log('New alert received:', alert);
  // Update UI, show notification, etc.
});

// Join specific camera room
socket.emit('join-camera', 'CAM_001');

// Listen for camera-specific alerts
socket.on('new-alert', (alert) => {
  if (alert.cameraId === 'CAM_001') {
    // Handle camera-specific alert
  }
});
```

## Configuration

### Environment Variables

Add to `.env`:
```env
NOTIFICATIONS_ENABLED=false  # Set to true to enable notifications
```

### WebSocket Path

WebSocket is available at:
```
ws://localhost:5000/api/voshan/socket.io
```

## Dependencies Added

- `socket.io` - WebSocket server implementation

## Notification Channels

Currently implemented:
- ✅ **Log** - Console logging (always enabled)

Placeholder for future implementation:
- 📧 **Email** - Email notifications (nodemailer, SendGrid, etc.)
- 📱 **SMS** - SMS notifications (Twilio, AWS SNS, etc.)
- 🔔 **Push** - Push notifications (Firebase Cloud Messaging, etc.)

## Alert Broadcasting Flow

1. **Alert Generated** → Detection controller receives alert from ML service
2. **Save to Database** → Alert saved to MongoDB
3. **Broadcast via WebSocket** → Alert broadcasted to all subscribed clients
4. **Send Notification** → Notification service sends alerts (if enabled)
5. **Camera-Specific Broadcast** → Alert also sent to camera-specific room

## Testing

### Test WebSocket Connection
```bash
# Using wscat (install: npm install -g wscat)
wscat -c ws://localhost:5000/api/voshan/socket.io

# In wscat:
> emit subscribe-alerts
> emit join-camera CAM_001
```

### Test Alert Broadcasting
1. Process a video that generates alerts
2. Check WebSocket connection receives alerts in real-time
3. Verify alerts are saved to database
4. Check console for notification logs

## Next Steps

1. **Frontend Integration** - Connect React frontend to WebSocket
2. **Notification Implementation** - Implement actual email/SMS/push services
3. **Alert Acknowledgment** - Add acknowledgment feature via WebSocket
4. **Video Clip Storage** - Store video evidence for alerts
5. **Dashboard** - Create real-time alert dashboard

## Notes

- WebSocket service is automatically initialized when server starts
- All alerts are broadcasted in real-time to connected clients
- Camera-specific rooms allow targeted alert delivery
- Notification service can be extended for production use
- All changes are in `voshan/` folders to keep separate from other features

