$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$node = "D:\node-v24.22.3-win-x64\node.exe"
$ollama = "D:\Ollama\ollama.exe"
$flowise = "D:\ai-agency-tools\flowise-runtime\node_modules\flowise\bin\run"

foreach ($path in @($node, $ollama, $flowise)) {
    if (-not (Test-Path $path)) { throw "Required installed component not found: $path" }
}

$nodeVersion = & $node --version
if ($nodeVersion -notmatch "^v24\.") { throw "Flowise requires Node 24; detected $nodeVersion." }

Write-Host "Disk space before start:"
foreach ($drive in @("C", "D")) {
    $volume = Get-PSDrive -Name $drive -ErrorAction SilentlyContinue
    if ($volume) {
        Write-Host ("{0}: {1} GB free" -f $drive, [math]::Round($volume.Free / 1GB, 2))
    }
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

New-Item -ItemType Directory -Force -Path $env:DATABASE_PATH, $env:BLOB_STORAGE_PATH, $env:LOG_PATH | Out-Null

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$stdoutLog = Join-Path $env:LOG_PATH "flowise-$stamp.stdout.log"
$stderrLog = Join-Path $env:LOG_PATH "flowise-$stamp.stderr.log"

Write-Host "Flowise database: $env:DATABASE_PATH"
Write-Host "Flowise URL: http://localhost:3000"
Write-Host "Allowed browser origin: http://localhost:8080"
Write-Host "Starting Flowise in the background with Node $nodeVersion ..."

$process = Start-Process -FilePath $node -ArgumentList "$flowise start" -WorkingDirectory $projectRoot -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog

$deadline = (Get-Date).AddSeconds(90)
$healthy = $false
while ((Get-Date) -lt $deadline) {
    if (-not (Get-Process -Id $process.Id -ErrorAction SilentlyContinue)) { break }
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:3000/api/v1/version" -UseBasicParsing -TimeoutSec 5
        if ([int]$response.StatusCode -eq 200) {
            $healthy = $true
            break
        }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $healthy) {
    Write-Host "Flowise did not become healthy. Recent stderr:"
    if (Test-Path $stderrLog) { Get-Content $stderrLog -Tail 60 }
    Write-Host "Recent stdout:"
    if (Test-Path $stdoutLog) { Get-Content $stdoutLog -Tail 60 }
    if (Get-Process -Id $process.Id -ErrorAction SilentlyContinue) {
        Stop-Process -Id $process.Id -Force
    }
    throw "Flowise startup failed or /api/v1/version did not return HTTP 200."
}

Write-Host "Flowise HTTP 200. Background PID: $($process.Id)"
Write-Host "stdout: $stdoutLog"
Write-Host "stderr: $stderrLog"
$cFree = [math]::Round((Get-PSDrive C).Free / 1GB, 2)
$dFree = [math]::Round((Get-PSDrive D).Free / 1GB, 2)
Write-Host ("C: {0} GB free; D: {1} GB free after startup" -f $cFree, $dFree)
Write-Host "To stop this exact process later: Stop-Process -Id $($process.Id)"
