#!/usr/bin/env bash

# PulsePlan Setup Script
# Cross-platform setup for Mac, Linux, and Windows (Git Bash/WSL)

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect OS
OS="unknown"
case "$(uname -s)" in
    Linux*)     OS="linux";;
    Darwin*)    OS="mac";;
    CYGWIN*|MINGW*|MSYS*)    OS="windows";;
esac

echo "🚀 Setting up PulsePlan development environment..."
echo "Detected OS: $OS"
echo ""

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to find Python 3.11+
find_python() {
    for cmd in python3.12 python3.11 python3 python; do
        if command_exists "$cmd"; then
            version=$("$cmd" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
            major=$(echo "$version" | cut -d. -f1)
            minor=$(echo "$version" | cut -d. -f2)

            if [ "$major" -eq 3 ] && [ "$minor" -ge 11 ]; then
                echo "$cmd"
                return 0
            fi
        fi
    done
    return 1
}

# Check Python
echo "Checking for Python 3.11+..."
PYTHON_CMD=$(find_python)

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}❌ Python 3.11+ is required but not found.${NC}"
    echo ""
    echo "Installation instructions:"
    case $OS in
        mac)
            echo "  macOS:   brew install python@3.12"
            ;;
        linux)
            echo "  Ubuntu:  sudo apt-get install python3.12"
            echo "  Fedora:  sudo dnf install python3.12"
            ;;
        windows)
            echo "  Windows: Download from https://www.python.org/downloads/"
            echo "           Or use: winget install Python.Python.3.12"
            ;;
    esac
    exit 1
fi

echo -e "${GREEN}✅ Python found: $PYTHON_CMD${NC}"

# Check Node.js
echo "Checking for Node.js..."
if ! command_exists node; then
    echo -e "${RED}❌ Node.js is required but not found.${NC}"
    echo ""
    echo "Installation instructions:"
    case $OS in
        mac)
            echo "  macOS:   brew install node"
            ;;
        linux)
            echo "  Linux:   curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -"
            echo "           sudo apt-get install -y nodejs"
            ;;
        windows)
            echo "  Windows: Download from https://nodejs.org/"
            echo "           Or use: winget install OpenJS.NodeJS"
            ;;
    esac
    exit 1
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✅ Node.js found: $NODE_VERSION${NC}"

# Check npm
if ! command_exists npm; then
    echo -e "${RED}❌ npm is required but not found.${NC}"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Backend Setup (Python)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    "$PYTHON_CMD" -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate virtual environment (cross-platform)
echo "Activating virtual environment..."
if [ "$OS" = "windows" ]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip --quiet

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt --quiet

echo -e "${GREEN}✅ Backend dependencies installed${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating backend .env file..."
    cat > .env << 'EOF'
# PulsePlan Development Environment Configuration
# This file contains development-only values for testing

# Application Settings
APP_NAME=PulsePlan API
VERSION=2.0.0
ENVIRONMENT=development
DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000

# Security Configuration (Development values - DO NOT USE IN PRODUCTION)
SECRET_KEY=dev-secret-key-change-in-production-12345678901234567890
HMAC_SECRET_KEY=dev-hmac-secret-key-change-in-production-12345678901234567890
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
ALLOWED_HOSTS=["*"]
ALLOWED_ORIGINS=["http://localhost:3000", "http://localhost:8081", "http://localhost:5173", "http://localhost:5174"]

# Database Configuration (Supabase) - Replace with your actual values
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-supabase-service-key-here

# Redis Configuration (Optional for development)
# REDIS_URL=redis://localhost:6379
# UPSTASH_REDIS_REST_URL=
# UPSTASH_REDIS_REST_TOKEN=

# Encryption Configuration (Development values - DO NOT USE IN PRODUCTION)
TOKEN_ENCRYPTION_KEY=dev-encryption-key-32-chars-long-12345678901234567890123456789012

# OAuth Provider Configuration (Replace with your actual values)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URL=http://localhost:8000/auth/google/callback
GOOGLE_WEBHOOK_VERIFICATION_TOKEN=your-webhook-verification-token

MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
MICROSOFT_REDIRECT_URL=http://localhost:8000/auth/microsoft/callback
MICROSOFT_TENANT_ID=common

# Canvas LMS Configuration (Replace with your actual values)
CANVAS_API_KEY=your-canvas-api-key-here
CANVAS_BASE_URL=https://canvas.instructure.com

# Calendar System (Replace with actual values)
API_BASE_URL=http://localhost:8000

# OpenAI/LLM Configuration (Replace with your actual API key)
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.0
OPENAI_MAX_TOKENS=1000
OPENAI_TIMEOUT=30

# Search Integration (Replace with your actual API key)
TAVILY_API_KEY=your-tavily-api-key-here

# Email Configuration (Replace with your actual values)
RESEND_API_KEY=your-resend-api-key-here
RESEND_FROM_EMAIL=noreply@yourdomain.com

# Application URLs
APP_URL=http://localhost:8000
CLIENT_URL=http://localhost:5173

# Logging Configuration
LOG_LEVEL=INFO
ENABLE_STRUCTURED_LOGGING=true
LOG_TO_FILE=false

# Rate Limiting (Development values)
ENABLE_RATE_LIMITING=false
USER_RATE_LIMIT=1000

# Health Check Configuration
HEALTH_CHECK_INTERVAL_SECONDS=60
HEALTH_CHECK_TIMEOUT_SECONDS=5

# Memory Management
MEMORY_WARNING_THRESHOLD=80
MEMORY_CRITICAL_THRESHOLD=90
EOF
    echo -e "${GREEN}✅ Backend .env file created${NC}"
else
    echo -e "${GREEN}✅ Backend .env file already exists${NC}"
fi

cd ..

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Frontend Setup (React Web App)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

cd web

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install --quiet

echo -e "${GREEN}✅ Frontend dependencies installed${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Creating frontend .env file..."
    cat > .env << 'EOF'
# Frontend Environment Configuration

# Backend API URL
VITE_API_URL=http://localhost:8000

# Supabase Configuration (Replace with your actual values)
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key-here

# OAuth Configuration
VITE_GOOGLE_CLIENT_ID=your-google-client-id

# Environment
VITE_ENVIRONMENT=development
EOF
    echo -e "${GREEN}✅ Frontend .env file created${NC}"
else
    echo -e "${GREEN}✅ Frontend .env file already exists${NC}"
fi

cd ..

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎉 Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Update .env files with your actual API keys!${NC}"
echo ""
echo "  Backend:  backend/.env"
echo "  Frontend: web/.env"
echo ""
echo "To start the applications:"
echo ""
echo -e "${GREEN}  Backend:${NC}"
if [ "$OS" = "windows" ]; then
    echo "    cd backend && source venv/Scripts/activate && python main.py"
else
    echo "    cd backend && source venv/bin/activate && python main.py"
fi
echo ""
echo -e "${GREEN}  Frontend:${NC}"
echo "    cd web && npm run dev"
echo ""
echo "Backend will run on:  http://localhost:8000"
echo "Frontend will run on: http://localhost:5173"
echo ""
echo "For more information, see README.md"
echo ""
