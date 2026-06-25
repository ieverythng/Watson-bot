# full-session.ps1 — Full gaming session: pause Watson → launch game → monitor → resume.
# Usage: .\full-session.ps1 -GameName mina_the_hollower
#        .\full-session.ps1 -GameName equinox_homecoming

param(
    [string]$GameName = "mina_the_hollower",
    [switch]$NoResume,
    [string]$ConfigPath = "$PSScriptRoot\config.json"
)

$ErrorActionPreference = 'Stop'
$ScriptDir = $PSScriptRoot

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║         GAMING SESSION ORCHESTRATOR         ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Phase 1: Pause Watson
Write-Host "── Phase 1: Pausing Watson ──" -ForegroundColor Yellow
$pauseScript = Join-Path $ScriptDir "pause-watson.ps1"
if (Test-Path $pauseScript) {
    & $pauseScript
} else {
    Write-Error "Pause script not found: $pauseScript"
    exit 1
}

Write-Host ""
Start-Sleep -Seconds 2

# Phase 2: Launch game
Write-Host "── Phase 2: Launching Game ──" -ForegroundColor Yellow
$launchScript = Join-Path $ScriptDir "launch-game.ps1"
if (Test-Path $launchScript) {
    & $launchScript -GameName $GameName
} else {
    Write-Error "Launch script not found: $launchScript"
    exit 1
}

Write-Host ""
Start-Sleep -Seconds 3

# Phase 3: Monitor game
$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
$game = $config.games.PSObject.Properties[$GameName]
if (-not $game) {
    Write-Error "Unknown game: $GameName"
    exit 1
}

$processName = $game.value.process_name
if ($processName) {
    Write-Host "── Phase 3: Monitoring Game ──" -ForegroundColor Yellow
    $monitorScript = Join-Path $ScriptDir "monitor-game.ps1"
    if (Test-Path $monitorScript) {
        & $monitorScript -ProcessName $processName -AutoResume:(-not $NoResume)
    }
} else {
    Write-Host ""
    Write-Host "── Phase 3: No process to monitor ──" -ForegroundColor Yellow
    Write-Host "Game launched. Press Enter when done playing..." -ForegroundColor DarkYellow
    Read-Host
    
    if (-not $NoResume) {
        Write-Host ""
        Write-Host "── Phase 4: Resuming Watson ──" -ForegroundColor Yellow
        $resumeScript = Join-Path $ScriptDir "resume-watson.ps1"
        if (Test-Path $resumeScript) {
            & $resumeScript
        }
    }
}

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║          SESSION COMPLETE — ENJOY!           ║" -ForegroundColor Green
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Green
