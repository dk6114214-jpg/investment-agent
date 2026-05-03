$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$backendPython = Join-Path $root "venv\Scripts\python.exe"
$frontendDir = Join-Path $root "frontend\web"
$serveEntry = Join-Path $frontendDir "node_modules\serve\build\main.js"
$backendLog = Join-Path $root "backend.log"
$backendErr = Join-Path $root "backend.err"

if (-not (Test-Path $backendPython)) {
  throw "Backend Python not found at $backendPython"
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

  Write-Output "Backend started with PID $($backend.Id)"
}

Write-Output ""
Write-Output "Dashboard is starting in this terminal."
Write-Output "Keep this terminal open while using the app."
Write-Output "Open: http://127.0.0.1:3000"
Write-Output ""

Push-Location $frontendDir
node.exe $serveEntry -s build -l 3000
Pop-Location
