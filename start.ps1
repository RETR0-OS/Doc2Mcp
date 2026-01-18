# Doc2MCP Platform - Quick Start Script
# This script sets up the entire platform with one command

$ErrorActionPreference = "Stop"

Write-Host "Doc2MCP Platform Setup" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
try {
    $null = Get-Command docker -ErrorAction Stop
    Write-Host "[OK] Docker found" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not installed. Please install Docker first." -ForegroundColor Red
    Write-Host "        Visit: https://docs.docker.com/get-docker/" -ForegroundColor Yellow
    exit 1
}

# Check if Docker Compose is installed
try {
    $null = Get-Command docker-compose -ErrorAction Stop
    Write-Host "[OK] Docker Compose found" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker Compose is not installed. Please install Docker Compose first." -ForegroundColor Red
    Write-Host "        Visit: https://docs.docker.com/compose/install/" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check for .env file
if (-not (Test-Path .env)) {
    Write-Host "[INFO] Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    Write-Host "[WARNING] Please edit .env and add your API keys:" -ForegroundColor Yellow
    Write-Host "          - GOOGLE_API_KEY (get from https://aistudio.google.com/app/apikey)"
    Write-Host "          - CLERK_SECRET_KEY (get from https://dashboard.clerk.com)"
    Write-Host "          - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
    Write-Host ""
    Read-Host "Press Enter once you've added your keys"
}

# Check for web/.env file
if (-not (Test-Path web\.env)) {
    Write-Host "[INFO] Creating web/.env file from template..." -ForegroundColor Yellow
    Copy-Item web\.env.example web\.env
    Write-Host "[WARNING] Please edit web/.env and add your Clerk keys" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter once you've added your keys"
}

Write-Host "[BUILD] Building Docker containers..." -ForegroundColor Cyan
docker-compose build

Write-Host ""
Write-Host "[START] Starting all services..." -ForegroundColor Cyan
docker-compose up -d

Write-Host ""
Write-Host "[WAIT] Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "[INIT] Creating data directory..." -ForegroundColor Cyan
if (-not (Test-Path web\data)) {
    New-Item -ItemType Directory -Path web\data -Force | Out-Null
}

Write-Host "[INIT] Initializing database..." -ForegroundColor Cyan
docker-compose exec -T web node ./node_modules/prisma/build/index.js generate
docker-compose exec -T web node ./node_modules/prisma/build/index.js db push

Write-Host ""
Write-Host "[SUCCESS] Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Access your platform:" -ForegroundColor Cyan
Write-Host "  - Web App:     http://localhost:3000"
Write-Host "  - API:         http://localhost:8000"
Write-Host "  - API Docs:    http://localhost:8000/docs"
Write-Host "  - Phoenix:     http://localhost:6006"
Write-Host ""
Write-Host "View logs:" -ForegroundColor Yellow
Write-Host "  docker-compose logs -f"
Write-Host ""
Write-Host "Stop services:" -ForegroundColor Yellow
Write-Host "  docker-compose down"
Write-Host ""
Write-Host "Happy coding!" -ForegroundColor Magenta
