$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backendPython = Join-Path $root "venv\Scripts\python.exe"
$frontendDir = Join-Path $root "frontend\web"
$pidFile = Join-Path $PSScriptRoot "dashboard-pids.json"
$backendLog = Join-Path $root "backend.log"
$backendErr = Join-Path $root "backend.err"
$frontendLog = Join-Path $root "frontend.log"
$frontendErr = Join-Path $root "frontend.err"

if (-not (Test-Path $backendPython)) {
  throw "Backend Python not found at $backendPython"
}

if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
  throw "Frontend package.json not found at $frontendDir"
}

$backend = Start-Process -FilePath $backendPython `
  -ArgumentList "-m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000" `
  -WorkingDirectory $root `
  -RedirectStandardOutput $backendLog `
  -RedirectStandardError $backendErr `
  -WindowStyle Hidden `
  -PassThru

$frontend = Start-Process -FilePath "npm.cmd" `
  -ArgumentList "run", "dev" `
  -WorkingDirectory $frontendDir `
  -RedirectStandardOutput $frontendLog `
  -RedirectStandardError $frontendErr `
  -WindowStyle Hidden `
  -PassThru

$payload = @{
  backend_pid = $backend.Id
  frontend_pid = $frontend.Id
  backend_url = "http://127.0.0.1:8000"
  frontend_url = "http://127.0.0.1:3000"
  started_at = (Get-Date).ToString("o")
}

$payload | ConvertTo-Json | Set-Content -Path $pidFile -Encoding UTF8

Write-Output "Backend PID: $($backend.Id)"
Write-Output "Frontend PID: $($frontend.Id)"
Write-Output "Backend URL: http://127.0.0.1:8000"
Write-Output "Frontend URL: http://127.0.0.1:3000"
