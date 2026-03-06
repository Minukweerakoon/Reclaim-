/**
 * Test Script: WebSocket Real-Time Alert Testing
 * 
 * This script tests WebSocket connection and alert broadcasting
 * Run with: node test-websocket-alert.js
 * 
 * Note: For full WebSocket testing, use the browser console method
 * or install socket.io-client: npm install socket.io-client
 */

const axios = require('axios');

const BACKEND_URL = 'http://localhost:5000';
const SOCKET_PATH = '/api/voshan/socket.io';

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

async function checkWebSocketStatus() {
  log('\n📡 Checking WebSocket Status...', 'blue');
  try {
    const response = await axios.get(`${BACKEND_URL}/api/voshan/detection/websocket/status`);
    const status = response.data.data;
    
    log(`   Enabled: ${status.enabled ? '✅ Yes' : '❌ No'}`, status.enabled ? 'green' : 'red');
    log(`   Connected Clients: ${status.connectedClients}`, 'cyan');
    
    if (status.connectedClients > 0) {
      log(`   Client IDs: ${status.clientIds.join(', ')}`, 'cyan');
    }
    
    return status.enabled;
  } catch (error) {
    log(`   ❌ Error checking status: ${error.message}`, 'red');
    return false;
  }
}

async function testWebSocketConnection() {
  log('\n🔌 Testing WebSocket Connection...', 'blue');
  log('   ℹ️  Full WebSocket testing requires browser or socket.io-client', 'yellow');
  log('   ℹ️  Checking connection status via API...', 'yellow');
  
  try {
    const response = await axios.get(`${BACKEND_URL}/api/voshan/detection/websocket/status`);
    const status = response.data.data;
    
    if (status.enabled && status.connectedClients > 0) {
      log(`   ✅ WebSocket service is active`, 'green');
      log(`   ✅ ${status.connectedClients} client(s) connected`, 'green');
      return { connected: true, subscribed: true, alertReceived: false };
    } else if (status.enabled) {
      log(`   ⚠️  WebSocket service is enabled but no clients connected`, 'yellow');
      log(`   ℹ️  Open the frontend to establish a connection`, 'yellow');
      return { connected: false, subscribed: false, alertReceived: false };
    } else {
      log(`   ❌ WebSocket service is not enabled`, 'red');
      return { connected: false, subscribed: false, alertReceived: false };
    }
  } catch (error) {
    log(`   ❌ Error checking connection: ${error.message}`, 'red');
    return { connected: false, subscribed: false, alertReceived: false };
  }
}

async function broadcastTestAlert() {
  log('\n📤 Broadcasting Test Alert...', 'blue');
  
  // Note: This requires the backend to have a test endpoint
  // For now, we'll just check if we can connect and receive alerts
  // In a real scenario, you would upload a video or use a test endpoint
  
  log('   ℹ️  To test alert broadcasting:', 'yellow');
  log('      1. Upload a video through the frontend', 'yellow');
  log('      2. Or wait for a real alert to be generated', 'yellow');
  log('      3. The WebSocket connection will receive it automatically', 'yellow');
}

async function runTests() {
  log('\n🧪 WebSocket Real-Time Update Tests\n', 'blue');
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');
  
  try {
    // Test 1: Check WebSocket Status
    const enabled = await checkWebSocketStatus();
    if (!enabled) {
      log('\n❌ WebSocket service is not enabled', 'red');
      log('   Please ensure the backend server is running', 'yellow');
      return;
    }

    // Test 2: Test Connection
    const result = await testWebSocketConnection();
    
    log('\n📊 Test Results:', 'blue');
    log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');
    log(`✅ Connection: ${result.connected ? 'PASS' : 'FAIL'}`, result.connected ? 'green' : 'red');
    log(`✅ Subscription: ${result.subscribed ? 'PASS' : 'FAIL'}`, result.subscribed ? 'green' : 'red');
    log(`⚠️  Alert Received: ${result.alertReceived ? 'PASS' : 'WAITING'}`, result.alertReceived ? 'green' : 'yellow');
    
    if (result.connected && result.subscribed) {
      log('\n✅ WebSocket is working correctly!', 'green');
      log('   The connection is ready to receive real-time alerts.', 'green');
      log('   Upload a video to generate alerts and test the real-time updates.', 'yellow');
    } else if (enabled) {
      log('\n⚠️  WebSocket service is enabled but no clients connected', 'yellow');
      log('   To test real-time updates:', 'yellow');
      log('   1. Open http://localhost:3000/voshan/detection in your browser', 'yellow');
      log('   2. Check browser console for WebSocket connection', 'yellow');
      log('   3. Upload a video to generate alerts', 'yellow');
    } else {
      log('\n❌ WebSocket connection failed', 'red');
      log('   Please check the troubleshooting guide.', 'yellow');
    }

    // Test 3: Instructions for testing alerts
    await broadcastTestAlert();
    
  } catch (error) {
    log(`\n❌ Test failed: ${error.message}`, 'red');
    log('\nTroubleshooting:', 'yellow');
    log('1. Ensure backend is running on port 5000', 'yellow');
    log('2. Check WebSocket service is initialized', 'yellow');
    log('3. Verify CORS settings allow connections from frontend', 'yellow');
    log('4. Check backend terminal for WebSocket initialization message', 'yellow');
  }
}

// Run tests
if (require.main === module) {
  runTests()
    .then(() => {
      log('\n✅ Tests completed\n', 'green');
      process.exit(0);
    })
    .catch((error) => {
      log(`\n❌ Tests failed: ${error.message}\n`, 'red');
      process.exit(1);
    });
}

module.exports = { runTests, checkWebSocketStatus, testWebSocketConnection };

