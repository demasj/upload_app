#!/bin/bash

# Large File Upload App - Development Setup Script
# This script sets up the application for development

set -e

echo "🚀 Setting up Large File Upload Application"
echo "==========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python version...${NC}"
python3 --version

# Create virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3.11 -m venv .venv
else
    echo -e "${GREEN}Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source .venv/bin/activate

# Upgrade pip
echo -e "${BLUE}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -r requirements.txt

# Copy .env file if not exists
if [ ! -f "config/.env" ]; then
    echo -e "${BLUE}Creating .env file from template...${NC}"
    cp config/.env.example config/.env
    echo -e "${YELLOW}⚠️  Please edit config/.env with your Azure credentials${NC}"
else
    echo -e "${GREEN}.env file already exists${NC}"
fi

# Create uploads state directory
mkdir -p .uploads_state

echo ""
echo -e "${GREEN}✅ Setup complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Edit config/.env with your Azure Storage credentials"
echo "2. Run: source .venv/bin/activate"
echo "3. Run: python backend/main.py"
echo "4. Open: http://localhost:8000/static/index.html"
echo ""
