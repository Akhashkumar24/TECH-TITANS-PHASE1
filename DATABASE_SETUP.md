# Database Setup Guide

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
\q
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
