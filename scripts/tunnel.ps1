$ErrorActionPreference = "Stop"

$cloudflared = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cloudflared) {
    Write-Error "cloudflared est absent. Installez-le manuellement, puis relancez scripts\tunnel.ps1."
    exit 1
}

Write-Warning "Le tunnel rend la démo accessible depuis Internet. Ne partagez aucune donnée réelle."
& $cloudflared.Source tunnel --url http://localhost:3001
exit $LASTEXITCODE
