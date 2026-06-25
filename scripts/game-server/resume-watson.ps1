# resume-watson.ps1 — Restart the Watson inference stack after gaming.
# Calls Lazarus-equivalent logic: launches llama.cpp + LiteLLM via the canonical stack script.

$ErrorActionPreference = 'Stop'

$StackScript = "C:\Users\Admin\PROJECTS\zerotier-llm-proxy\scripts\windows\Start-Qwen36ZeroTierStack.ps1"
$Profile = "hermes-qwen36-64k"
$Model = "qwen36-turbo-hermes"

Write-Host "=== RESUMING WATSON ===" -ForegroundColor Yellow

# Check if stack script exists
if (-not (Test-Path $StackScript)) {
    Write-Error "Stack script not found at: $StackScript"
    exit 1
}

# Kill any stale LiteLLM on Windows side
try {
    $litellm = Get-Process -Name "python", "python3" -ErrorAction SilentlyContinue | Where-Object {
        $_.CommandLine -match 'litellm'
    }
    if ($litellm) {
        $litellm | Stop-Process -Force
        Write-Host "  ✓ Killed stale LiteLLM processes" -ForegroundColor Green
    }
} catch {}

# Launch the canonical stack
Write-Host "Launching inference stack..." -ForegroundColor Yellow
& $StackScript -ContextSize 65536 -Profile $Profile -Model $Model -ReplaceLiteLLM -NoOracle

Start-Sleep -Seconds 2

# Verify llama.cpp is up
$llama = Get-Process -Name "llama-server" -ErrorAction SilentlyContinue
if ($llama) {
    Write-Host "  ✓ llama.cpp running (PID: $($llama.Id))" -ForegroundColor Green
} else {
    Write-Host "  ⚠ llama-server process not detected yet" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "=== WATSON RESUMED ===" -ForegroundColor Green
Write-Host "Inference stack should be back online." -ForegroundColor Cyan
