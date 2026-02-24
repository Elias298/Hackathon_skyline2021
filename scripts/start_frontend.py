#!/usr/bin/env python3

import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

def start_frontend():
    # Load environment variables from .env file in project root
    load_dotenv()

    frontend_port = os.getenv("VITE_PORT", "3000")
    frontend_host = os.getenv("VITE_HOST","localhost")
    print(f"Starting React frontend on port {frontend_port}...")

    # Resolve the frontend directory path relative to this script
    frontend_dir = (Path(__file__).parent.parent / "frontend/HackathonProject").resolve()

    # Start the frontend development server with specified configuration
    subprocess.run(
        ["npm", "run", "dev", "--port", str(frontend_port), "--host", str(frontend_host)],
        cwd=str(frontend_dir),
        check=True,
    )

if __name__ == "__main__":
    start_frontend()
