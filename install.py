#!/usr/bin/env python
import sys
import os
import subprocess
import importlib.metadata

# List of required packages.
REQUIRED_PACKAGES = {"pyperclip", "requests", "tqdm", "beautifulsoup4"}

# Path configuration (DO NOT MODIFY)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.extend([
    BASE_DIR,  # Project root
    os.path.join(BASE_DIR, 'src')  # Source directory
])

def install_missing_packages():
    """Install any missing packages."""
    installed = {pkg.metadata['Name'].lower() for pkg in importlib.metadata.distributions()}
    missing = REQUIRED_PACKAGES - installed
    if missing:
        print(f"Installing missing dependencies: {missing}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", *missing])

def main():
    """Main entry point for the application."""
    # Absolute import with full package path
    from src.mtg_crafter.__main__ import main as app_main
    app_main()

if __name__ == "__main__":
    install_missing_packages()
    main() 