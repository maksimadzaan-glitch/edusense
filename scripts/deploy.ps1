# Manual one-click deploy (clipboard password).
# 1) Copy VPS root password
# 2) Run this script

$ErrorActionPreference = "Stop"
$plink = "C:\Program Files\PuTTY\plink.exe"

if (-not (Test-Path $plink)) {
  Write-Host "plink.exe not found at $plink" -ForegroundColor Red
  exit 1
}

$pw = (Get-Clipboard).Trim()
if (-not $pw) {
  Write-Host "Clipboard empty. Copy VPS password, then run again." -ForegroundColor Yellow
  exit 1
}

$cmd = "cd /opt/edusense && git fetch origin main && git reset --hard origin/main && systemctl restart edusense && systemctl is-active edusense && git rev-parse --short HEAD"
Write-Host "Deploying..."
& $plink -ssh root@168.113.208.95 -pw $pw $cmd
if ($LASTEXITCODE -eq 0) {
  Write-Host "Deploy OK" -ForegroundColor Green
} else {
  Write-Host "Deploy failed" -ForegroundColor Red
  exit $LASTEXITCODE
}
