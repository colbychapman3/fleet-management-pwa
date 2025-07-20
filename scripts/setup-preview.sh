#!/bin/bash
# Setup Preview Environment Script

set -e

echo "🚀 Setting up Fleet Management Preview Environment"
echo "=================================================="

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ docker-compose not found. Please install Docker Compose first."
    exit 1
fi

# Create preview branch if it doesn't exist
echo "📋 Setting up preview branch..."
git checkout -b preview 2>/dev/null || git checkout preview

# Build and start preview environment
echo "🔧 Building preview environment..."
docker-compose -f docker-compose.preview.yml build

echo "🚀 Starting preview services..."
docker-compose -f docker-compose.preview.yml up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check if services are running
echo "🔍 Checking service health..."
if docker-compose -f docker-compose.preview.yml ps | grep -q "Up"; then
    echo "✅ Preview services are running!"
    echo ""
    echo "🌐 Preview Environment URLs:"
    echo "   Web Application: http://localhost:5001"
    echo "   Database: postgresql://preview:preview123@localhost:5433/fleet_preview"
    echo "   Redis: redis://localhost:6380/0"
    echo ""
    echo "📋 Useful Commands:"
    echo "   View logs: docker-compose -f docker-compose.preview.yml logs -f"
    echo "   Stop services: docker-compose -f docker-compose.preview.yml down"
    echo "   Restart: docker-compose -f docker-compose.preview.yml restart"
    echo "   Shell access: docker-compose -f docker-compose.preview.yml exec web-preview bash"
    echo ""
    echo "🧪 Run tests against preview:"
    echo "   python test_deployment.py http://localhost:5001"
else
    echo "❌ Some services failed to start. Check logs:"
    docker-compose -f docker-compose.preview.yml logs
    exit 1
fi