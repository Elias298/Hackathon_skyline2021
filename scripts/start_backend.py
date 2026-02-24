#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

def start_backend():

    # Load environment variables from .env file in project root
    load_dotenv()

    # Extract host and port configuration from environment variables
    backend_host = os.getenv("BACKEND_HOST", "localhost")
    backend_port = os.getenv("BACKEND_PORT", "8000")

    print(f"Starting FastAPI backend on {backend_host}:{backend_port}...")

    # Get the backend root directory
    # Resolve backend directory relative to this script's location
    backend_dir = (Path(__file__).parent.parent / "backend").resolve()
    subprocess.run(
        [
            "uvicorn",
            "app:app",
            "--reload",
            "--host",
            backend_host,
            "--port",
            backend_port,
        ],
        cwd=backend_dir,  # Run from the backend directory
    )

if __name__ == "__main__":
    start_backend()
