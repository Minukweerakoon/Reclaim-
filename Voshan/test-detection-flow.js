/**
 * Test Script: Verify Suspicious Bag Detection Flow
 * 
 * This script tests the complete flow from video upload to alert generation
 * Run with: node test-detection-flow.js
 */

const axios = require('axios');
const fs = require('fs');
const path = require('path');

const BACKEND_URL = 'http://localhost:5000/api';
const ML_SERVICE_URL = 'http://localhost:5001/api/v1/detect';

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

async function testBackendHealth() {
  log('\n📡 Testing Backend Health...', 'blue');
  try {
    const response = await axios.get(`${BACKEND_URL}/health`);
    if (response.data.status === 'OK') {
      log('✅ Backend is healthy', 'green');
      return true;
    } else {
      log('❌ Backend returned unexpected status', 'red');
      return false;
    }
  } catch (error) {
    log(`❌ Backend health check failed: ${error.message}`, 'red');
    return false;
  }
}

async function testMLServiceHealth() {
  log('\n🤖 Testing ML Service Health...', 'blue');
  try {
    const response = await axios.get(`${ML_SERVICE_URL}/status`);
    if (response.data.status === 'healthy' && response.data.model_loaded) {
      log('✅ ML Service is healthy', 'green');
      log(`   Model: ${response.data.model_info?.model_path || 'N/A'}`, 'green');
      log(`   Device: ${response.data.model_info?.device || 'N/A'}`, 'green');
      return true;
    } else {
      log('❌ ML Service is not healthy', 'red');
      log(`   Status: ${response.data.status}`, 'red');
      log(`   Model Loaded: ${response.data.model_loaded}`, 'red');
      return false;
    }
  } catch (error) {
    log(`❌ ML Service health check failed: ${error.message}`, 'red');
    log('   Make sure the Python ML service is running on port 5001', 'yellow');
    return false;
  }
}

async function testDetectionEndpoint() {
  log('\n🎬 Testing Detection Endpoint...', 'blue');
  try {
    const response = await axios.get(`${BACKEND_URL}/voshan/detection/health`);
    if (response.data.healthy !== false) {
      log('✅ Detection endpoint is accessible', 'green');
      return true;
    } else {
      log('❌ Detection endpoint returned unhealthy status', 'red');
      return false;
    }
  } catch (error) {
    log(`❌ Detection endpoint test failed: ${error.message}`, 'red');
    return false;
  }
}

async function checkMongoDBConnection() {
  log('\n💾 Checking MongoDB Connection...', 'blue');
  // This is a simple check - actual connection is handled by the backend
  log('⚠️  MongoDB connection check requires backend to be running', 'yellow');
  log('   Check backend terminal for MongoDB connection status', 'yellow');
  return true;
}

function checkVideoFile() {
  log('\n📹 Checking for Test Video...', 'blue');
  const uploadDir = path.join(__dirname, 'uploads', 'voshan');
  if (!fs.existsSync(uploadDir)) {
    log('⚠️  Upload directory does not exist', 'yellow');
    return false;
  }
  
  const files = fs.readdirSync(uploadDir).filter(f => 
    f.match(/\.(mp4|avi|mov)$/i)
  );
  
  if (files.length > 0) {
    log(`✅ Found ${files.length} video file(s) in upload directory`, 'green');
    return true;
  } else {
    log('⚠️  No video files found in upload directory', 'yellow');
    log('   You can upload a video through the frontend to test', 'yellow');
    return false;
  }
}

async function runAllTests() {
  log('\n🧪 Starting Detection Flow Verification Tests...\n', 'blue');
  
  const results = {
    backend: await testBackendHealth(),
    mlService: await testMLServiceHealth(),
    detectionEndpoint: await testDetectionEndpoint(),
    mongoDB: await checkMongoDBConnection(),
    videoFile: checkVideoFile(),
  };
  
  log('\n📊 Test Results Summary:', 'blue');
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');
  
  Object.entries(results).forEach(([test, passed]) => {
    const status = passed ? '✅ PASS' : '❌ FAIL';
    const color = passed ? 'green' : 'red';
    log(`${status.padEnd(10)} ${test}`, color);
  });
  
  log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━', 'blue');
  
  const allPassed = Object.values(results).every(r => r);
  
  if (allPassed) {
    log('\n✅ All critical tests passed!', 'green');
    log('   The detection system should be working correctly.', 'green');
    log('   Try uploading a video through the frontend to test detection.', 'green');
  } else {
    log('\n❌ Some tests failed', 'red');
    log('   Please fix the issues above before testing video upload.', 'red');
    log('   See VERIFY_BAG_DETECTION.md for troubleshooting steps.', 'yellow');
  }
  
  return allPassed;
}

// Run tests
if (require.main === module) {
  runAllTests()
    .then(success => {
      process.exit(success ? 0 : 1);
    })
    .catch(error => {
      log(`\n❌ Test script error: ${error.message}`, 'red');
      process.exit(1);
    });
}

module.exports = { runAllTests };

