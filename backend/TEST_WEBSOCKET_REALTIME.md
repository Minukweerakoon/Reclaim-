# Testing WebSocket Real-Time Updates

This guide shows you how to verify that WebSocket real-time alerts are working correctly.

## Quick Test Methods

### Method 1: Browser Console (Easiest)

1. **Open your frontend** at `http://localhost:3000/voshan/detection`
2. **Open Browser DevTools** (F12)
3. **Go to Console tab**
4. **Check connection status** - You should see:
   ```
   🔌 Connecting to WebSocket: http://localhost:5000/api/voshan/socket.io
   ✅ WebSocket connected: [socket-id]
   🔔 Subscribed to alerts: true
   ```

5. **Monitor for alerts** - When an alert is generated, you'll see:
   ```
   📢 New alert received: {type: "BAG_UNATTENDED", ...}
   ```

### Method 2: Upload a Video to Generate Alerts

1. **Go to Upload page**: `http://localhost:3000/voshan/upload`
2. **Upload a video** that contains bags and people
3. **Watch the browser console** while processing
4. **After processing completes**, alerts should appear in:
   - Real-time Alert Display component
   - Browser console (if using Detection Dashboard)

### Method 3: Use the Test Script

Run the test script to manually trigger an alert:

```powershell
cd backend
node test-websocket-alert.js
```

This will:
- Connect to WebSocket
- Send a test alert
- Verify it's received

## Step-by-Step Verification

### Step 1: Verify WebSocket Connection

**Check Backend Status:**
```powershell
Invoke-WebRequest -Uri "http://localhost:5000/api/voshan/detection/websocket/status"
```

Expected response:
```json
{
  "success": true,
  "data": {
    "enabled": true,
    "connectedClients": 1,
    "clientIds": ["socket-id-here"]
  }
}
```

**Check Frontend Connection:**
1. Open browser console (F12)
2. Look for: `✅ WebSocket connected: [socket-id]`
3. Check Detection Dashboard - should show "🟢 Connected"

### Step 2: Monitor Real-Time Updates

**In Browser Console:**
- Watch for `📢 New alert received:` messages
- These appear when alerts are broadcast

**In Detection Dashboard:**
- Real-time Alert Display section should show alerts
- Alerts appear automatically without page refresh

### Step 3: Test Alert Generation

**Option A: Upload Video**
1. Upload a video with suspicious behavior
2. Wait for processing to complete
3. Alerts should appear in real-time display

**Option B: Manual Test (using script)**
```powershell
node backend/test-websocket-alert.js
```

## Browser DevTools Network Tab

1. **Open DevTools** (F12)
2. **Go to Network tab**
3. **Filter by "WS"** (WebSocket)
4. **Click on the WebSocket connection**
5. **Go to "Messages" tab**
6. **You'll see:**
   - Outgoing: `subscribe-alerts`, `ping`
   - Incoming: `subscribed-alerts`, `new-alert`, `pong`

## Real-Time Alert Display Component

The `RealTimeAlertDisplay` component automatically:
- Connects to WebSocket on mount
- Subscribes to all alerts
- Displays alerts in real-time
- Shows connection status

**Location**: Detection Dashboard (`/voshan/detection`)

## Testing Checklist

- [ ] WebSocket connects successfully (check console)
- [ ] Connection status shows "🟢 Connected" in UI
- [ ] Backend shows connected client count > 0
- [ ] Browser console shows "Subscribed to alerts: true"
- [ ] Upload video and process it
- [ ] Alerts appear in Real-Time Alert Display
- [ ] Alerts appear in browser console
- [ ] No page refresh needed to see new alerts

## Troubleshooting

### No Alerts Appearing

1. **Check WebSocket Connection:**
   - Browser console should show "✅ WebSocket connected"
   - Backend status should show `connectedClients > 0`

2. **Check Alert Generation:**
   - Upload a video and verify alerts are created
   - Check backend logs for: `📢 Broadcasted alert: [type]`

3. **Check Subscription:**
   - Browser console should show: `🔔 Subscribed to alerts: true`

### Alerts Not Broadcasting

1. **Check Backend Logs:**
   - Look for: `📢 Broadcasted alert: [type]`
   - If missing, alerts aren't being broadcast

2. **Check WebSocket Service:**
   - Verify `websocketService.io` is not null
   - Check for initialization errors

### Connection Drops

1. **Check Network Tab:**
   - Look for WebSocket disconnection reasons
   - Common: `transport close`, `ping timeout`

2. **Check Reconnection:**
   - Should see: `🔄 WebSocket reconnected after X attempts`
   - If not, check connection settings

## Expected Behavior

**When Working Correctly:**

1. **On Page Load:**
   - WebSocket connects automatically
   - Subscribes to alerts
   - Shows "🟢 Connected" status

2. **When Alert Generated:**
   - Alert appears in Real-Time Display (no refresh)
   - Browser console logs the alert
   - Alert persists until cleared

3. **On Disconnection:**
   - Automatically attempts to reconnect
   - Shows "🔴 Disconnected" during reconnection
   - Reconnects and re-subscribes automatically

## Manual Test Commands

### Test WebSocket Connection
```javascript
// In browser console
const socket = io('http://localhost:5000', {
  path: '/api/voshan/socket.io'
});

socket.on('connect', () => {
  console.log('Connected:', socket.id);
  socket.emit('subscribe-alerts');
});

socket.on('new-alert', (alert) => {
  console.log('Alert received:', alert);
});
```

### Check Connection Status
```powershell
# PowerShell
Invoke-WebRequest -Uri "http://localhost:5000/api/voshan/detection/websocket/status" | ConvertFrom-Json
```

## Next Steps

Once WebSocket is working:
1. Upload videos to generate real alerts
2. Monitor real-time alert display
3. Check Alert History for saved alerts
4. Test with multiple browser tabs (all should receive alerts)

