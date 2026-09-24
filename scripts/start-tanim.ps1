$ErrorActionPreference = "Stop"

$Root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RuntimeDir = Join-Path $Root ".tanim\runtime"
$LogDir = Join-Path $Root ".tanim\logs"
$PidFile = Join-Path $RuntimeDir "pids.json"
$VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
$script:PythonLauncher = $null
$script:PythonLauncherArgs = @()

function Ask-YesNo([string]$Prompt, [bool]$DefaultYes = $false) {
    $suffix = if ($DefaultYes) { " [Y/n]" } else { " [y/N]" }
    $answer = Read-Host ($Prompt + $suffix)
    if ([string]::IsNullOrWhiteSpace($answer)) { return $DefaultYes }
    return $answer.Trim().ToLowerInvariant() -in @("y", "yes")
}

function Install-WithWinget([string]$Name, [string]$PackageId) {
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "Windows Package Manager (winget) is not available."
        Write-Host "Install $Name manually, then run TANIM.bat again."
        return $false
    }

    if (-not (Ask-YesNo "Install $Name now with winget?")) { return $false }

    Write-Host "Installing $Name..."
    & winget install --id $PackageId -e --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Automatic installation of $Name failed."
        Write-Host "Install it manually, then run TANIM.bat again."
        return $false
    }

    Write-Host "$Name installation completed. Close this window and run TANIM.bat again."
    return $true
}

function Get-VersionParts([string]$VersionText) {
    $match = [regex]::Match($VersionText, "(\d+)\.(\d+)(?:\.(\d+))?")
    if (-not $match.Success) { return $null }
    return @([int]$match.Groups[1].Value, [int]$match.Groups[2].Value)
}

function Test-MinimumVersion([string]$VersionText, [int]$Major, [int]$Minor) {
    $parts = Get-VersionParts $VersionText
    if ($null -eq $parts) { return $false }
    if ($parts[0] -gt $Major) { return $true }
    if ($parts[0] -lt $Major) { return $false }
    return $parts[1] -ge $Minor
}

function Check-NodeVersion {
    $command = Get-Command node -ErrorAction SilentlyContinue
    if (-not $command) {
        Write-Host "[MISSING] Node.js 20 or later"
        Install-WithWinget "Node.js 20 or later" "OpenJS.NodeJS.LTS" | Out-Null
        return $false
    }
    $version = (& node --version 2>&1 | Out-String).Trim()
    if (-not (Test-MinimumVersion $version 20 0)) {
        Write-Host "[MISSING] Node.js 20 or later. Found: $version"
        Install-WithWinget "Node.js 20 or later" "OpenJS.NodeJS.LTS" | Out-Null
        return $false
    }
    Write-Host "[OK] Node.js $version"
    return $true
}

function Check-NpmVersion([bool]$NodeReady) {
    $command = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $command) {
        Write-Host "[MISSING] npm 10 or later"
        if ($NodeReady) {
            Install-WithWinget "Node.js with npm 10 or later" "OpenJS.NodeJS.LTS" | Out-Null
        } else {
            Write-Host "npm is included with Node.js. Install Node.js, then run TANIM.bat again."
        }
        return $false
    }
    $version = (& npm --version 2>&1 | Out-String).Trim()
    if (-not (Test-MinimumVersion $version 10 0)) {
        Write-Host "[MISSING] npm 10 or later. Found: $version"
        if ($NodeReady) {
            Install-WithWinget "Node.js with npm 10 or later" "OpenJS.NodeJS.LTS" | Out-Null
        } else {
            Write-Host "npm is included with Node.js. Install Node.js, then run TANIM.bat again."
        }
        return $false
    }
    Write-Host "[OK] npm $version"
    return $true
}

function Invoke-SelectedPython([string[]]$Arguments) {
    $combinedArguments = @($script:PythonLauncherArgs) + @($Arguments)
    & $script:PythonLauncher @combinedArguments
}

