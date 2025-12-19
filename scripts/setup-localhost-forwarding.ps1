# Setup localhost port forwarding to WSL
# Run as Administrator

Write-Host "Setting up localhost → WSL port forwarding..." -ForegroundColor Cyan

# Get WSL IP
$wslIP = (wsl hostname -I).Trim().Split()[0]
Write-Host "WSL IP: $wslIP" -ForegroundColor Green

# Remove existing forwarding
Write-Host "`nRemoving old forwarding rules..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=127.0.0.1 2>$null
netsh interface portproxy delete v4tov4 listenport=9000 listenaddress=127.0.0.1 2>$null

# Add forwarding from localhost to WSL
Write-Host "Adding localhost forwarding to WSL..." -ForegroundColor Yellow
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=8000 connectaddress=$wslIP connectport=8000
netsh interface portproxy add v4tov4 listenaddress=127.0.0.1 listenport=9000 connectaddress=$wslIP connectport=9000

Write-Host "`n✅ Localhost forwarding setup complete!" -ForegroundColor Green
Write-Host "`nPort Forwarding Rules:" -ForegroundColor Cyan
netsh interface portproxy show all

Write-Host "`nNow the mobile app can connect via:" -ForegroundColor Cyan
Write-Host "  localhost:8000 → WSL Backend" -ForegroundColor White
Write-Host "  localhost:9000 → WSL OCR Service" -ForegroundColor White
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')

