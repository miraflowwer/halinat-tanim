$ErrorActionPreference = "Continue"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$PidFile = Join-Path $Root ".tanim\runtime\pids.json"

Write-Host ""
Write-Host "Stopping TANIM"
Write-Host "=============="
Write-Host ""

if (-not (Test-Path $PidFile)) {
    Write-Host "No TANIM PID file was found."
    Write-Host "No unrelated Node.js, Python, or PostgreSQL processes were stopped."
    exit 0
}

try {
    $state = Get-Content -LiteralPath $PidFile -Raw | ConvertFrom-Json
} catch {
    Write-Host "The TANIM PID file is invalid. No processes were stopped."
    Write-Host "Review .tanim\runtime\pids.json before trying again."
    exit 1
}

if ($state.tanim_root -ne $Root) {
    Write-Host "The PID file belongs to another TANIM folder. No processes were stopped."
    exit 1
}

$targets = @(
    @{ Name = "Frontends"; Record = $state.frontends; Marker = "run-frontends.ps1" },
    @{ Name = "API"; Record = $state.api; Marker = "services.api.app:app" }
)
$hadOwnershipMismatch = $false

foreach ($target in $targets) {
    $record = $target.Record
    if ($null -eq $record -or -not $record.pid) { continue }

    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($record.pid)" -ErrorAction SilentlyContinue
    $process = Get-Process -Id $record.pid -ErrorAction SilentlyContinue
    if (-not $processInfo -or -not $process) {
        Write-Host "$($target.Name) TANIM process is not running."
        continue
    }

    $ownerMatches = $true
    try {
        $expectedStart = [DateTimeOffset]::Parse($record.started_at_utc).UtcDateTime
        $actualStart = $process.StartTime.ToUniversalTime()
        if ([Math]::Abs(($actualStart - $expectedStart).TotalSeconds) -gt 3) { $ownerMatches = $false }
    } catch {
        $ownerMatches = $false
    }

    if ($record.executable -and $processInfo.ExecutablePath -and
        -not [string]::Equals($record.executable, $processInfo.ExecutablePath, [StringComparison]::OrdinalIgnoreCase)) {
        $ownerMatches = $false
    }
    if ($processInfo.CommandLine -notlike "*$($target.Marker)*") { $ownerMatches = $false }

    if (-not $ownerMatches) {
        Write-Host "$($target.Name) PID $($record.pid) no longer matches its TANIM process record. It was left running."
        $hadOwnershipMismatch = $true
        continue
    }

    Write-Host "Stopping verified TANIM $($target.Name) process tree (PID $($record.pid))..."
    & taskkill.exe /PID $record.pid /T /F | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Could not stop the TANIM $($target.Name) process tree."
        $hadOwnershipMismatch = $true
    }
}

if (-not $hadOwnershipMismatch) {
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
    Write-Host ""
    Write-Host "TANIM-owned development processes have been stopped."
    exit 0
}

Write-Host ""
Write-Host "Some process records did not match. No unrelated processes were stopped."
exit 1
