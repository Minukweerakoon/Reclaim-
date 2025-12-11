# Quick API Testing Guide

## Test All Endpoints

### 1. Health Checks

**Backend Health:**
```powershell
Invoke-WebRequest -Uri "http://localhost:5000/api/health"
```

**ML Service Health (via Backend):**
```powershell
Invoke-WebRequest -Uri "http://localhost:5000/api/voshan/detection/health"
```

**ML Service Direct:**
```powershell
Invoke-WebRequest -Uri "http://localhost:5001/api/v1/detect/status"
```

### 2. WebSocket Status

```powershell
Invoke-WebRequest -Uri "http://localhost:5000/api/voshan/detection/websocket/status"
```

### 3. Get Alerts

```powershell
Invoke-WebRequest -Uri "http://localhost:5000/api/voshan/detection/alerts?page=1&limit=10"
```

### 4. Test Video Processing

**Note:** You need a video file for this test.

```powershell
$videoPath = "C:\path\to\video.mp4"
$uri = "http://localhost:5000/api/voshan/detection/process-video"

$form = @{
    video = Get-Item $videoPath
    cameraId = "CAM_001"
    saveOutput = "true"
}

$response = Invoke-RestMethod -Uri $uri -Method Post -Form $form
$response | ConvertTo-Json -Depth 10
```

---

## Browser Testing

1. **Open:** `http://localhost:3000/voshan/detection`
2. **Check:**
   - ML Service Status: ✅ Healthy
   - WebSocket: 🟢 Connected
   - Statistics: Loaded

3. **Open:** `http://localhost:3000/voshan/alerts`
4. **Check:**
   - Page loads
   - Filters work
   - Alerts display (if any)

---

## Quick Verification Script

Save this as `test-system.ps1`:

```powershell
Write-Host "Testing Suspicious Behavior Detection System..." -ForegroundColor Cyan
Write-Host ""

# Test ML Service
Write-Host "1. Testing ML Service..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5001/api/v1/detect/status" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    if ($data.status -eq "healthy") {
        Write-Host "   ✅ ML Service: Healthy" -ForegroundColor Green
    } else {
        Write-Host "   ❌ ML Service: Unhealthy" -ForegroundColor Red
    }
} catch {
    Write-Host "   ❌ ML Service: Not responding" -ForegroundColor Red
}

# Test Backend
Write-Host "2. Testing Backend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/health" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    if ($data.status -eq "OK") {
        Write-Host "   ✅ Backend: Running" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ Backend: Not responding" -ForegroundColor Red
}

# Test ML Service via Backend
Write-Host "3. Testing ML Service via Backend..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/voshan/detection/health" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    if ($data.status -eq "healthy") {
        Write-Host "   ✅ ML Service Connection: Working" -ForegroundColor Green
    }
} catch {
    Write-Host "   ❌ ML Service Connection: Failed" -ForegroundColor Red
}

# Test WebSocket Status
Write-Host "4. Testing WebSocket..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/voshan/detection/websocket/status" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    if ($data.data.enabled) {
        Write-Host "   ✅ WebSocket: Enabled" -ForegroundColor Green
        Write-Host "      Connected Clients: $($data.data.connectedClients)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ WebSocket: Not available" -ForegroundColor Red
}

# Test Alerts Endpoint
Write-Host "5. Testing Alerts Endpoint..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost:5000/api/voshan/detection/alerts?limit=5" -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    if ($data.success) {
        Write-Host "   ✅ Alerts Endpoint: Working" -ForegroundColor Green
        Write-Host "      Total Alerts: $($data.data.pagination.total)" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Alerts Endpoint: Failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "Testing Complete!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Open http://localhost:3000/voshan/detection in browser" -ForegroundColor White
Write-Host "2. Check dashboard for status indicators" -ForegroundColor White
Write-Host "3. Process a test video to generate alerts" -ForegroundColor White
```

Run it:
```powershell
.\test-system.ps1
```

