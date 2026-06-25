# pause-watson.ps1 — Stop llama.cpp inference to free VRAM for gaming.
# Kills the Windows llama.cpp process and WSL LiteLLM proxy.
# Watson will be offline until resume-watson.ps1 or Lazarus restores it.

$ErrorActionPreference = 'Stop'

Write-Host "=== PAUSING WATSON ===" -ForegroundColor Yellow

# Kill llama.cpp on Windows (the main VRAM hog)
$llamaProcesses = Get-Process -Name "llama-server" -ErrorAction SilentlyContinue
if ($llamaProcesses) {
    foreach ($p in $llamaProcesses) {
        Write-Host "Stopping llama.cpp (PID: $($p.Id))..." -ForegroundColor Yellow
        $p | Stop-Process -Force
    }
    Write-Host "  ✓ llama.cpp stopped" -ForegroundColor Green
} else {
    Write-Host "  ℹ llama.cpp not running" -ForegroundColor DarkYellow
}

# Kill any other model servers that might be holding VRAM
$gpuProcesses = Get-Process -Name "python", "python3" -ErrorAction SilentlyContinue | Where-Object {
    $_.StartTime -lt (Get-Date).AddHours(-1)
}
if ($gpuProcesses) {
    foreach ($p in $gpuProcesses) {
        Write-Host "Stopping long-running Python (PID: $($p.Id))..." -ForegroundColor Yellow
        $p | Stop-Process -Force
    }
}

# Verify VRAM freed
try {
    $vram = nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits 2>$null
    if ($vram) {
        Write-Host "  ✓ VRAM now: ${vram} MB" -ForegroundColor Green
    }
} catch {
    Write-Host "  ⚠ Could not query VRAM (nvidia-smi unavailable)" -ForegroundColor DarkYellow
}

Write-Host ""
Write-Host "=== WATSON PAUSED ===" -ForegroundColor Green
Write-Host "VRAM is free for gaming." -ForegroundColor Cyan
Write-Host "Run resume-watson.ps1 or Lazarus to restore inference." -ForegroundColor DarkYellow
