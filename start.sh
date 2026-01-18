#!/bin/bash

# Doc2MCP Platform - Quick Start Script
# This script sets up the entire platform with one command

set -e

echo "🚀 Doc2MCP Platform Setup"
echo "=========================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Check for .env file
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys:"
    echo "   - GOOGLE_API_KEY (get from https://aistudio.google.com/app/apikey)"
    echo "   - CLERK_SECRET_KEY (get from https://dashboard.clerk.com)"
    echo "   - NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY"
    echo ""
    read -p "Press Enter once you've added your keys..."
fi

# Check for web/.env file
if [ ! -f web/.env ]; then
    echo "📝 Creating web/.env file from template..."
    cp web/.env.example web/.env
    echo "⚠️  Please edit web/.env and add your Clerk keys"
    echo ""
    read -p "Press Enter once you've added your keys..."
fi

echo "🐳 Building Docker containers..."
docker-compose build

echo ""
echo "🚀 Starting all services..."
docker-compose up -d

echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

echo ""
echo "📊 Initializing database..."
docker-compose exec -T web npx prisma generate
docker-compose exec -T web npx prisma db push

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Access your platform:"
echo "   - Web App:     http://localhost:3000"
echo "   - API:         http://localhost:8000"
echo "   - API Docs:    http://localhost:8000/docs"
echo "   - Phoenix:     http://localhost:6006"
echo ""
echo "📝 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 Stop services:"
echo "   docker-compose down"
echo ""
echo "🎉 Happy coding!"
