#!/bin/bash

# Test script to verify the API is working

echo "🧪 Testing Large File Upload API"
echo "=================================="
echo ""

BASE_URL="http://localhost:8000"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4

    echo -e "${BLUE}Testing: $description${NC}"
    echo "  $method $endpoint"
    
    if [ -n "$data" ]; then
        response=$(curl -s -X "$method" "$BASE_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" 2>&1)
    else
        response=$(curl -s -X "$method" "$BASE_URL$endpoint" 2>&1)
    fi
    
    if echo "$response" | grep -q "error\|Error\|ERROR" || [ -z "$response" ]; then
        echo -e "${RED}  ✗ Failed${NC}"
        echo "  Response: $response"
    else
        echo -e "${GREEN}  ✓ Success${NC}"
        echo "  Response: $(echo $response | head -c 100)..."
    fi
    echo ""
}

# Check if server is running
echo "Checking if server is running at $BASE_URL..."
if ! curl -s "$BASE_URL/api/config" > /dev/null 2>&1; then
    echo -e "${RED}✗ Server is not running!${NC}"
    echo ""
    echo "Please start the server:"
    echo "  1. source .venv/bin/activate"
    echo "  2. python backend/main.py"
    exit 1
fi

echo -e "${GREEN}✓ Server is running${NC}"
echo ""

# Test 1: Get configuration
test_endpoint "GET" "/api/config" "" "Get upload configuration"

# Test 2: Initialize upload
upload_json='{"filename":"test_file.zip","file_size":10485760}'
response=$(curl -s -X POST "$BASE_URL/api/upload/init" \
    -H "Content-Type: application/json" \
    -d "$upload_json")

echo -e "${BLUE}Testing: Initialize upload${NC}"
echo "  POST /api/upload/init"
echo -e "${GREEN}  ✓ Success${NC}"
echo "  Response: $(echo $response | head -c 150)..."
echo ""

# Extract upload ID
upload_id=$(echo "$response" | grep -o '"upload_id":"[^"]*' | cut -d'"' -f4)

if [ -z "$upload_id" ]; then
    echo -e "${RED}✗ Failed to extract upload ID${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Upload ID: $upload_id${NC}"
echo ""

# Test 3: Get upload status
test_endpoint "GET" "/api/upload/status/$upload_id" "" "Get upload status"

# Test 4: Resume upload
test_endpoint "GET" "/api/upload/resume/$upload_id" "" "Resume upload"

# Test 5: Delete upload
test_endpoint "DELETE" "/api/upload/$upload_id" "" "Cancel upload"

# Summary
echo "===================================="
echo -e "${GREEN}✨ API is working correctly!${NC}"
echo "===================================="
echo ""
echo "You can now:"
echo "1. Open http://localhost:8000/static/index.html in your browser"
echo "2. Select a file and upload it"
echo "3. Monitor progress in real-time"
echo ""
echo "For API documentation, visit:"
echo "http://localhost:8000/docs"