function Check-PythonVersion {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        $runtimes = @()
        foreach ($line in (& $py.Source -0p 2>&1)) {
            if ($line -match '^\s*-V:(\S+)(?:\s+\*)?\s+') {
                $tag = $Matches[1]
                $parts = Get-VersionParts $tag
                if ($null -ne $parts -and (Test-MinimumVersion $tag 3 12)) {
                    $version = (& $py.Source "-V:$tag" --version 2>&1 | Out-String).Trim()
                    if ($LASTEXITCODE -eq 0 -and
                        (Test-MinimumVersion $version 3 12) -and
                        $version -notmatch '(?i)\d+(?:a|b|rc)\d+') {
                        $runtimes += @{
                            Major = $parts[0]
                            Minor = $parts[1]
                            Tag = $tag
                            Version = $version
                        }
                    }
                }
            }
        }

        $selectedRuntime = $runtimes |
            Sort-Object @{ Expression = "Major"; Descending = $true }, @{ Expression = "Minor"; Descending = $true } |
            Select-Object -First 1
        if ($selectedRuntime) {
            $script:PythonLauncher = $py.Source
            $script:PythonLauncherArgs = @("-V:$($selectedRuntime.Tag)")
            Write-Host "[OK] $($selectedRuntime.Version)"
            return $true
        }
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        $version = (& python --version 2>&1 | Out-String).Trim()
        if (Test-MinimumVersion $version 3 12) {
            $script:PythonLauncher = $python.Source
            $script:PythonLauncherArgs = @()
            Write-Host "[OK] $version"
            return $true
        }
        Write-Host "[MISSING] Python 3.12 or later. Found: $version"
    } else {
        Write-Host "[MISSING] Python 3.12 or later"
    }

    Install-WithWinget "Python 3.12" "Python.Python.3.12" | Out-Null
    return $false
}

