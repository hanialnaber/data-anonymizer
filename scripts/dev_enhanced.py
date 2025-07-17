"""Enhanced development script with better functionality."""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


def run_command(command: List[str], cwd: Optional[str] = None) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(command)}")
    result = subprocess.run(command, cwd=cwd)
    return result.returncode


def check_python_version():
    """Check if Python version is compatible."""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)


def install_dependencies():
    """Install project dependencies."""
    print("Installing dependencies...")
    return run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])


def install_dev_dependencies():
    """Install development dependencies."""
    print("Installing development dependencies...")
    return run_command([sys.executable, "-m", "pip", "install", "-e", "."])


def generate_samples():
    """Generate sample data files."""
    print("Generating sample data...")
    try:
        from src.data_anonymizer.utils.data_generator import generate_sample_data
        results = generate_sample_data()
        print(f"Generated sample files: {list(results.keys())}")
        return 0
    except Exception as e:
        print(f"Error generating samples: {e}")
        return 1


def run_tests(test_path: str = "tests/", verbose: bool = True):
    """Run tests."""
    print(f"Running tests from {test_path}...")
    cmd = [sys.executable, "-m", "pytest", test_path]
    if verbose:
        cmd.append("-v")
    return run_command(cmd)


def run_specific_tests(test_type: str):
    """Run specific test categories."""
    test_files = {
        "core": "tests/test_anonymizer.py",
        "api": "tests/test_api.py",
        "security": "tests/test_security.py",
        "performance": "tests/test_performance.py",
        "integration": "tests/test_integration.py"
    }
    
    if test_type not in test_files:
        print(f"Unknown test type: {test_type}")
        print(f"Available types: {list(test_files.keys())}")
        return 1
    
    return run_tests(test_files[test_type])


def start_backend():
    """Start the FastAPI backend."""
    print("Starting FastAPI backend...")
    return run_command([
        sys.executable, "-m", "uvicorn",
        "src.data_anonymizer.api.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
    ])


def start_frontend():
    """Start the Streamlit frontend."""
    print("Starting Streamlit frontend...")
    return run_command([
        sys.executable, "-m", "streamlit", "run",
        "frontend/streamlit_app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0"
    ])


def start_both():
    """Start both backend and frontend."""
    import threading
    import time
    
    print("Starting both services...")
    
    # Start backend in a thread
    backend_thread = threading.Thread(target=start_backend)
    backend_thread.daemon = True
    backend_thread.start()
    
    # Wait a bit for backend to start
    time.sleep(3)
    
    # Start frontend in main thread
    start_frontend()


def format_code():
    """Format code with black and isort."""
    print("Formatting code...")
    
    # Format with black
    result1 = run_command([sys.executable, "-m", "black", "src/", "tests/", "scripts/"])
    
    # Sort imports with isort
    result2 = run_command([sys.executable, "-m", "isort", "src/", "tests/", "scripts/"])
    
    return max(result1, result2)


def lint_code():
    """Run linting with flake8."""
    print("Running linting...")
    return run_command([sys.executable, "-m", "flake8", "src/", "tests/", "scripts/"])


def type_check():
    """Run type checking with mypy."""
    print("Running type checking...")
    return run_command([sys.executable, "-m", "mypy", "src/"])


def clean_cache():
    """Clean Python cache files."""
    print("Cleaning cache files...")
    cache_patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        "**/.pytest_cache",
        "**/.mypy_cache",
        ".coverage",
        "htmlcov/"
    ]
    
    import shutil
    import glob
    
    for pattern in cache_patterns:
        for path in glob.glob(pattern, recursive=True):
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"Removed directory: {path}")
            elif os.path.isfile(path):
                os.remove(path)
                print(f"Removed file: {path}")


def setup_project():
    """Set up the project for development."""
    print("Setting up project for development...")
    
    check_python_version()
    
    # Install dependencies
    if install_dependencies() != 0:
        print("Failed to install dependencies")
        return 1
    
    # Install in development mode
    if install_dev_dependencies() != 0:
        print("Failed to install in development mode")
        return 1
    
    # Generate samples
    if generate_samples() != 0:
        print("Failed to generate samples")
        return 1
    
    print("Project setup complete!")
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Data Anonymizer Development Tool")
    parser.add_argument("command", choices=[
        "setup", "install", "samples", "test", "test-core", "test-api", 
        "test-security", "test-performance", "test-integration",
        "backend", "frontend", "dev", "format", "lint", "type-check", "clean"
    ], help="Command to run")
    
    args = parser.parse_args()
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    if args.command == "setup":
        sys.exit(setup_project())
    elif args.command == "install":
        sys.exit(install_dependencies())
    elif args.command == "samples":
        sys.exit(generate_samples())
    elif args.command == "test":
        sys.exit(run_tests())
    elif args.command.startswith("test-"):
        test_type = args.command[5:]  # Remove "test-" prefix
        sys.exit(run_specific_tests(test_type))
    elif args.command == "backend":
        sys.exit(start_backend())
    elif args.command == "frontend":
        sys.exit(start_frontend())
    elif args.command == "dev":
        sys.exit(start_both())
    elif args.command == "format":
        sys.exit(format_code())
    elif args.command == "lint":
        sys.exit(lint_code())
    elif args.command == "type-check":
        sys.exit(type_check())
    elif args.command == "clean":
        sys.exit(clean_cache())
    else:
        print(f"Unknown command: {args.command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
