# launch-game.ps1 — Launch a game by name (from config.json) or by direct path.
# Usage: .\launch-game.ps1 -GameName mina_the_hollower
#        .\launch-game.ps1 -ExePath "D:\path\to\game.exe"

param(
    [string]$GameName,
    [string]$ExePath,
    [string]$WorkingDir,
    [string]$ConfigPath = "$PSScriptRoot\config.json"
)

$ErrorActionPreference = 'Stop'

$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json

if ($ExePath) {
    # Direct launch mode
    Write-Host "=== LAUNCHING GAME ===" -ForegroundColor Cyan
    Write-Host "Executable: $ExePath"
    
    if (-not (Test-Path $ExePath)) {
        Write-Error "Game executable not found: $ExePath"
        exit 1
    }
    
    $dir = Split-Path $ExePath -Parent
    Start-Process -FilePath $ExePath -WorkingDirectory $dir
    Write-Host "  ✓ Game launched" -ForegroundColor Green
    
} elseif ($GameName) {
    # Config-driven launch
    $game = $config.games.PSObject.Properties[$GameName]
    if (-not $game) {
        Write-Error "Unknown game: $GameName. Available games: $($config.games.PSObject.Properties.Name -join ', ')"
        exit 1
    }
    
    $gameValue = $game.value
    Write-Host "=== LAUNCHING: $($gameValue.name) ===" -ForegroundColor Cyan
    
    if ($gameValue.steam_appid -and $gameValue.steam_appid -ne $null) {
        # Steam game
        $steamPath = "C:\Program Files (x86)\Steam\steam.exe"
        Write-Host "Launching via Steam (APPID: $($gameValue.steam_appid))..."
        Start-Process -FilePath $steamPath -ArgumentList "-applaunch $($gameValue.steam_appid)" -WorkingDirectory $gameValue.working_dir
    } elseif ($gameValue.exe) {
        # Direct executable
        Write-Host "Executable: $($gameValue.exe)"
        if (-not (Test-Path $gameValue.exe)) {
            Write-Error "Game executable not found: $($gameValue.exe)"
            exit 1
        }
        Start-Process -FilePath $gameValue.exe -WorkingDirectory $gameValue.working_dir
    } else {
        Write-Error "No launch method configured for game: $GameName"
        exit 1
    }
    
    Write-Host "  ✓ Game launched" -ForegroundColor Green
    
} else {
    Write-Error "Specify -GameName or -ExePath"
    exit 1
}
