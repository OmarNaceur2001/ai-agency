$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose up -d failed (exit code $LASTEXITCODE). This optional path requires a working Docker/WSL installation."
    }
    Write-Host "Optional Docker services:"
    Write-Host "Flowise: http://localhost:3001"
    Write-Host "n8n:     http://localhost:5678"
    Write-Host "Qdrant:  http://localhost:6333/dashboard"
}
finally {
    Pop-Location
}
