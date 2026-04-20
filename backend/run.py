#!/usr/bin/env python
"""
FastAPI Application Startup Script

This script properly starts the FastAPI server using uvicorn.
Run from the backend directory.
"""

import subprocess
import sys
import os

def main():
    """Start the FastAPI server"""
    
    # Change to backend directory if not already there
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    if not os.getcwd().endswith('backend'):
        os.chdir(backend_dir)
    
    print("=" * 70)
    print("Starting University Comparison API")
    print("=" * 70)
    print()
    print("Server Info:")
    print("  - Host: 0.0.0.0")
    print("  - Port: 8000")
    print("  - Reload: Enabled (auto-restart on code changes)")
    print()
    print("Access the API:")
    print("  - API: http://localhost:8000")
    print("  - Docs (Swagger): http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("  - Health Check: http://localhost:8000/health")
    print()
    print("Press CTRL+C to stop the server")
    print("=" * 70)
    print()
    
    # Run uvicorn with proper settings
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\nServer stopped by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
