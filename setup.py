# setup.py
#!/usr/bin/env python3
"""
Setup script for Job Matching System
"""

import os
import sys
import subprocess
from pathlib import Path

def create_directory_structure():
    """Create the required directory structure"""
    directories = [
        "logs",
        "uploads/resumes",
        "config",
        "models",
        "agents", 
        "services",
        "cli",
        "database",
        "utils"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py files for Python packages
        if directory not in ["logs", "uploads/resumes"]:
            init_file = Path(directory) / "__init__.py"
            if not init_file.exists():
                init_file.touch()
    
    print("✓ Directory structure created successfully!")

def create_env_template():
    """Create .env template file"""
    env_template = """# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=job_matching_db
DB_USER=postgres
DB_PASSWORD=your_password_here

# Gemini API Configuration  
# Get your API key from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Application Settings
LOG_LEVEL=INFO
MAX_RESUME_SIZE_MB=5
SUPPORTED_FILE_TYPES=pdf,docx,txt
"""
    
    env_file = Path(".env.template")
    with open(env_file, "w") as f:
        f.write(env_template)
    print("✓ .env.template created! Please copy to .env and fill in your values.")

def create_requirements():
    """Create requirements.txt with proper versions"""
    requirements = """# Database
psycopg2-binary>=2.9.7

# AI/ML
google-generativeai>=0.3.2

# Configuration
python-dotenv>=1.0.0

# CLI Interface
tabulate>=0.9.0
colorama>=0.4.6

# Utilities
click>=8.1.7
pydantic>=2.5.0

# Optional: For better resume parsing
# PyPDF2>=3.0.1
# python-docx>=0.8.11
"""
    
    req_file = Path("requirements.txt")
    with open(req_file, "w") as f:
        f.write(requirements)
    print("✓ requirements.txt created!")

def install_dependencies():
    """Install Python dependencies"""
    print("Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        print("You can install manually using: pip install -r requirements.txt")
        return False

def create_database_setup_guide():
    """Create database setup guide"""
    db_guide = """# Database Setup Guide

## PostgreSQL Installation

### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### macOS (using Homebrew):
```bash
brew install postgresql
brew services start postgresql
```

### Windows:
Download and install from: https://www.postgresql.org/download/windows/

## Database Setup

1. Switch to postgres user and create database:
```bash
sudo -u postgres psql
CREATE DATABASE job_matching_db;
CREATE USER your_username WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE job_matching_db TO your_username;
\\q
```

2. Or create database with your current user:
```bash
createdb job_matching_db
```

## Configuration

1. Copy .env.template to .env:
```bash
cp .env.template .env
```

2. Edit .env with your database credentials and Gemini API key

3. Get Gemini API key from: https://makersuite.google.com/app/apikey

## Running the Application

```bash
python main.py
```

Default admin login:
- Username: admin
- Password: admin123
"""
    
    guide_file = Path("DATABASE_SETUP.md")
    with open(guide_file, "w") as f:
        f.write(db_guide)
    print("✓ DATABASE_SETUP.md created!")

def create_quick_start():
    """Create quick start script"""
    quick_start = """#!/bin/bash
# Quick Start Script for Job Matching System

echo "🚀 Job Matching System - Quick Start"
echo "=================================="

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Copying .env.template to .env..."
    cp .env.template .env
    echo "Please edit .env file with your configuration before continuing."
    echo "You need to set:"
    echo "  - Database credentials (DB_USER, DB_PASSWORD)"
    echo "  - Gemini API key (GEMINI_API_KEY)"
    echo ""
    echo "Get Gemini API key from: https://makersuite.google.com/app/apikey"
    exit 1
fi

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo "⚠️  PostgreSQL is not running!"
    echo "Please start PostgreSQL first:"
    echo "  Linux: sudo systemctl start postgresql"
    echo "  macOS: brew services start postgresql"
    echo "  Windows: Start PostgreSQL service"
    exit 1
fi

# Run the application
echo "Starting Job Matching System..."
python main.py
"""
    
    script_file = Path("quick_start.sh")
    with open(script_file, "w") as f:
        f.write(quick_start)
    script_file.chmod(0o755)  # Make executable
    print("✓ quick_start.sh created!")

def check_system_requirements():
    """Check if system meets requirements"""
    print("Checking system requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8+ required. Current version:", sys.version)
        return False
    else:
        print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Check if pip is available
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "--version"], 
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✓ pip is available")
    except subprocess.CalledProcessError:
        print("✗ pip not found")
        return False
    
    return True

def main():
    """Setup the project"""
    print("🚀 Setting up Job Matching System...")
    print("=" * 50)
    
    # Check system requirements
    if not check_system_requirements():
        print("❌ System requirements not met!")
        sys.exit(1)
    
    # Create project structure
    create_directory_structure()
    create_env_template()
    create_requirements()
    create_database_setup_guide()
    create_quick_start()
    
    print("\n" + "=" * 50)
    print("📦 Installing dependencies...")
    
    install_success = install_dependencies()
    
    print("\n" + "=" * 50)
    print("✅ Setup completed!")
    print("\n📋 Next steps:")
    
    if install_success:
        print("1. ✓ Dependencies installed")
    else:
        print("1. Install dependencies: pip install -r requirements.txt")
    
    print("2. Set up PostgreSQL database (see DATABASE_SETUP.md)")
    print("3. Copy .env.template to .env and configure:")
    print("   - Database credentials")
    print("   - Gemini API key from: https://makersuite.google.com/app/apikey")
    print("4. Run: python main.py (or use ./quick_start.sh on Linux/macOS)")
    
    print(f"\n🔑 Default admin login:")
    print("   Username: admin")
    print("   Password: admin123")
    
    print(f"\n📚 For detailed setup, check DATABASE_SETUP.md")

if __name__ == "__main__":
    main()