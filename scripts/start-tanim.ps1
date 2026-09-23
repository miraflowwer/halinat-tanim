$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RuntimeDir = Join-Path $Root ".tanim\runtime"
$LogDir = Join-Path $Root ".tanim\logs"
$PidFile = Join-Path $RuntimeDir "pids.json"

New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

function Ask-YesNo([string]$Prompt, [bool]$DefaultYes = $false) {
    $suffix = if ($DefaultYes) { " [Y/n]" } else { " [y/N]" }
    $answer = Read-Host ($Prompt + $suffix)
    if ([string]::IsNullOrWhiteSpace($answer)) {
        return $DefaultYes
    }
    return $answer.Trim().ToLowerInvariant() -in @("y", "yes")
}

function Find-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) { return "py" }
    if (Get-Command python -ErrorAction SilentlyContinue) { return "python" }
    return $null
}

function Find-Psql {
    $cmd = Get-Command psql -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $base = "C:\Program Files\PostgreSQL"
    if (Test-Path $base) {
        $candidate = Get-ChildItem -Path $base -Directory |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName "bin\psql.exe" } |
            Where-Object { Test-Path $_ } |
            Select-Object -First 1
        if ($candidate) { return $candidate }
    }

    return $null
}

function Install-WithWinget([string]$Name, [string]$PackageId) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "Windows Package Manager (winget) is not available."
        Write-Host "Install $Name manually, then run TANIM.bat again."
        return $false
    }

    if (-not (Ask-YesNo "Install $Name now with winget?")) {
        return $false
    }

    Write-Host "Installing $Name..."
    & winget install --id $PackageId -e --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Automatic installation of $Name failed."
        Write-Host "Install it manually, then run TANIM.bat again."
        return $false
    }

    Write-Host "$Name installation command completed."
    Write-Host "If PATH changed, close this window and run TANIM.bat again."
    return $true
}

function Require-Command([string]$DisplayName, [string]$CommandName, [string]$WingetId) {
    if (Get-Command $CommandName -ErrorAction SilentlyContinue) {
        Write-Host "[OK] $DisplayName"
        return $true
    }

    Write-Host "[MISSING] $DisplayName"
    Install-WithWinget $DisplayName $WingetId | Out-Null
    return $false
}

Set-Location $Root

Write-Host ""
Write-Host "TANIM local launcher"
Write-Host "===================="
Write-Host ""

$missing = $false

if (-not (Require-Command "Node.js" "node" "OpenJS.NodeJS.LTS")) { $missing = $true }
if (-not (Require-Command "npm" "npm" "OpenJS.NodeJS.LTS")) { $missing = $true }

$python = Find-Python
if ($python) {
    Write-Host "[OK] Python"
} else {
    Write-Host "[MISSING] Python"
    Install-WithWinget "Python 3.12" "Python.Python.3.12" | Out-Null
    $missing = $true
}

$psql = Find-Psql
if ($psql) {
    Write-Host "[OK] PostgreSQL client"
} else {
    Write-Host "[MISSING] PostgreSQL"
    Install-WithWinget "PostgreSQL 17" "PostgreSQL.PostgreSQL.17" | Out-Null
    $missing = $true
}

if ($missing) {
    Write-Host ""
    Write-Host "One or more required dependencies were missing."
    Write-Host "After installation is complete, run TANIM.bat again."
    exit 1
}

if (-not (Test-Path (Join-Path $Root "node_modules"))) {
    if (Ask-YesNo "Frontend dependencies are not installed. Run npm install now?") {
        & npm install
        if ($LASTEXITCODE -ne 0) { throw "npm install failed." }
    } else {
        Write-Host "Cannot start TANIM without frontend dependencies."
        exit 1
    }
}

$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    if (Ask-YesNo "Python virtual environment is not ready. Create it and install TANIM packages now?") {
        if ($python -eq "py") {
            & py -3.12 -m venv .venv
        } else {
            & python -m venv .venv
        }
        if ($LASTEXITCODE -ne 0) { throw "Failed to create .venv." }

        & $VenvPython -m pip install --upgrade pip
        & $VenvPython -m pip install -e ".[dev]"
        if ($LASTEXITCODE -ne 0) { throw "Python package installation failed." }
    } else {
        Write-Host "Cannot start TANIM without the local Python environment."
        exit 1
    }
}

if (-not (Test-Path (Join-Path $Root ".env"))) {
    Write-Host ""
    Write-Host "[NOTICE] .env does not exist."
    Write-Host "Copy .env.example to .env and configure the local database and weather provider."
    if (Ask-YesNo "Create .env from .env.example now?") {
        Copy-Item (Join-Path $Root ".env.example") (Join-Path $Root ".env")
        Write-Host ".env created. Edit it before expecting database or weather features to work."
    }
}

if (Test-Path $PidFile) {
    Write-Host ""
    Write-Host "A TANIM PID file already exists."
    Write-Host "Run STOP_TANIM.bat first, or remove stale runtime state after confirming TANIM is stopped."
    exit 1
}

$frontendOut = Join-Path $LogDir "frontends.out.log"
$frontendErr = Join-Path $LogDir "frontends.err.log"
$apiOut = Join-Path $LogDir "api.out.log"
$apiErr = Join-Path $LogDir "api.err.log"

Write-Host ""
Write-Host "Starting TANIM frontends..."
$frontends = Start-Process `
    -FilePath "npm" `
    -ArgumentList @("run", "dev:frontends") `
    -WorkingDirectory $Root `
    -PassThru `
    -RedirectStandardOutput $frontendOut `
    -RedirectStandardError $frontendErr

Write-Host "Starting TANIM API..."
$api = Start-Process `
    -FilePath $VenvPython `
    -ArgumentList @("-m", "uvicorn", "services.api.app:app", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $Root `
    -PassThru `
    -RedirectStandardOutput $apiOut `
    -RedirectStandardError $apiErr

@{
    frontends_pid = $frontends.Id
    api_pid = $api.Id
    started_at = (Get-Date).ToString("o")
} | ConvertTo-Json | Set-Content -Encoding UTF8 $PidFile

Write-Host ""
Write-Host "Waiting for TANIM health checks..."
& (Join-Path $PSScriptRoot "check-health.ps1") -TimeoutSeconds 90

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Startup is incomplete. Check logs under .tanim\logs."
    Write-Host "Run STOP_TANIM.bat to stop the TANIM processes."
    exit 1
}

Write-Host ""
Write-Host "TANIM is ready."
Write-Host "Opening the landing page..."
Start-Process "http://127.0.0.1:3000"
