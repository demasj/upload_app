#!/bin/bash

# Verification Checklist for Large File Upload System
# Run this script to verify all components are in place

echo "🔍 Verifying Large File Upload System Installation"
echo "===================================================="
echo ""

ERRORS=0
WARNINGS=0
CHECKS_PASSED=0

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check function
check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} Found: $1"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} Missing: $1"
        ((ERRORS++))
    fi
}

check_dir() {
    if [ -d "$1" ]; then
        echo -e "${GREEN}✓${NC} Found: $1"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} Missing: $1"
        ((ERRORS++))
    fi
}

check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✓${NC} $1 is installed"
        ((CHECKS_PASSED++))
    else
        echo -e "${RED}✗${NC} $1 is NOT installed"
        ((ERRORS++))
    fi
}

# Check Python
echo -e "${BLUE}[1] Python Environment${NC}"
echo "-------------------------"
check_command "python3"
check_dir ".venv"
check_dir ".venv/bin"
echo ""

# Check Backend Files
echo -e "${BLUE}[2] Backend Files${NC}"
echo "-------------------"
check_file "backend/main.py"
check_file "backend/config.py"
check_file "backend/storage.py"
check_file "backend/azure_handler.py"
echo ""

# Check Frontend Files
echo -e "${BLUE}[3] Frontend Files${NC}"
echo "-------------------"
check_file "frontend/app.py"
check_file "frontend/static/styles.css"
check_file "frontend/static/script.js"
check_file "frontend/static/template.html"
check_file "frontend/Dockerfile"
echo ""

# Check Configuration Files
echo -e "${BLUE}[4] Configuration Files${NC}"
echo "------------------------"
check_file "config/.env"
check_file "config/.env.example"
echo ""

# Check Documentation
echo -e "${BLUE}[5] Documentation${NC}"
echo "-------------------"
check_file "README.md"
check_file "DEVELOPMENT.md"
echo ""

# Check Deployment Files
echo -e "${BLUE}[6] Deployment Files${NC}"
echo "---------------------"
check_file "Dockerfile"
check_file "docker-compose.yml"
check_file "setup.sh"
echo ""

# Check Requirements
echo -e "${BLUE}[7] Requirements${NC}"
echo "-----------------"
check_file "requirements.txt"

# Check if packages are installed
if [ -f ".venv/bin/python" ]; then
    echo ""
    echo "Checking installed packages..."
    FASTAPI_CHECK=$(.venv/bin/python -c "import fastapi; print('installed')" 2>/dev/null)
    if [ "$FASTAPI_CHECK" = "installed" ]; then
        echo -e "${GREEN}✓${NC} FastAPI is installed"
        ((CHECKS_PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} FastAPI is NOT installed - run: pip install -r requirements.txt"
        ((WARNINGS++))
    fi

    AZURE_CHECK=$(.venv/bin/python -c "import azure.storage.blob; print('installed')" 2>/dev/null)
    if [ "$AZURE_CHECK" = "installed" ]; then
        echo -e "${GREEN}✓${NC} Azure SDK is installed"
        ((CHECKS_PASSED++))
    else
        echo -e "${YELLOW}⚠${NC} Azure SDK is NOT installed - run: pip install -r requirements.txt"
        ((WARNINGS++))
    fi
fi

echo ""

# Check .env configuration
echo -e "${BLUE}[8] Azure Configuration${NC}"
echo "------------------------"

if [ -f "config/.env" ]; then
    ACCOUNT=$(grep "AZURE_STORAGE_ACCOUNT_NAME" config/.env | grep -v "^#" | cut -d'=' -f2)
    KEY=$(grep "AZURE_STORAGE_ACCOUNT_KEY" config/.env | grep -v "^#" | cut -d'=' -f2)
    
    if [ -z "$ACCOUNT" ] || [ "$ACCOUNT" = "your_account_name" ]; then
        echo -e "${YELLOW}⚠${NC} AZURE_STORAGE_ACCOUNT_NAME not configured"
        ((WARNINGS++))
    else
        echo -e "${GREEN}✓${NC} AZURE_STORAGE_ACCOUNT_NAME is configured"
        ((CHECKS_PASSED++))
    fi
    
    if [ -z "$KEY" ] || [ "$KEY" = "your_account_key" ]; then
        echo -e "${YELLOW}⚠${NC} AZURE_STORAGE_ACCOUNT_KEY not configured"
        ((WARNINGS++))
    else
        echo -e "${GREEN}✓${NC} AZURE_STORAGE_ACCOUNT_KEY is configured"
        ((CHECKS_PASSED++))
    fi
fi

echo ""

# Port availability check
echo -e "${BLUE}[9] Port Availability${NC}"
echo "----------------------"
if ! lsof -Pi :8001 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${GREEN}✓${NC} Port 8001 is available"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} Port 8001 is already in use"
    ((WARNINGS++))
fi

if ! lsof -Pi :8501 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${GREEN}✓${NC} Port 8501 is available"
    ((CHECKS_PASSED++))
else
    echo -e "${YELLOW}⚠${NC} Port 8501 is already in use"
    ((WARNINGS++))
fi

echo ""

# Summary
echo "===================================================="
echo "Verification Summary"
echo "===================================================="
echo -e "${GREEN}Checks Passed: $CHECKS_PASSED${NC}"
if [ $WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}Warnings: $WARNINGS${NC}"
fi
if [ $ERRORS -gt 0 ]; then
    echo -e "${RED}Errors: $ERRORS${NC}"
fi

echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✨ Everything is ready!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Edit config/.env with your Azure credentials"
    echo "2. Run: source .venv/bin/activate"
    echo "3. Run: python backend/main.py"
    echo "4. Run: streamlit run frontend/app.py (in another terminal)"
    echo "5. Visit: http://localhost:8501"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Please address warnings above${NC}"
    exit 1
else
    echo -e "${RED}❌ Please fix errors above${NC}"
    exit 1
fi
