param(
    [int]$TimeoutSeconds = 90
)

$ErrorActionPreference = "SilentlyContinue"

$targets = @(
    @{ Name = "Landing"; Url = "http://127.0.0.1:3000/" },
    @{ Name = "Authentication"; Url = "http://127.0.0.1:3001/" },
    @{ Name = "Platform"; Url = "http://127.0.0.1:3002/" },
    @{ Name = "Documentation"; Url = "http://127.0.0.1:3003/" },
    @{ Name = "API"; Url = "http://127.0.0.1:8000/health" },
    @{ Name = "Database"; Url = "http://127.0.0.1:8000/health/db" }
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
            if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 400) {
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
