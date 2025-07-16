#!/usr/bin/env python3
"""Development script for running the Data Anonymizer application."""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def run_backend():
    """Run the FastAPI backend."""
    print("Starting FastAPI backend...")
    print("  Backend will be available at: http://localhost:8000")
    print("  API documentation at: http://localhost:8000/docs")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")

    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "src.data_anonymizer.api.main:app",
        "--host",
        "0.0.0.0",
        "--port",
        "8000",
        "--reload",
    ]

    return subprocess.Popen(cmd, env=env)


def run_frontend():
    """Run the Streamlit frontend."""
    print("Starting Streamlit frontend...")
    print("  Frontend will be available at: http://localhost:8501")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.parent / "src")

    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "frontend/streamlit_app.py",
        "--server.port",
        "8501",
        "--server.address",
        "localhost",
    ]

    return subprocess.Popen(cmd, env=env)


def generate_samples():
    """Generate sample data."""
    print("Generating sample data...")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent / "src")

    cmd = [
        sys.executable,
        "-c",
        "import sys; sys.path.insert(0, 'src'); from data_anonymizer.utils.data_generator import generate_sample_data; generate_sample_data('samples')",
    ]

    subprocess.run(cmd, env=env)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Data Anonymizer development script")
    parser.add_argument(
        "action",
        choices=["dev", "backend", "frontend", "samples"],
        help="Action to perform",
    )

    args = parser.parse_args()

    if args.action == "samples":
        generate_samples()
    elif args.action == "backend":
        backend_process = run_backend()
        try:
            backend_process.wait()
        except KeyboardInterrupt:
            print("\nShutting down backend...")
            backend_process.terminate()
    elif args.action == "frontend":
        frontend_process = run_frontend()
        try:
            frontend_process.wait()
        except KeyboardInterrupt:
            print("\nShutting down frontend...")
            frontend_process.terminate()
    elif args.action == "dev":
        # Run both backend and frontend
        print("🚀 Starting Data Anonymizer Development Environment")
        print("=" * 50)

        backend_process = run_backend()
        time.sleep(3)  # Give backend time to start
        frontend_process = run_frontend()

        print("\n" + "=" * 50)
        print("✅ Development environment is ready!")
        print("   Backend API: http://localhost:8000")
        print("   API Docs:    http://localhost:8000/docs")
        print("   Frontend:    http://localhost:8501")
        print("   Press Ctrl+C to stop both services")
        print("=" * 50)

        def signal_handler(signum, frame):
            print("\n🛑 Shutting down services...")
            backend_process.terminate()
            frontend_process.terminate()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        try:
            while True:
                time.sleep(1)
                if backend_process.poll() is not None:
                    print("Backend process died, restarting...")
                    backend_process = run_backend()
                if frontend_process.poll() is not None:
                    print("Frontend process died, restarting...")
                    frontend_process = run_frontend()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
