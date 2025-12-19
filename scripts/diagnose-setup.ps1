# Comprehensive Setup Diagnostic Script
Write-Host "=== Smart Notebook Setup Diagnostic ===" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check WSL Docker
Write-Host "1. Checking WSL Docker..." -ForegroundColor Yellow
$wslDocker = wsl docker --version 2>&1
if ($wslDocker -match "version") {
    Write-Host "   ✅ Docker is installed in WSL" -ForegroundColor Green
    Write-Host "   Version: $wslDocker" -ForegroundColor White
} else {
    Write-Host "   ❌ Docker not found in WSL" -ForegroundColor Red
    Write-Host "   Install Docker in WSL or use Docker Desktop" -ForegroundColor Yellow
}

# Step 2: Check Docker Compose
Write-Host "`n2. Checking Docker Compose..." -ForegroundColor Yellow
$wslCompose = wsl docker compose version 2>&1
if ($wslCompose -match "version") {
    Write-Host "   ✅ Docker Compose is available" -ForegroundColor Green
} else {
    Write-Host "   ❌ Docker Compose not found" -ForegroundColor Red
}

# Step 3: Check if containers are running
Write-Host "`n3. Checking Docker containers..." -ForegroundColor Yellow
$containers = wsl bash -c "cd /home/karim/smart-notebook && docker compose ps --format json" 2>&1
if ($containers -match "sn_ocr_service") {
    Write-Host "   ✅ OCR service container found" -ForegroundColor Green
    $containers | ConvertFrom-Json | Where-Object {$_.Name -eq "sn_ocr_service"} | ForEach-Object {
        Write-Host "   Status: $($_.State)" -ForegroundColor White
    }
} else {
    Write-Host "   ❌ OCR service container NOT running" -ForegroundColor Red
    Write-Host "   Run: wsl bash -c 'cd /home/karim/smart-notebook && docker compose up -d'" -ForegroundColor Yellow
}

# Step 4: Check port forwarding
Write-Host "`n4. Checking port forwarding..." -ForegroundColor Yellow
$portForwarding = netsh interface portproxy show all 2>&1
if ($portForwarding -match "9000") {
    Write-Host "   ✅ Port 9000 forwarding configured" -ForegroundColor Green
    $portForwarding | Select-String "9000" | ForEach-Object { Write-Host "   $_" -ForegroundColor White }
} else {
    Write-Host "   ❌ Port 9000 forwarding NOT configured" -ForegroundColor Red
    Write-Host "   Run setup-port-forwarding.ps1 as Administrator" -ForegroundColor Yellow
}

# Step 5: Check Windows IP
Write-Host "`n5. Checking Windows WiFi IP..." -ForegroundColor Yellow
$windowsIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -like "*Wi-Fi*"} | Select-Object -First 1).IPAddress
if ($windowsIP) {
    Write-Host "   ✅ Windows WiFi IP: $windowsIP" -ForegroundColor Green
    Write-Host "   Mobile app should use: http://$windowsIP:9000" -ForegroundColor White
} else {
    Write-Host "   ❌ Could not detect WiFi IP" -ForegroundColor Red
}

# Step 6: Test OCR service from WSL
Write-Host "`n6. Testing OCR service from WSL..." -ForegroundColor Yellow
$wslHealth = wsl bash -c "curl -s http://localhost:9000/health 2>&1" 2>&1
if ($wslHealth -match "healthy" -or $wslHealth -match "status") {
    Write-Host "   ✅ OCR service responding in WSL" -ForegroundColor Green
    Write-Host "   Response: $wslHealth" -ForegroundColor White
} else {
    Write-Host "   ❌ OCR service NOT responding in WSL" -ForegroundColor Red
    Write-Host "   Response: $wslHealth" -ForegroundColor White
}

# Step 7: Test OCR service from Windows
Write-Host "`n7. Testing OCR service from Windows..." -ForegroundColor Yellow
if ($windowsIP) {
    try {
        $winHealth = Invoke-WebRequest -Uri "http://$windowsIP:9000/health" -TimeoutSec 5 -ErrorAction Stop
        Write-Host "   ✅ OCR service accessible from Windows IP" -ForegroundColor Green
        Write-Host "   Response: $($winHealth.Content)" -ForegroundColor White
    } catch {
        Write-Host "   ❌ OCR service NOT accessible from Windows IP" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor White
        if ($_.Exception.Message -like "*refused*") {
            Write-Host "   → Port forwarding is likely not set up" -ForegroundColor Yellow
        }
    }
} else {
    Write-Host "   ⚠️  Skipped (no WiFi IP detected)" -ForegroundColor Yellow
}

# Step 8: Check React Native setup
Write-Host "`n8. Checking React Native setup..." -ForegroundColor Yellow
$mobilePath = "\\wsl.localhost\Ubuntu\home\karim\smart-notebook\mobile"
if (Test-Path "$mobilePath\node_modules") {
    Write-Host "   ✅ node_modules exists" -ForegroundColor Green
} else {
    Write-Host "   ❌ node_modules NOT found" -ForegroundColor Red
    Write-Host "   Run: cd $mobilePath && npm install" -ForegroundColor Yellow
}

# Step 9: Check API configuration
Write-Host "`n9. Checking API configuration..." -ForegroundColor Yellow
$apiFile = "$mobilePath\src\services\api.ts"
if (Test-Path $apiFile) {
    $apiContent = Get-Content $apiFile -Raw
    if ($apiContent -match "172\.20\.10\.2:9000") {
        Write-Host "   ✅ OCR_SERVICE_URL configured: http://172.20.10.2:9000" -ForegroundColor Green
        if ($windowsIP -and $windowsIP -ne "172.20.10.2") {
            Write-Host "   ⚠️  Warning: API uses 172.20.10.2 but current WiFi IP is $windowsIP" -ForegroundColor Yellow
            Write-Host "   Update api.ts if IP changed" -ForegroundColor Yellow
        }
    } else {
        Write-Host "   ⚠️  OCR_SERVICE_URL not found in expected format" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ❌ api.ts not found" -ForegroundColor Red
}

Write-Host "`n=== Diagnostic Complete ===" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. If containers not running: wsl bash -c 'cd /home/karim/smart-notebook && docker compose up -d'" -ForegroundColor White
Write-Host "2. If port forwarding missing: Run setup-port-forwarding.ps1 as Administrator" -ForegroundColor White
Write-Host "3. If node_modules missing: cd mobile && npm install" -ForegroundColor White
Write-Host "4. Start Metro: cd mobile && npm start" -ForegroundColor White
Write-Host "5. Run app: npm run android" -ForegroundColor White
