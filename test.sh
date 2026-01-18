#!/bin/bash

# Doc2MCP Platform - Integration Test Script
# Tests all components to verify they're working

set -e

echo "🧪 Doc2MCP Platform Integration Tests"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Helper functions
pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((TESTS_FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if services are running
echo "1. Checking Docker Services..."
if docker-compose ps | grep -q "Up"; then
    pass "Docker Compose services are running"
else
    fail "Docker Compose services are not running"
    echo "   Run: docker-compose up -d"
    exit 1
fi
echo ""

# Test Web Frontend
echo "2. Testing Web Frontend (Next.js)..."
if curl -sf http://localhost:3000 > /dev/null; then
    pass "Web frontend is accessible"
else
    fail "Web frontend is not accessible"
fi
echo ""

# Test API Backend
echo "3. Testing API Backend (FastAPI)..."
if curl -sf http://localhost:8000/health > /dev/null; then
    HEALTH=$(curl -s http://localhost:8000/health)
    pass "API backend is healthy"
    echo "   Response: $HEALTH"
else
    fail "API backend is not accessible"
fi
echo ""

# Test Phoenix
echo "4. Testing Phoenix Dashboard..."
if curl -sf http://localhost:6006 > /dev/null; then
    pass "Phoenix dashboard is accessible"
else
    warn "Phoenix dashboard is not accessible (optional)"
fi
echo ""

# Test Redis
echo "5. Testing Redis..."
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    pass "Redis is responding"
else
    fail "Redis is not responding"
fi
echo ""

# Test Database
echo "6. Testing Database..."
if docker-compose exec -T web npx prisma db push --skip-generate > /dev/null 2>&1; then
    pass "Database schema is up to date"
else
    warn "Database might need migration"
fi
echo ""

# Test API Endpoints
echo "7. Testing API Endpoints..."

# Health endpoint
if curl -sf http://localhost:8000/health | grep -q "healthy"; then
    pass "Health endpoint works"
else
    fail "Health endpoint failed"
fi

# Root endpoint
if curl -sf http://localhost:8000 | grep -q "Doc2MCP API"; then
    pass "Root endpoint works"
else
    fail "Root endpoint failed"
fi

# Docs endpoint
if curl -sf http://localhost:8000/docs > /dev/null; then
    pass "API documentation is accessible"
else
    fail "API documentation failed"
fi
echo ""

# Test Environment Variables
echo "8. Checking Environment Variables..."

if docker-compose exec -T api env | grep -q "GOOGLE_API_KEY"; then
    pass "GOOGLE_API_KEY is set in API"
else
    fail "GOOGLE_API_KEY is not set in API"
fi

if docker-compose exec -T web env | grep -q "CLERK_SECRET_KEY"; then
    pass "CLERK_SECRET_KEY is set in Web"
else
    fail "CLERK_SECRET_KEY is not set in Web"
fi
echo ""

# Test doc2mcp Agent
echo "9. Testing doc2mcp Agent..."
if docker-compose exec -T api python -c "from doc2mcp.agents.doc_search import DocSearchAgent; print('OK')" 2>/dev/null | grep -q "OK"; then
    pass "doc2mcp agent can be imported"
else
    fail "doc2mcp agent import failed"
fi
echo ""

# Test Prisma
echo "10. Testing Prisma ORM..."
if docker-compose exec -T web npx prisma version > /dev/null 2>&1; then
    pass "Prisma is installed and working"
else
    fail "Prisma is not working"
fi
echo ""

# Summary
echo ""
echo "======================================"
echo "Test Summary:"
echo "======================================"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
else
    echo -e "Failed: $TESTS_FAILED"
fi
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}🎉 All tests passed! Platform is working correctly.${NC}"
    echo ""
    echo "Access your platform:"
    echo "  • Web:     http://localhost:3000"
    echo "  • API:     http://localhost:8000"
    echo "  • Docs:    http://localhost:8000/docs"
    echo "  • Phoenix: http://localhost:6006"
    exit 0
else
    echo -e "${RED}❌ Some tests failed. Please check the output above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  • Restart services: docker-compose restart"
    echo "  • Check logs: docker-compose logs -f"
    echo "  • Rebuild: docker-compose up -d --build"
    exit 1
fi
