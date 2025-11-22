#!/bin/bash

# Large File Upload System - Startup Script
# This script handles all setup and startup tasks

set -e

echo "🚀 Large File Upload System - Startup"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source "$SCRIPT_DIR/.venv/bin/activate"

# Check for .env configuration
echo -e "${BLUE}Checking configuration...${NC}"
if grep -q "your_account_name" "$SCRIPT_DIR/config/.env" || grep -q "your_account_key" "$SCRIPT_DIR/config/.env"; then
    echo -e "${YELLOW}⚠️  Azure credentials not configured!${NC}"
    echo ""
    echo "Please edit config/.env with your Azure credentials:"
    echo "  AZURE_STORAGE_ACCOUNT_NAME=your_actual_account_name"
    echo "  AZURE_STORAGE_ACCOUNT_KEY=your_actual_account_key"
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo -e "${GREEN}✓ Configuration found${NC}"

# Create uploads state directory
mkdir -p "$SCRIPT_DIR/.uploads_state"

# Start the application
echo ""
echo -e "${BLUE}Starting FastAPI server...${NC}"
echo "===================================="
echo ""
echo "📍 API Endpoint: http://localhost:8000"
echo "📖 API Docs: http://localhost:8000/docs"
echo "🌐 Frontend: http://localhost:8000/static/index.html"
echo ""
echo "Press Ctrl+C to stop the server"
echo "===================================="
echo ""

# Run the application
python "$SCRIPT_DIR/backend/main.py"
