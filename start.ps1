# Lifeline Quick Start Script for Windows PowerShell

Write-Host "================================" -ForegroundColor Cyan
Write-Host "  LIFELINE TRAFFIC MANAGEMENT  " -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (-Not (Test-Path "venv")) {
    Write-Host "[1/4] Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[1/4] Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "[2/4] Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Note: If you get execution policy error, run:" -ForegroundColor Yellow
    Write-Host "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}

# Install dependencies
Write-Host "[3/4] Installing dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Start the system
Write-Host "[4/4] Starting Lifeline system..." -ForegroundColor Yellow
Write-Host ""
Write-Host "================================" -ForegroundColor Green
Write-Host "System starting..." -ForegroundColor Green
Write-Host "Dashboard: http://localhost:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
Write-Host ""

python main.py

Write-Host ""
Write-Host "System stopped." -ForegroundColor Yellow