function Find-PostgresExecutable([string]$Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($command) { return $command.Source }

    $base = "C:\Program Files\PostgreSQL"
    if (Test-Path $base) {
        $candidate = Get-ChildItem -Path $base -Directory |
            Sort-Object Name -Descending |
            ForEach-Object { Join-Path $_.FullName ("bin\" + $Name + ".exe") } |
            Where-Object { Test-Path $_ } |
            Select-Object -First 1
        if ($candidate) { return $candidate }
    }
    return $null
}

function Check-PostgresTools {
    $script:Psql = Find-PostgresExecutable "psql"
    $script:PgIsReady = Find-PostgresExecutable "pg_isready"
    if (-not $script:Psql -or -not $script:PgIsReady) {
        Write-Host "[MISSING] PostgreSQL client tools (psql and pg_isready)"
        Install-WithWinget "PostgreSQL 17" "PostgreSQL.PostgreSQL.17" | Out-Null
        return $false
    }

    $version = (& $script:Psql --version 2>&1 | Out-String).Trim()
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[MISSING] PostgreSQL client tools could not be started."
        return $false
    }
    Write-Host "[OK] $version"
    return $true
}

function Get-DatabaseUrl {
    if (-not [string]::IsNullOrWhiteSpace($env:DATABASE_URL)) { return $env:DATABASE_URL.Trim() }
    $envFile = Join-Path $Root ".env"
    if (-not (Test-Path $envFile)) { return "" }
    foreach ($line in Get-Content -LiteralPath $envFile) {
        if ($line -match '^\s*DATABASE_URL\s*=\s*(.*?)\s*$') {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return ""
}

function Get-ConfiguredValue([string]$Name) {
    $environmentValue = [Environment]::GetEnvironmentVariable($Name)
    if (-not [string]::IsNullOrWhiteSpace($environmentValue)) { return $environmentValue.Trim() }
    $envFile = Join-Path $Root ".env"
    if (-not (Test-Path $envFile)) { return "" }
    foreach ($line in Get-Content -LiteralPath $envFile) {
        if ($line -match ("^\s*" + [regex]::Escape($Name) + "\s*=\s*(.*?)\s*$")) {
            return $Matches[1].Trim().Trim('"').Trim("'")
        }
    }
    return ""
}

function Get-PostgresEndpoint([string]$DatabaseUrl) {
    if ($DatabaseUrl -match '^\w+://') {
        $uri = [System.Uri]$DatabaseUrl
        $hostName = if ([string]::IsNullOrWhiteSpace($uri.Host)) { "127.0.0.1" } else { $uri.Host }
        $port = if ($uri.IsDefaultPort) { 5432 } else { $uri.Port }
        return @{ Host = $hostName; Port = $port }
    }

    $hostMatch = [regex]::Match($DatabaseUrl, '(?:^|\s)host=([^\s]+)')
    $portMatch = [regex]::Match($DatabaseUrl, '(?:^|\s)port=(\d+)')
    $hostName = if ($hostMatch.Success) { $hostMatch.Groups[1].Value } else { "127.0.0.1" }
    $port = if ($portMatch.Success) { [int]$portMatch.Groups[1].Value } else { 5432 }
    return @{ Host = $hostName; Port = $port }
}

function Check-PostgresAvailability([string]$DatabaseUrl) {
    if ([string]::IsNullOrWhiteSpace($DatabaseUrl)) {
        Write-Host "[MISSING] DATABASE_URL is not configured. Set it in .env and run TANIM.bat again."
        return $false
    }

    try {
        $endpoint = Get-PostgresEndpoint $DatabaseUrl
    } catch {
        Write-Host "[MISSING] DATABASE_URL is not a valid PostgreSQL URL or connection string."
        return $false
    }

    & $script:PgIsReady -h $endpoint.Host -p $endpoint.Port -t 3 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[UNAVAILABLE] PostgreSQL is not accepting connections at the configured address."
        Write-Host "Start the local PostgreSQL server, then run TANIM.bat again."
        return $false
    }

    Write-Host "[OK] PostgreSQL server is accepting connections at $($endpoint.Host):$($endpoint.Port)"
    return $true
}

function Save-PidState($State) {
    $temporaryPath = "$PidFile.tmp"
    $State | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $temporaryPath -Encoding UTF8
    Move-Item -LiteralPath $temporaryPath -Destination $PidFile -Force
}

function New-ProcessRecord($Process, [string]$Executable, [string]$Marker) {
    return @{
        pid = $Process.Id
        started_at_utc = $Process.StartTime.ToUniversalTime().ToString("o")
        executable = [System.IO.Path]::GetFullPath($Executable)
        command_marker = $Marker
    }
}

Set-Location $Root
New-Item -ItemType Directory -Force -Path $RuntimeDir | Out-Null
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Host ""
Write-Host "TANIM local launcher"
Write-Host "===================="
Write-Host ""

$missing = $false
$nodeReady = Check-NodeVersion
if (-not $nodeReady) { $missing = $true }
if (-not (Check-NpmVersion $nodeReady)) { $missing = $true }
if (-not (Check-PythonVersion)) { $missing = $true }
if (-not (Check-PostgresTools)) { $missing = $true }

if ($missing) {
    Write-Host ""
    Write-Host "A required dependency is missing or below its required version."
    Write-Host "After installation, close this window and run TANIM.bat again."
    exit 1
}

if (-not (Test-Path (Join-Path $Root ".env")) -and [string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
    Write-Host "[NOTICE] .env does not exist."
    if (Ask-YesNo "Create .env from .env.example now?" -DefaultYes $false) {
        Copy-Item -LiteralPath (Join-Path $Root ".env.example") -Destination (Join-Path $Root ".env") -NoClobber
        Write-Host ".env was created without replacing an existing file. Set DATABASE_URL before starting TANIM."
        exit 1
    }
    Write-Host "Set DATABASE_URL in .env or in this PowerShell session, then run TANIM.bat again."
    exit 1
}

$databaseUrl = Get-DatabaseUrl
if (-not (Check-PostgresAvailability $databaseUrl)) { exit 1 }

$dependencyMarker = $false
$lockfile = Join-Path $Root "package-lock.json"
$lockFingerprintFile = Join-Path $RuntimeDir "npm-lock.sha256"
$lockFingerprint = if (Test-Path $lockfile) { (Get-FileHash -Algorithm SHA256 -LiteralPath $lockfile).Hash } else { "" }
$installedFingerprint = if (Test-Path $lockFingerprintFile) { (Get-Content -Raw -LiteralPath $lockFingerprintFile).Trim() } else { "" }
$frontendNeedsInstall = -not (Test-Path (Join-Path $Root "node_modules")) -or
    -not (Test-Path $lockfile) -or
    [string]::IsNullOrWhiteSpace($installedFingerprint) -or
    $installedFingerprint -ne $lockFingerprint
if ($frontendNeedsInstall) {
    if (Ask-YesNo "Frontend dependencies are missing or do not match package-lock.json. Run npm ci now?" -DefaultYes $false) {
        & npm ci
        if ($LASTEXITCODE -ne 0) { throw "npm ci failed. Review the output, then retry." }
        $lockFingerprint | Set-Content -LiteralPath $lockFingerprintFile -Encoding ASCII
    } else {
        Write-Host "Cannot start TANIM without the local frontend dependencies."
        exit 1
    }
}

if (-not (Test-Path $VenvPython)) {
    if (-not (Ask-YesNo "The TANIM Python environment is not ready. Create it and install project packages now?" -DefaultYes $false)) {
        Write-Host "Cannot start TANIM without the local Python environment."
        exit 1
    }
    Invoke-SelectedPython -Arguments @("-m", "venv", ".venv")
    if ($LASTEXITCODE -ne 0) { throw "Failed to create .venv." }
    $dependencyMarker = $true
} else {
    & $VenvPython -c "import fastapi, psycopg, uvicorn, dotenv"
    if ($LASTEXITCODE -ne 0) {
        if (-not (Ask-YesNo "TANIM Python packages are missing. Install them in .venv now?" -DefaultYes $false)) {
            Write-Host "Cannot start TANIM without the local Python packages."
            exit 1
        }
        $dependencyMarker = $true
    }
}

if ($dependencyMarker) {
    & $VenvPython -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw "Failed to prepare pip in .venv." }
    & $VenvPython -m pip install -e ".[dev]"
    if ($LASTEXITCODE -ne 0) { throw "Python package installation failed." }
}

if (Test-Path $PidFile) {
    Write-Host "A TANIM runtime PID file already exists."
    Write-Host "Run STOP_TANIM.bat, then run TANIM.bat again."
    exit 1
}

Write-Host "Applying database migrations..."
& $VenvPython "scripts/init_db.py"
if ($LASTEXITCODE -ne 0) { throw "Database migrations did not complete. TANIM was not started." }

Write-Host "Seeding the configured TANIM agricultural dataset..."
& $VenvPython "scripts/seed_data.py"
if ($LASTEXITCODE -ne 0) { throw "The configured TANIM dataset was not seeded. TANIM was not started." }

$demoFarmerPassword = Get-ConfiguredValue "TANIM_DEMO_FARMER_PASSWORD"
$demoCoopPassword = Get-ConfiguredValue "TANIM_DEMO_COOP_PASSWORD"
if (-not [string]::IsNullOrWhiteSpace($demoFarmerPassword) -and
    -not [string]::IsNullOrWhiteSpace($demoCoopPassword)) {
    Write-Host "Preparing configured demo accounts..."
    & $VenvPython "scripts/seed_demo_accounts.py"
    if ($LASTEXITCODE -ne 0) { throw "Configured demo accounts could not be prepared. TANIM was not started." }
} else {
    Write-Host "[NOTICE] Demo account passwords are not both configured. TANIM can run, but demo credentials were not prepared."
    Write-Host "Set TANIM_DEMO_FARMER_PASSWORD and TANIM_DEMO_COOP_PASSWORD in .env to prepare judge accounts."
}

$state = @{
    version = 1
    tanim_root = $Root
    frontends = $null
    api = $null
}

$frontendOut = Join-Path $LogDir "frontends.out.log"
$frontendErr = Join-Path $LogDir "frontends.err.log"
$apiOut = Join-Path $LogDir "api.out.log"
$apiErr = Join-Path $LogDir "api.err.log"
$powershellExe = Join-Path $PSHOME "powershell.exe"
$frontendRunner = Join-Path $PSScriptRoot "run-frontends.ps1"

try {
    Write-Host "Starting TANIM frontends..."
    $frontends = Start-Process `
        -FilePath $powershellExe `
        -ArgumentList @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $frontendRunner) `
        -WorkingDirectory $Root `
        -PassThru `
        -RedirectStandardOutput $frontendOut `
        -RedirectStandardError $frontendErr
    $state.frontends = New-ProcessRecord $frontends $powershellExe "run-frontends.ps1"
    Save-PidState $state

    Write-Host "Starting TANIM API..."
    $apiArguments = @("-m", "uvicorn", "services.api.app:app", "--host", "127.0.0.1", "--port", "8000")
    if (Test-Path (Join-Path $Root ".env")) {
        $apiArguments += @("--env-file", ".env")
    }
    $api = Start-Process `
        -FilePath $VenvPython `
        -ArgumentList $apiArguments `
        -WorkingDirectory $Root `
        -PassThru `
        -RedirectStandardOutput $apiOut `
        -RedirectStandardError $apiErr
    $state.api = New-ProcessRecord $api $VenvPython "services.api.app:app"
    Save-PidState $state

    Write-Host ""
    Write-Host "Waiting for TANIM health checks..."
    & (Join-Path $PSScriptRoot "check-health.ps1") -TimeoutSeconds 90
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Startup is incomplete. Check logs under .tanim\logs."
        & (Join-Path $PSScriptRoot "stop-tanim.ps1")
        exit 1
    }

    Write-Host ""
    Write-Host "TANIM is ready. Opening the landing page..."
    Start-Process "http://127.0.0.1:3000"
} catch {
    Write-Host "TANIM startup failed: $($_.Exception.Message)"
    if (Test-Path $PidFile) { & (Join-Path $PSScriptRoot "stop-tanim.ps1") }
    exit 1
}
