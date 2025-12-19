# WSL Port Forwarding Setup Script
# Run this as Administrator!

Write-Host "Setting up WSL Port Forwarding..." -ForegroundColor Cyan

# Get WSL IP address
$wslIP = (wsl hostname -I).Trim().Split()[0]
Write-Host "WSL IP Address: $wslIP" -ForegroundColor Green

# Remove existing port forwarding rules (if any)
Write-Host "`nRemoving old port forwarding rules..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=8081 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=9000 listenaddress=0.0.0.0 2>$null

# Add new port forwarding rules
Write-Host "`nAdding port forwarding rules..." -ForegroundColor Yellow
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8000 connectaddress=$wslIP connectport=8000
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=8081 connectaddress=$wslIP connectport=8081
netsh interface portproxy add v4tov4 listenaddress=0.0.0.0 listenport=9000 connectaddress=$wslIP connectport=9000

# Configure Windows Firewall
Write-Host "`nConfiguring Windows Firewall..." -ForegroundColor Yellow

# Remove old rules if they exist
Remove-NetFirewallRule -DisplayName "WSL Backend 8000" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "WSL Metro 8081" -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName "WSL OCR Service 9000" -ErrorAction SilentlyContinue

# Add new firewall rules
New-NetFirewallRule -DisplayName "WSL Backend 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow | Out-Null
New-NetFirewallRule -DisplayName "WSL Metro 8081" -Direction Inbound -LocalPort 8081 -Protocol TCP -Action Allow | Out-Null
New-NetFirewallRule -DisplayName "WSL OCR Service 9000" -Direction Inbound -LocalPort 9000 -Protocol TCP -Action Allow | Out-Null

# Show current port forwarding rules
Write-Host "`nCurrent Port Forwarding Rules:" -ForegroundColor Cyan
netsh interface portproxy show all

# Get Windows IP address for display
$windowsIP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object {$_.InterfaceAlias -like "*Wi-Fi*" -or $_.InterfaceAlias -like "*Ethernet*"} | Select-Object -First 1).IPAddress
if (-not $windowsIP) {
    $windowsIP = "YOUR_WINDOWS_IP"
}

Write-Host "`n✅ Setup Complete!" -ForegroundColor Green
Write-Host "`nYou can now access:" -ForegroundColor Cyan
Write-Host "  Backend API: http://$windowsIP:8000/" -ForegroundColor White
Write-Host "  Metro Bundler: http://$windowsIP:8081/status" -ForegroundColor White
Write-Host "  OCR Service: http://$windowsIP:9000/health" -ForegroundColor White
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')

