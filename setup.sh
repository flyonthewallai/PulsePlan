#!/bin/bash

# PulsePlan Setup Script
# This script sets up the development environment for PulsePlan

set -e

echo "Setting up PulsePlan development environment..."

# Check if Python 3.12+ is available
if ! command -v python3.12 &> /dev/null; then
    echo "❌ Python 3.12+ is required but not found."
    echo "Please install Python 3.12+ using Homebrew: brew install python@3.12"
    exit 1
fi

echo "✅ Python 3.12+ found"

# Backend setup
echo "Setting up backend dependencies..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3.12 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Backend dependencies installed"

# Frontend setup
echo "Setting up frontend dependencies..."
cd ../web

# Install Node.js dependencies
echo "Installing Node.js dependencies..."
npm install

echo "✅ Frontend dependencies installed"

# Create .env file if it doesn't exist
cd ../backend
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
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

MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
MICROSOFT_REDIRECT_URL=http://localhost:8000/auth/microsoft/callback
MICROSOFT_TENANT_ID=common

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
CLIENT_URL=http://localhost:8081

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
    echo "✅ .env file created"
else
    echo "✅ .env file already exists"
fi

cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start the applications:"
echo "  Backend:  cd backend && source venv/bin/activate && python3 main.py"
echo "  Frontend: cd web && npm run dev"
echo ""
echo "⚠️  Remember to update the .env file with your actual API keys and configuration!"
echo ""
