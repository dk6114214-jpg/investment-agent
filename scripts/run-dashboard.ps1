$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backendPython = Join-Path $root "venv\Scripts\python.exe"
$frontendDir = Join-Path $root "frontend\web"
$pidFile = Join-Path $PSScriptRoot "dashboard-pids.json"
$backendLog = Join-Path $root "backend.log"
$backendErr = Join-Path $root "backend.err"
$frontendLog = Join-Path $root "frontend.log"
$frontendErr = Join-Path $root "frontend.err"
$serveEntry = Join-Path $frontendDir "node_modules\serve\build\main.js"

if (-not (Test-Path $backendPython)) {
  throw "Backend Python not found at $backendPython"
}

if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
  throw "Frontend package.json not found at $frontendDir"
}

if (-not (Test-Path $serveEntry)) {
  throw "Serve package not found. Run: cd frontend\web; npm install"
}

if (-not (Test-Path (Join-Path $frontendDir "build\index.html"))) {
  Write-Output "Frontend build not found. Building now..."
  Push-Location $frontendDir
  npm.cmd run build
  Pop-Location
}

$backendPid = $null
$backendReady = $false
try {
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -Method Get -TimeoutSec 2 | Out-Null
  $backendReady = $true
  Write-Output "Backend already running on http://127.0.0.1:8000"
} catch {
  $backendReady = $false
}

if (-not $backendReady) {
  $backend = Start-Process -FilePath $backendPython `
    -ArgumentList @("-m", "uvicorn", "backend.api.main:app", "--host", "127.0.0.1", "--port", "8000") `
    -WorkingDirectory $root `
    -RedirectStandardOutput $backendLog `
    -RedirectStandardError $backendErr `
    -WindowStyle Hidden `
    -PassThru
  $backendPid = $backend.Id
} else {
  $backendPid = "already-running"
}

$frontend = Start-Process -FilePath "node.exe" `
  -ArgumentList @($serveEntry, "-s", "build", "-l", "3000") `
  -WorkingDirectory $frontendDir `
  -RedirectStandardOutput $frontendLog `
  -RedirectStandardError $frontendErr `
  -WindowStyle Hidden `
  -PassThru

$payload = @{
  backend_pid = $backendPid
  frontend_pid = $frontend.Id
  backend_url = "http://127.0.0.1:8000"
  frontend_url = "http://127.0.0.1:3000"
  started_at = (Get-Date).ToString("o")
}

$payload | ConvertTo-Json | Set-Content -Path $pidFile -Encoding UTF8

Start-Sleep -Seconds 3

$frontendStatus = try {
  (Invoke-WebRequest -Uri "http://127.0.0.1:3000/" -UseBasicParsing -TimeoutSec 5).StatusCode
} catch {
  $_.Exception.Message
}

$backendStatus = try {
  (Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -Method Get -TimeoutSec 5).status
} catch {
  $_.Exception.Message
}

Write-Output "Backend PID: $backendPid"
Write-Output "Frontend PID: $($frontend.Id)"
Write-Output "Backend URL: http://127.0.0.1:8000"
Write-Output "Frontend URL: http://127.0.0.1:3000"
Write-Output "Backend Status: $backendStatus"
Write-Output "Frontend Status: $frontendStatus"
