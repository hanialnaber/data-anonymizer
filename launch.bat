@echo off
REM Data Anonymizer Launch Script for Windows
REM This script sets up and launches the complete data anonymization application

setlocal enabledelayedexpansion

echo.
echo 🛡️  Data Anonymizer Launch Script (Windows)
echo ==========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

echo [INFO] Python detected
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo [SUCCESS] Python version !PYTHON_VERSION! detected

REM Setup virtual environment
echo [INFO] Setting up virtual environment...
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    echo [SUCCESS] Virtual environment created
) else (
    echo [INFO] Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat
echo [SUCCESS] Virtual environment activated

REM Install dependencies
echo [INFO] Installing dependencies...
python -m pip install --upgrade pip

if exist "requirements.txt" (
    pip install -r requirements.txt
    echo [SUCCESS] Dependencies installed
) else (
    echo [ERROR] requirements.txt not found
    pause
    exit /b 1
)

REM Install package in development mode
pip install -e .
echo [SUCCESS] Package installed in development mode

REM Generate sample data
echo [INFO] Generating sample data...
if not exist "samples" mkdir samples
python -m data_anonymizer.utils.data_generator
echo [SUCCESS] Sample data generated

REM Create uploads directory
if not exist "uploads" mkdir uploads

REM Create logs directory
if not exist "logs" mkdir logs

REM Start the application
echo [INFO] Starting Data Anonymizer Application...

REM Start FastAPI backend
echo [INFO] Starting FastAPI backend on http://localhost:8000...
start "FastAPI Backend" cmd /c "uvicorn data_anonymizer.api.main:app --host localhost --port 8000 --reload > logs\fastapi.log 2>&1"

REM Wait a moment for FastAPI to start
timeout /t 3 /nobreak >nul

REM Start Streamlit frontend
echo [INFO] Starting Streamlit frontend on http://localhost:8501...
start "Streamlit Frontend" cmd /c "streamlit run frontend\streamlit_app.py --server.port 8501 --server.address localhost > logs\streamlit.log 2>&1"

REM Wait a moment for services to start
timeout /t 5 /nobreak >nul

REM Display status
echo.
echo [SUCCESS] 🚀 Data Anonymizer Application is now running!
echo.
echo 📍 Access Points:
echo   • Web Interface: http://localhost:8501
echo   • API Documentation: http://localhost:8000/docs
echo   • API Endpoint: http://localhost:8000
echo.
echo 📝 Logs:
echo   • FastAPI: logs\fastapi.log
echo   • Streamlit: logs\streamlit.log
echo.
echo 🛑 To stop the application, run: stop.bat
echo    Or close this window and manually stop the services

REM Create stop script
echo @echo off > stop.bat
echo echo Stopping Data Anonymizer Application... >> stop.bat
echo taskkill /f /im python.exe 2^>nul ^|^| echo No Python processes found >> stop.bat
echo taskkill /f /im uvicorn.exe 2^>nul ^|^| echo FastAPI not running >> stop.bat
echo taskkill /f /im streamlit.exe 2^>nul ^|^| echo Streamlit not running >> stop.bat
echo echo Application stopped. >> stop.bat
echo pause >> stop.bat

echo.
echo Press any key to open the web interface...
pause >nul

REM Open web browser
start http://localhost:8501

echo.
echo Application is running. Press any key to stop all services...
pause >nul

REM Stop services
echo Stopping services...
taskkill /f /im python.exe 2>nul || echo No Python processes found
taskkill /f /im uvicorn.exe 2>nul || echo FastAPI not running
taskkill /f /im streamlit.exe 2>nul || echo Streamlit not running

echo Application stopped.
pause
