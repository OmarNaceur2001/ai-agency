$ErrorActionPreference = "Stop"

Write-Host "=== Disk space ==="
foreach ($drive in @("C", "D")) {
    $volume = Get-PSDrive -Name $drive -ErrorAction SilentlyContinue
    if ($null -eq $volume) {
        Write-Host ($drive + ": unavailable")
    } else {
        $freeGB = [math]::Round($volume.Free / 1GB, 2)
        Write-Host ("{0}: {1} GB free" -f $drive, $freeGB)
    }
}

$env:TEMP = "D:\temp"
$env:TMP = "D:\temp"
$env:npm_config_cache = "D:\npm-cache"
New-Item -ItemType Directory -Force -Path "D:\temp", "D:\npm-cache" | Out-Null

$node = "D:\node-v24.22.3-win-x64\node.exe"
$ollama = "D:\Ollama\ollama.exe"
$flowise = "D:\ai-agency-tools\flowise-runtime\node_modules\flowise\bin\run"

foreach ($path in @($node, $ollama, $flowise)) {
    if (-not (Test-Path $path)) { throw "Required installed component not found: $path" }
}

$nodeVersion = & $node --version
Write-Host "Node: $nodeVersion"
if ($nodeVersion -notmatch "^v24\.") { throw "Flowise 3.1.4 requires the installed Node 24 runtime." }

$tags = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 10
$modelNames = @($tags.models | ForEach-Object { $_.name })
Write-Host "Ollama models:"
$modelNames | ForEach-Object { Write-Host " - $_" }

if (-not ($modelNames | Where-Object { $_ -like "*LFM3-1.7B*" })) {
    throw "The configured LFM3 chat model is missing from Ollama /api/tags."
}
if (-not ($modelNames | Where-Object { $_ -like "bge-m3*" })) {
    throw "The bge-m3 embedding model is missing from Ollama /api/tags."
}

Write-Host "Preflight passed. No software was installed and no existing project or database data was changed."
