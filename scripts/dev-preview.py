#!/usr/bin/env python3
"""
Development preview script for contributors
Run this to generate and serve the website locally
"""
import os
import sys
import subprocess
import webbrowser
from pathlib import Path

def main():
    print("🧠 Awesome Computational Primatology - Development Preview")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists("README.md"):
        print("❌ Error: README.md not found. Please run this from the repository root.")
        sys.exit(1)
    
    # Check for required dependencies
    try:
        import pandas
        print("✅ Dependencies OK")
    except ImportError:
        print("📦 Installing pandas...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pandas"])
    
    # Generate website
    print("🏗️  Generating website...")
    try:
        # Run the website_generator.py script
        result = subprocess.run([
            sys.executable, "scripts/website_generator.py"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Website generated successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ Error generating website:")
            print(result.stderr)
            sys.exit(1)
    except Exception as e:
        print(f"❌ Error running website generator: {e}")
        sys.exit(1)
    
    # Start server
    print("🚀 Starting development server...")
    print("📱 Website will open at: http://localhost:8000")
    print("👀 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        # Open browser
        webbrowser.open("http://localhost:8000")
        
        # Start server
        subprocess.run([
            sys.executable, "-m", "http.server", "8000"
        ])
    except KeyboardInterrupt:
        print("\n👋 Development server stopped")

if __name__ == "__main__":
    main()