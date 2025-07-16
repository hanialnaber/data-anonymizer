# Data Anonymizer Launch Script for PowerShell
# This script sets up and launches the complete data anonymization application

param(
    [switch]$SetupOnly,
    [switch]$NoDeps,
    [switch]$NoSamples,
    [switch]$Help
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

function Write-Status {
    param($Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Blue
}

function Write-Success {
    param($Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param($Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param($Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

function Show-Help {
    Write-Host "Data Anonymizer Launch Script (PowerShell)"
    Write-Host ""
    Write-Host "Usage: .\launch.ps1 [OPTIONS]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -SetupOnly    Only setup environment, don't start application"
    Write-Host "  -NoDeps       Skip dependency installation"
    Write-Host "  -NoSamples    Skip sample data generation"
    Write-Host "  -Help         Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\launch.ps1                  # Full setup and launch"
    Write-Host "  .\launch.ps1 -SetupOnly       # Only setup environment"
    Write-Host "  .\launch.ps1 -NoDeps          # Skip dependency installation"
}

function Test-PythonVersion {
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Python is not installed. Please install Python 3.8 or higher."
            exit 1
        }
        
        $version = $pythonVersion -replace "Python ", ""
        $versionParts = $version.Split(".")
        $major = [int]$versionParts[0]
        $minor = [int]$versionParts[1]
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
            Write-Error "Python 3.8 or higher is required. Current version: $version"
            exit 1
        }
        
        Write-Success "Python version $version detected"
        return $true
    }
    catch {
        Write-Error "Error checking Python version: $_"
        exit 1
    }
}

function Setup-VirtualEnvironment {
    Write-Status "Setting up virtual environment..."
    
    if (-not (Test-Path "venv")) {
        Write-Status "Creating virtual environment..."
        python -m venv venv
        Write-Success "Virtual environment created"
    }
    else {
        Write-Status "Virtual environment already exists"
    }
    
    # Activate virtual environment
    & "venv\Scripts\Activate.ps1"
    Write-Success "Virtual environment activated"
}

function Install-Dependencies {
    Write-Status "Installing dependencies..."
    
    # Upgrade pip
    python -m pip install --upgrade pip
    
    # Install requirements
    if (Test-Path "requirements.txt") {
        pip install -r requirements.txt
        Write-Success "Dependencies installed"
    }
    else {
        Write-Error "requirements.txt not found"
        exit 1
    }
    
    # Install package in development mode
    pip install -e .
    Write-Success "Package installed in development mode"
}

function Generate-SampleData {
    Write-Status "Generating sample data..."
    
    if (-not (Test-Path "samples")) {
        New-Item -ItemType Directory -Path "samples" | Out-Null
    }
    
    # Generate sample data using the data generator
    python -m data_anonymizer.utils.data_generator
    Write-Success "Sample data generated"
}

function Start-Application {
    Write-Status "Starting Data Anonymizer Application..."
    
    # Create directories
    if (-not (Test-Path "uploads")) {
        New-Item -ItemType Directory -Path "uploads" | Out-Null
    }
    
    if (-not (Test-Path "logs")) {
        New-Item -ItemType Directory -Path "logs" | Out-Null
    }
    
    # Kill any existing processes
    Get-Process | Where-Object { $_.ProcessName -like "*uvicorn*" -or $_.ProcessName -like "*streamlit*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    # Start FastAPI backend
    Write-Status "Starting FastAPI backend on http://localhost:8000..."
    $fastApiJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        & "venv\Scripts\Activate.ps1"
        uvicorn data_anonymizer.api.main:app --host localhost --port 8000 --reload
    }
    
    # Wait for FastAPI to start
    Start-Sleep -Seconds 3
    
    # Start Streamlit frontend
    Write-Status "Starting Streamlit frontend on http://localhost:8501..."
    $streamlitJob = Start-Job -ScriptBlock {
        Set-Location $using:PWD
        & "venv\Scripts\Activate.ps1"
        streamlit run frontend/streamlit_app.py --server.port 8501 --server.address localhost
    }
    
    # Wait for services to start
    Start-Sleep -Seconds 5
    
    # Display status
    Write-Success "🚀 Data Anonymizer Application is now running!"
    Write-Host ""
    Write-Host "📍 Access Points:"
    Write-Host "  • Web Interface: http://localhost:8501"
    Write-Host "  • API Documentation: http://localhost:8000/docs"
    Write-Host "  • API Endpoint: http://localhost:8000"
    Write-Host ""
    Write-Host "📊 Job IDs:"
    Write-Host "  • FastAPI Backend: $($fastApiJob.Id)"
    Write-Host "  • Streamlit Frontend: $($streamlitJob.Id)"
    Write-Host ""
    Write-Host "🛑 To stop the application, run: .\stop.ps1"
    Write-Host "   Or press Ctrl+C to stop this script"
    
    # Create stop script
    @"
# Data Anonymizer Stop Script for PowerShell
Write-Host "Stopping Data Anonymizer Application..." -ForegroundColor Yellow
Get-Process | Where-Object { `$_.ProcessName -like "*uvicorn*" -or `$_.ProcessName -like "*streamlit*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Get-Job | Stop-Job -PassThru | Remove-Job
Write-Host "Application stopped." -ForegroundColor Green
"@ | Out-File -FilePath "stop.ps1" -Encoding UTF8
    
    # Open web browser
    Write-Host ""
    Write-Host "Opening web interface..."
    Start-Process "http://localhost:8501"
    
    Write-Host ""
    Write-Host "Press Ctrl+C to stop all services..."
    
    # Wait for user input
    try {
        while ($true) {
            if ($fastApiJob.State -eq "Failed" -or $streamlitJob.State -eq "Failed") {
                Write-Error "One of the services failed"
                break
            }
            Start-Sleep -Seconds 2
        }
    }
    finally {
        Write-Host "Stopping services..."
        Get-Job | Stop-Job -PassThru | Remove-Job
        Get-Process | Where-Object { $_.ProcessName -like "*uvicorn*" -or $_.ProcessName -like "*streamlit*" } | Stop-Process -Force -ErrorAction SilentlyContinue
    }
}

# Main execution
function Main {
    Write-Host ""
    Write-Host "🛡️  Data Anonymizer Launch Script (PowerShell)" -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Cyan
    Write-Host ""
    
    if ($Help) {
        Show-Help
        exit 0
    }
    
    # Check prerequisites
    Write-Status "Checking prerequisites..."
    Test-PythonVersion
    
    # Setup virtual environment
    Setup-VirtualEnvironment
    
    # Install dependencies
    if (-not $NoDeps) {
        Install-Dependencies
    }
    else {
        Write-Warning "Skipping dependency installation"
    }
    
    # Generate sample data
    if (-not $NoSamples) {
        Generate-SampleData
    }
    else {
        Write-Warning "Skipping sample data generation"
    }
    
    # Start application or exit if setup-only
    if ($SetupOnly) {
        Write-Success "Environment setup complete!"
        Write-Host ""
        Write-Host "To start the application, run: .\launch.ps1"
        exit 0
    }
    
    # Start the application
    Start-Application
}

# Run main function
Main
