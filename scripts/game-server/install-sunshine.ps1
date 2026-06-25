# install-sunshine.ps1 — Download and install Sunshine on Windows host.
# Run from WSL: pwsh -File /mnt/c/Users/Admin/Watson/scripts/game-server/install-sunshine.ps1

$ErrorActionPreference = 'Stop'

$SunshineRepo = 'LizardByte/Sunshine'
$InstallDir = "$env:LOCALAPPDATA\Sunshine"

Write-Host "=== Sunshine Installer ===" -ForegroundColor Cyan

# Check if already installed
if (Get-Service sunshine -ErrorAction SilentlyContinue) {
    Write-Host "Sunshine is already installed." -ForegroundColor Green
    Write-Host "Web UI: https://localhost:47990"
    exit 0
}

# Get latest release URL
Write-Host "Fetching latest Sunshine release..." -ForegroundColor Yellow
$release = Invoke-RestMethod -Uri "https://api.github.com/repos/$SunshineRepo/releases/latest"
$assets = $release.assets | Where-Object { $_.name -match '\.msi$' }

if ($null -eq $assets) {
    Write-Error "No MSI installer found in latest release."
    exit 1
}

$installer = $assets[0]
$downloadUrl = $installer.browser_download_url
$msiPath = Join-Path $env:TEMP $installer.name

Write-Host "Downloading: $($installer.name)" -ForegroundColor Yellow
Write-Host "URL: $downloadUrl"

Invoke-WebRequest -Uri $downloadUrl -OutFile $msiPath -UseBasicParsing

Write-Host "Installing Sunshine..." -ForegroundColor Yellow
Start-Process msiexec.exe -ArgumentList "/i `"$msiPath`" /quiet /norestart INSTALLDIR=`"$InstallDir`"" -Wait -NoNewWindow

# Verify installation
Start-Sleep -Seconds 3
$service = Get-Service sunshine -ErrorAction SilentlyContinue
if ($service) {
    Write-Host ""
    Write-Host "=== Sunshine installed successfully ===" -ForegroundColor Green
    Write-Host "Service status: $($service.Status)"
    Write-Host "Web UI: https://localhost:47990"
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  1. Open https://localhost:47990 in your browser"
    Write-Host "  2. Add games to Sunshine's app list"
    Write-Host "  3. Install Moonlight on client devices (iPad, laptop)"
    Write-Host "  4. Pair with the PIN shown in Sunshine web UI"
} else {
    Write-Error "Installation may have failed. Check logs at $InstallDir\logs"
    exit 1
}

# Cleanup
Remove-Item $msiPath -Force -ErrorAction SilentlyContinue
