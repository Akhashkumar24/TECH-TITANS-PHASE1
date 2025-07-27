#!/bin/bash
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
