#!/bin/bash

# Data Anonymizer Launch Script
# This script sets up and launches the complete data anonymization application

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.8 or higher."
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        print_error "Python 3.8 or higher is required. Current version: $PYTHON_VERSION"
        exit 1
    fi

    print_success "Python version $PYTHON_VERSION detected"
}

# Function to setup virtual environment
setup_venv() {
    print_status "Setting up virtual environment..."
    
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi

    # Activate virtual environment
    if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows (Git Bash)
        source venv/Scripts/activate
    else
        # Unix/Linux/macOS
        source venv/bin/activate
    fi
    
    print_success "Virtual environment activated"
}

# Function to install dependencies
install_dependencies() {
    print_status "Installing dependencies..."
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
    
    # Install package in development mode
    pip install -e .
    print_success "Package installed in development mode"
}

# Function to generate sample data
generate_sample_data() {
    print_status "Generating sample data..."
    
    if [ ! -d "samples" ]; then
        mkdir -p samples
    fi
    
    # Generate sample data using the data generator
    $PYTHON_CMD -m data_anonymizer.utils.data_generator
    print_success "Sample data generated"
}

# Function to start the application
start_application() {
    print_status "Starting Data Anonymizer Application..."
    
    # Check if ports are available
    if command_exists lsof; then
        if lsof -i :8000 >/dev/null 2>&1; then
            print_warning "Port 8000 is already in use. Stopping existing process..."
            pkill -f "uvicorn.*8000" || true
        fi
        
        if lsof -i :8501 >/dev/null 2>&1; then
            print_warning "Port 8501 is already in use. Stopping existing process..."
            pkill -f "streamlit.*8501" || true
        fi
    fi
    
    # Create uploads directory if it doesn't exist
    mkdir -p uploads
    
    # Start FastAPI backend in background
    print_status "Starting FastAPI backend on http://localhost:8000..."
    nohup uvicorn data_anonymizer.api.main:app --host localhost --port 8000 --reload > logs/fastapi.log 2>&1 &
    FASTAPI_PID=$!
    
    # Wait a moment for FastAPI to start
    sleep 3
    
    # Start Streamlit frontend in background
    print_status "Starting Streamlit frontend on http://localhost:8501..."
    nohup streamlit run frontend/streamlit_app.py --server.port 8501 --server.address localhost > logs/streamlit.log 2>&1 &
    STREAMLIT_PID=$!
    
    # Wait a moment for services to start
    sleep 5
    
    # Display status
    print_success "🚀 Data Anonymizer Application is now running!"
    echo ""
    echo "📍 Access Points:"
    echo "  • Web Interface: http://localhost:8501"
    echo "  • API Documentation: http://localhost:8000/docs"
    echo "  • API Endpoint: http://localhost:8000"
    echo ""
    echo "📊 Process IDs:"
    echo "  • FastAPI Backend: $FASTAPI_PID"
    echo "  • Streamlit Frontend: $STREAMLIT_PID"
    echo ""
    echo "📝 Logs:"
    echo "  • FastAPI: logs/fastapi.log"
    echo "  • Streamlit: logs/streamlit.log"
    echo ""
    echo "🛑 To stop the application, run: ./stop.sh"
    echo "   Or press Ctrl+C to stop this script and kill processes"
    
    # Create stop script
    cat > stop.sh << 'EOF'
#!/bin/bash
echo "Stopping Data Anonymizer Application..."
pkill -f "uvicorn.*8000" || echo "FastAPI not running"
pkill -f "streamlit.*8501" || echo "Streamlit not running"
echo "Application stopped."
EOF
    chmod +x stop.sh
    
    # Wait for user input or process termination
    echo ""
    echo "Press Ctrl+C to stop all services..."
    trap 'echo ""; echo "Stopping services..."; kill $FASTAPI_PID $STREAMLIT_PID 2>/dev/null || true; exit 0' INT
    
    # Keep script running and monitor processes
    while true; do
        if ! kill -0 $FASTAPI_PID 2>/dev/null; then
            print_error "FastAPI process died unexpectedly"
            exit 1
        fi
        if ! kill -0 $STREAMLIT_PID 2>/dev/null; then
            print_error "Streamlit process died unexpectedly"
            exit 1
        fi
        sleep 5
    done
}

# Function to display help
show_help() {
    echo "Data Anonymizer Launch Script"
    echo ""
    echo "Usage: ./launch.sh [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --setup-only    Only setup environment, don't start application"
    echo "  --no-deps       Skip dependency installation"
    echo "  --no-samples    Skip sample data generation"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./launch.sh                  # Full setup and launch"
    echo "  ./launch.sh --setup-only     # Only setup environment"
    echo "  ./launch.sh --no-deps        # Skip dependency installation"
}

# Main execution
main() {
    echo "🛡️  Data Anonymizer Launch Script"
    echo "=================================="
    echo ""
    
    # Parse command line arguments
    SETUP_ONLY=false
    NO_DEPS=false
    NO_SAMPLES=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --setup-only)
                SETUP_ONLY=true
                shift
                ;;
            --no-deps)
                NO_DEPS=true
                shift
                ;;
            --no-samples)
                NO_SAMPLES=true
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # Create logs directory
    mkdir -p logs
    
    # Check prerequisites
    print_status "Checking prerequisites..."
    check_python_version
    
    # Setup virtual environment
    setup_venv
    
    # Install dependencies
    if [ "$NO_DEPS" = false ]; then
        install_dependencies
    else
        print_warning "Skipping dependency installation"
    fi
    
    # Generate sample data
    if [ "$NO_SAMPLES" = false ]; then
        generate_sample_data
    else
        print_warning "Skipping sample data generation"
    fi
    
    # Start application or exit if setup-only
    if [ "$SETUP_ONLY" = true ]; then
        print_success "Environment setup complete!"
        echo ""
        echo "To start the application, run: ./launch.sh"
        exit 0
    fi
    
    # Start the application
    start_application
}

# Run main function
main "$@"
