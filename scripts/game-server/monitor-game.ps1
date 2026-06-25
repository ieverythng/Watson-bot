# monitor-game.ps1 — Watch for game process to exit, then trigger resume.
# Usage: .\monitor-game.ps1 -ProcessName MinaTheHollower
#        .\monitor-game.ps1 -GameName mina_the_hollower

param(
    [string]$ProcessName,
    [string]$GameName,
    [string]$ConfigPath = "$PSScriptRoot\config.json",
    [switch]$AutoResume
)

$ErrorActionPreference = 'Stop'

if (-not $ProcessName -and $GameName) {
    $config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
    $game = $config.games.PSObject.Properties[$GameName]
    if ($game -and $game.value.process_name) {
        $ProcessName = $game.value.process_name
    } else {
        Write-Error "Cannot determine process name for game: $GameName"
        exit 1
    }
}

if (-not $ProcessName) {
    Write-Error "Specify -ProcessName or -GameName"
    exit 1
}

Write-Host "=== MONITORING: $ProcessName ===" -ForegroundColor Cyan
Write-Host "Waiting for game to exit..." -ForegroundColor DarkYellow

# Wait for the process to exit
while ($true) {
    $proc = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue
    if (-not $proc) {
        Write-Host ""
        Write-Host "  ✓ Game process exited!" -ForegroundColor Green
        break
    }
    Start-Sleep -Seconds 5
}

if ($AutoResume) {
    Write-Host ""
    Write-Host "=== AUTO-RESUMING WATSON ===" -ForegroundColor Yellow
    $resumeScript = Join-Path $PSScriptRoot "resume-watson.ps1"
    if (Test-Path $resumeScript) {
        & $resumeScript
    } else {
        Write-Error "Resume script not found: $resumeScript"
    }
} else {
    Write-Host ""
    Write-Host "Game ended. Run resume-watson.ps1 or Lazarus to restore inference." -ForegroundColor DarkYellow
}
