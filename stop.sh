#!/bin/bash

# Data Anonymizer Stop Script
# This script stops all Data Anonymizer services

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo "🛑 Stopping Data Anonymizer Application..."
echo "=========================================="

# Stop FastAPI (uvicorn)
print_status "Stopping FastAPI backend..."
if pkill -f "uvicorn.*8000"; then
    print_success "FastAPI backend stopped"
else
    print_warning "FastAPI backend was not running"
fi

# Stop Streamlit
print_status "Stopping Streamlit frontend..."
if pkill -f "streamlit.*8501"; then
    print_success "Streamlit frontend stopped"
else
    print_warning "Streamlit frontend was not running"
fi

# Clean up any remaining Python processes (be careful with this)
print_status "Cleaning up remaining processes..."
sleep 2

print_success "All services stopped!"
echo ""
echo "To restart the application, run: ./launch.sh"
