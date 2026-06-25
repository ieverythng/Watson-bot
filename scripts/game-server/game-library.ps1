# game-library.ps1
# Discover installed Steam games and their APPIDs.
# Usage: .\game-library.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Steam Game Library Scanner"
Write-Host "═══════════════════════════"
Write-Host ""

# Method 1: Read Steam library folders from config.vdf
$steamPath = "C:\Program Files (x86)\Steam"
$configPath = "$steamPath\config\vdf"

if (Test-Path $configPath) {
    Write-Host "[scan] Reading Steam library paths..."
    $libraries = Get-Content $configPath
    # Parse library paths from VDF (simplified)
} else {
    Write-Host "[scan] Using default Steam library path."
}

# Method 2: Scan appmanifest_*.acf files for installed games
$steamLibraries = @("$steamPath\steamapps")

# Check for additional library folders
try {
    $libraryFolders = Get-ChildItem "$env:USERPROFILE\Documents\My Games" -Directory -ErrorAction SilentlyContinue
} catch {}

# Scan for appmanifest files
$games = @()

foreach ($lib in $steamLibraries) {
    if (Test-Path $lib) {
        $manifests = Get-ChildItem "$lib\appmanifest_*.acf" -ErrorAction SilentlyContinue
        
        foreach ($manifest in $manifests) {
            $content = Get-Content $manifest.FullName -Raw
            
            # Extract APPID
            if ($content -match '"appid"\s+"(\d+)"') {
                $appid = $matches[1]
            } else {
                continue
            }
            
            # Extract game name
            if ($content -match '"name"\s+"([^"]+)"') {
                $name = $matches[1]
            } else {
                $name = "Unknown"
            }
            
            # Extract disk space
            if ($content -match '"StateFlags"\s+"(\d+)"') {
                $stateFlags = [int]$matches[1]
                $installed = ($stateFlags -band 4) -eq 0 # StateFlag_Installed = 4
            } else {
                $installed = $true
            }
            
            if ($installed) {
                $games += [PSCustomObject]@{
                    AppId = $appid
                    Name  = $name
                }
            }
        }
    }
}

# Display results
Write-Host "Found $($games.Count) installed Steam games:"
Write-Host ""
$games | Sort-Object Name | Format-Table -AutoSize -Property @(
    @{Label="APPID"; Expression={$_.AppId}; Width=12},
    @{Label="Game Name"; Expression={$_.Name}; Width=50}
)

# Export to JSON for Watson
$jsonPath = "$PSScriptRoot\steam-library.json"
$games | ConvertTo-Json | Out-File $jsonPath -Encoding utf8
Write-Host ""
Write-Host "[export] Library saved to $jsonPath"

exit 0
