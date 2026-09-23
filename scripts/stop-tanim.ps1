$ErrorActionPreference = "Continue"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PidFile = Join-Path $Root ".tanim\runtime\pids.json"

Write-Host ""
Write-Host "Stopping TANIM"
Write-Host "=============="
Write-Host ""

if (-not (Test-Path $PidFile)) {
    Write-Host "No TANIM PID file was found."
    Write-Host "No unrelated Node.js, Python, or PostgreSQL processes will be stopped."
    exit 0
}

$pids = Get-Content $PidFile -Raw | ConvertFrom-Json

$targets = @(
    @{ Name = "Frontends"; Pid = $pids.frontends_pid },
    @{ Name = "API"; Pid = $pids.api_pid }
)

foreach ($target in $targets) {
    if (-not $target.Pid) { continue }

    $process = Get-Process -Id $target.Pid -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "Stopping $($target.Name) process tree (PID $($target.Pid))..."
        & taskkill /PID $target.Pid /T /F | Out-Null
    } else {
        Write-Host "$($target.Name) PID $($target.Pid) is not running."
    }
}

Remove-Item $PidFile -Force -ErrorAction SilentlyContinue

Write-Host ""
Write-Host "TANIM-owned development processes have been stopped."
