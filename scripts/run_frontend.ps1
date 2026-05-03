$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $root "frontend\web"

if (-not (Test-Path (Join-Path $frontendDir "package.json"))) {
  throw "Frontend package.json not found at $frontendDir"
}

Set-Location $frontendDir
$env:REACT_APP_API_URL = "http://127.0.0.1:8000"
npm.cmd run dev
