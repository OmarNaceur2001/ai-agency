$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$webRoot = Join-Path $projectRoot "web"

if (-not (Test-Path (Join-Path $webRoot "config.js"))) {
    throw "web/config.js is missing. Set FLOWISE_CHATFLOW_ID and run python scripts\configure_web.py first."
}
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) { throw "Python was not found on PATH." }

Push-Location $webRoot
try {
    & $python.Source -m http.server 8080 --bind 127.0.0.1
}
finally {
    Pop-Location
}
