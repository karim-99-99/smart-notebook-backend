# Test OCR Service Connection
Write-Host "Testing OCR Service Connection..." -ForegroundColor Cyan

# Get Windows WiFi IP
$windowsIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -like "*Wi-Fi*"} | Select-Object -First 1).IPAddress
Write-Host "Windows WiFi IP: $windowsIP" -ForegroundColor Green

# Test 1: Check if port 9000 is listening on Windows
Write-Host "`n1. Checking if port 9000 is listening on Windows..." -ForegroundColor Yellow
$port9000 = Get-NetTCPConnection -LocalPort 9000 -ErrorAction SilentlyContinue
if ($port9000) {
    Write-Host "   ✅ Port 9000 is listening" -ForegroundColor Green
    $port9000 | Format-Table LocalAddress, LocalPort, State, OwningProcess
} else {
    Write-Host "   ❌ Port 9000 is NOT listening on Windows" -ForegroundColor Red
    Write-Host "   This means port forwarding is not set up!" -ForegroundColor Red
}

# Test 2: Check port forwarding rules
Write-Host "`n2. Checking port forwarding rules..." -ForegroundColor Yellow
$portForwarding = netsh interface portproxy show all
if ($portForwarding -match "9000") {
    Write-Host "   ✅ Port forwarding for 9000 is configured:" -ForegroundColor Green
    Write-Host $portForwarding
} else {
    Write-Host "   ❌ Port forwarding for 9000 is NOT configured" -ForegroundColor Red
    Write-Host "   Run setup-port-forwarding.ps1 as Administrator!" -ForegroundColor Yellow
}

# Test 3: Test connection to Windows IP
Write-Host "`n3. Testing connection to http://$windowsIP:9000/health..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://$windowsIP:9000/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "   ✅ Connection successful!" -ForegroundColor Green
    Write-Host "   Response: $($response.Content)" -ForegroundColor White
} catch {
    Write-Host "   ❌ Connection failed: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Message -like "*refused*" -or $_.Exception.Message -like "*not listening*") {
        Write-Host "   → Port forwarding is likely not set up" -ForegroundColor Yellow
    } elseif ($_.Exception.Message -like "*timeout*") {
        Write-Host "   → Service might not be running or firewall is blocking" -ForegroundColor Yellow
    }
}

# Test 4: Check WSL connection
Write-Host "`n4. Testing connection from WSL..." -ForegroundColor Yellow
$wslTest = wsl bash -c "curl -s http://localhost:9000/health 2>&1"
if ($wslTest -match "healthy" -or $wslTest -match "status") {
    Write-Host "   ✅ OCR service is running in WSL" -ForegroundColor Green
    Write-Host "   Response: $wslTest" -ForegroundColor White
} else {
    Write-Host "   ❌ OCR service is NOT running in WSL" -ForegroundColor Red
    Write-Host "   Response: $wslTest" -ForegroundColor White
    Write-Host "   → Start Docker containers: docker compose up" -ForegroundColor Yellow
}

Write-Host "`n" -ForegroundColor Cyan
