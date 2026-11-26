$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$node = "D:\node-v24.22.3-win-x64\node.exe"
$ollama = "D:\Ollama\ollama.exe"
$flowise = "D:\ai-agency-tools\flowise-runtime\node_modules\flowise\bin\run"

foreach ($path in @($node, $ollama, $flowise)) {
    if (-not (Test-Path $path)) { throw "Required installed component not found: $path" }
}

$listener = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if ($listener) {
    $pids = ($listener | Select-Object -ExpandProperty OwningProcess -Unique) -join ", "
    throw "Port 3000 is already listening (PID $pids). Do not start a second Flowise instance. Identify its database path and stop it from its owning terminal first."
}

$env:TEMP = "D:\temp"
$env:TMP = "D:\temp"
$env:npm_config_cache = "D:\npm-cache"
$env:PATH = "D:\node-v24.22.3-win-x64;D:\Ollama;$env:PATH"
New-Item -ItemType Directory -Force -Path "D:\temp", "D:\npm-cache" | Out-Null

# Preserve the documented database path by default; override only to reconnect
# to an existing database whose location is already known.
if (-not $env:FLOWISE_DATABASE_PATH) {
    $env:FLOWISE_DATABASE_PATH = "D:\ai-agency-tools\flowise\data"
}
$env:DATABASE_PATH = $env:FLOWISE_DATABASE_PATH
$env:BLOB_STORAGE_PATH = "D:\ai-agency-tools\flowise\storage"
$env:LOG_PATH = "D:\ai-agency-tools\flowise\logs"

# Strict local binding and the one allowed local widget origin.
$env:HOST = "127.0.0.1"
$env:PORT = "3000"
$env:CORS_ORIGINS = "http://localhost:8080"
$env:IFRAME_ORIGINS = "http://localhost:8080"

Write-Host "Flowise database: $env:DATABASE_PATH"
Write-Host "Flowise URL: http://localhost:3000"
Write-Host "Allowed browser origin: http://localhost:8080"
Write-Host "Temporary/cache paths: D:\temp and D:\npm-cache"
Write-Host "Starting Flowise in the foreground. Press Ctrl+C to stop."

Push-Location $projectRoot
try {
    & $node $flowise start
    if ($LASTEXITCODE -ne 0) { throw "Flowise exited with code $LASTEXITCODE." }
}
finally {
    foreach ($drive in @("C", "D")) {
        $volume = Get-PSDrive -Name $drive -ErrorAction SilentlyContinue
        if ($volume) {
            Write-Host ("{0}: {1} GB free at shutdown" -f $drive, [math]::Round($volume.Free / 1GB, 2))
        }
    }
    Pop-Location
}
