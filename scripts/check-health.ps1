param(
    [int]$TimeoutSeconds = 90
)

$ErrorActionPreference = "SilentlyContinue"

$targets = @(
    @{ Name = "Landing"; Url = "http://127.0.0.1:3000/"; Kind = "web" },
    @{ Name = "Authentication"; Url = "http://127.0.0.1:3001/"; Kind = "web" },
    @{ Name = "Platform"; Url = "http://127.0.0.1:3002/"; Kind = "web" },
    @{ Name = "Documentation"; Url = "http://127.0.0.1:3003/"; Kind = "web" },
    @{ Name = "API"; Url = "http://127.0.0.1:8000/health"; Kind = "api" },
    @{ Name = "Database"; Url = "http://127.0.0.1:8000/health/db"; Kind = "database" },
    @{ Name = "TANIM readiness"; Url = "http://127.0.0.1:8000/health/readiness"; Kind = "readiness" }
)

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$remaining = @{}

foreach ($target in $targets) {
    $remaining[$target.Name] = $target.Url
}

while ((Get-Date) -lt $deadline -and $remaining.Count -gt 0) {
    foreach ($name in @($remaining.Keys)) {
        $url = $remaining[$name]
        try {
            $response = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 3
            $healthy = $response.StatusCode -ge 200 -and $response.StatusCode -lt 300
            $kind = ($targets | Where-Object { $_.Name -eq $name } | Select-Object -First 1).Kind

            if ($healthy -and $kind -in @("api", "database", "readiness")) {
                $body = $response.Content | ConvertFrom-Json
                $healthy = if ($kind -eq "readiness") {
                    $body.status -eq "ready"
                } else {
                    $body.status -eq "healthy"
                }
                if ($kind -eq "database") { $healthy = $healthy -and $body.database -eq "reachable" }
            }

            if ($healthy) {
                Write-Host "[OK] $name"
                $remaining.Remove($name)
            }
        } catch {
        }
    }

    if ($remaining.Count -gt 0) {
        Start-Sleep -Seconds 2
    }
}

if ($remaining.Count -gt 0) {
    Write-Host ""
    Write-Host "TANIM did not become fully healthy in time."
    foreach ($name in $remaining.Keys) {
        Write-Host "[FAILED] $name -> $($remaining[$name])"
    }
    exit 1
}

Write-Host ""
Write-Host "All required TANIM services are healthy."
exit 0
