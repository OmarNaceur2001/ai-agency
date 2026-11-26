$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
Push-Location $projectRoot
try {
    docker compose up -d
    if ($LASTEXITCODE -ne 0) {
        throw "docker compose up -d a échoué (code $LASTEXITCODE)."
    }

    Write-Output "Services demandés:"
    Write-Output "Flowise : http://localhost:3001"
    Write-Output "n8n     : http://localhost:5678"
    Write-Output "Qdrant  : http://localhost:6333/dashboard"
} finally {
    Pop-Location
}
