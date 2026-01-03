# WebSocket Connection Troubleshooting Guide

## Quick Check

1. **Check WebSocket Status**:
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

2. **Check Browser Console**:
   - Open browser DevTools (F12)
   - Go to Console tab
   - Look for WebSocket connection messages:
     - `✅ WebSocket connected` - Success
     - `❌ WebSocket connection error` - Connection failed
     - `🔌 Connecting to WebSocket: ...` - Connection attempt

3. **Check Backend Terminal**:
   - Look for: `📡 Client connected: [socket-id]`
   - If you see: `⚠️ WebSocket not initialized` - WebSocket service not started

## Common Issues

### Issue 1: WebSocket Shows "Disconnected" in Frontend

**Symptoms:**
- Frontend shows "🔴 Disconnected" status
- No alerts received in real-time
- Browser console shows connection errors

**Solutions:**

1. **Verify Backend is Running**:
   ```powershell
   # Check if backend is running
   Invoke-WebRequest -Uri "http://localhost:5000/api/health"
   ```

2. **Check WebSocket Service Initialization**:
   - Backend terminal should show: `✅ WebSocket service initialized for Voshan detection`
   - If not, restart backend server

3. **Check CORS Configuration**:
   - Verify `CORS_ORIGIN` in `backend/.env` matches frontend URL
   - Default: `CORS_ORIGIN=http://localhost:3000`

4. **Check Frontend Environment Variables**:
   - Verify `VITE_API_URL` in `frontend/.env`
   - Should be: `VITE_API_URL=http://localhost:5000/api`

5. **Clear Browser Cache and Refresh**:
   - Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)

### Issue 2: Connection Error in Browser Console

**Error Messages:**
- `xhr poll error` - Connection failed
- `websocket error` - WebSocket upgrade failed
- `timeout` - Connection timed out

**Solutions:**

1. **Check Firewall/Antivirus**:
   - Temporarily disable to test if blocking WebSocket connections

2. **Check Network Tab**:
   - Open DevTools → Network tab
   - Filter by "WS" (WebSocket)
   - Check if connection attempts are being made
   - Look for failed requests

3. **Try Different Transport**:
   - The hook uses both `websocket` and `polling` transports
   - If WebSocket fails, it should fall back to polling
   - Check if polling works

### Issue 3: WebSocket Connects but Disconnects Immediately

**Symptoms:**
- Connection succeeds briefly
- Then immediately disconnects
- Reconnection attempts fail

**Solutions:**

1. **Check Server Timeout Settings**:
   - Verify `server.timeout` in `backend/server.js`
   - Should be set to handle long connections

2. **Check Keep-Alive Settings**:
   - Verify `keepAliveTimeout` and `headersTimeout` in `backend/server.js`

3. **Check Backend Logs**:
   - Look for disconnection reasons
   - Common: `transport close`, `ping timeout`

### Issue 4: No Alerts Received Even When Connected

**Symptoms:**
- WebSocket shows "🟢 Connected"
- But no alerts appear in real-time display

**Solutions:**

1. **Verify Subscription**:
   - Check browser console for: `🔔 Subscribed to alerts: true`
   - If not, subscription failed

2. **Check Alert Broadcasting**:
   - Backend should log: `📢 Broadcasted alert: [type]`
   - If not, alerts aren't being broadcast

3. **Test Alert Generation**:
   - Upload a video that generates alerts
   - Check if alerts are saved to database
   - Check if alerts are broadcast via WebSocket

## Manual Connection Test

### Test WebSocket Connection Directly

1. **Using Browser Console**:
   ```javascript
   // Open browser console on frontend page
   const socket = io('http://localhost:5000', {
     path: '/api/voshan/socket.io',
     transports: ['websocket', 'polling']
   });
   
   socket.on('connect', () => {
     console.log('Connected:', socket.id);
     socket.emit('subscribe-alerts');
   });
   
   socket.on('new-alert', (alert) => {
     console.log('Alert received:', alert);
   });
   ```

2. **Using wscat (if installed)**:
   ```powershell
   # Install wscat: npm install -g wscat
   wscat -c ws://localhost:5000/api/voshan/socket.io
   ```

## Configuration Checklist

- [ ] Backend server is running on port 5000
- [ ] WebSocket service initialized (check backend logs)
- [ ] CORS_ORIGIN in backend/.env matches frontend URL
- [ ] VITE_API_URL in frontend/.env is correct
- [ ] socket.io-client is installed in frontend (check package.json)
- [ ] Browser allows WebSocket connections (not blocked)
- [ ] Firewall/antivirus not blocking WebSocket

## Debug Mode

Enable detailed logging:

1. **Backend**: Already logs WebSocket events
2. **Frontend**: Check browser console for connection logs
3. **Network Tab**: Monitor WebSocket connections in DevTools

## Reset Connection

If connection is stuck:

1. **Frontend**: Refresh the page (F5)
2. **Backend**: Restart the server
3. **Browser**: Clear cache and hard refresh (Ctrl+Shift+R)

## Expected Behavior

When working correctly:

1. **On Page Load**:
   - Browser console: `🔌 Connecting to WebSocket: http://localhost:5000/api/voshan/socket.io`
   - Browser console: `✅ WebSocket connected: [socket-id]`
   - Browser console: `🔔 Subscribed to alerts: true`
   - Backend terminal: `📡 Client connected: [socket-id] (Total: 1)`

2. **When Alert Generated**:
   - Backend terminal: `📢 Broadcasted alert: [type] (ID: [id])`
   - Browser console: `📢 New alert received: [alert object]`
   - Frontend UI: Alert appears in real-time display

3. **On Disconnection**:
   - Browser console: `❌ WebSocket disconnected: [reason]`
   - Backend terminal: `📴 Client disconnected: [socket-id]`
   - Frontend: Shows "🔴 Disconnected" status

## Still Not Working?

1. Check all service logs (backend terminal, browser console)
2. Verify all environment variables are set correctly
3. Test WebSocket endpoint directly using browser console
4. Check if other WebSocket connections work (test with simple socket.io example)
5. Verify network connectivity between frontend and backend

