#!/bin/bash
# ==============================================================================
# SANKHYAI Platform - AWS EC2 (Free Tier) Automated Deployment Script
# Target OS: Ubuntu 22.04 LTS or 24.04 LTS
# Designed for: t2.micro / t3.micro (1 vCPU, 1 GB RAM) + 4GB Swap
# ==============================================================================

set -e

echo "=========================================================="
echo "🚀 SANKHYAI AWS Free Tier Deployment Starting..."
echo "=========================================================="

# 1. Setup 4GB Swap File (Crucial for 1GB RAM instances to prevent OOM)
if [ ! -f /swapfile ]; then
    echo "📦 [1/7] Creating 4GB Swap Memory..."
    sudo fallocate -l 4G /swapfile || sudo dd if=/dev/zero of=/swapfile bs=1M count=4096
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "✅ Swap memory enabled: 4GB"
else
    echo "ℹ️  Swapfile already exists. Skipping."
fi

# 2. Update System Packages
echo "🔄 [2/7] Updating system packages & installing core dependencies..."
sudo apt-get update -y
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    postgresql \
    postgresql-contrib \
    postgresql-server-dev-all \
    git \
    curl \
    nginx \
    build-essential

# 3. Install Node.js 20.x LTS
if ! command -v node &> /dev/null; then
    echo "📦 [3/7] Installing Node.js 20 LTS..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi
echo "Node.js version: $(node -v)"
echo "NPM version: $(npm -v)"

# 4. Install pgvector for PostgreSQL
echo "🐘 [4/7] Compiling & installing pgvector extension for PostgreSQL..."
if [ ! -d "/tmp/pgvector" ]; then
    cd /tmp
    git clone --branch v0.7.4 https://github.com/pgvector/pgvector.git
    cd pgvector
    make
    sudo make install
    rm -rf /tmp/pgvector
fi

# Start & Enable PostgreSQL
sudo systemctl enable postgresql
sudo systemctl start postgresql

# Create Database and User (default credentials matching deployment)
echo "Setting up PostgreSQL database and user..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_user WHERE usename = 'sankhyai_user'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE USER sankhyai_user WITH PASSWORD 'sankhyai_secure_pass';"

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname = 'sih_platform'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE sih_platform OWNER sankhyai_user;"

sudo -u postgres psql -d sih_platform -c "CREATE EXTENSION IF NOT EXISTS vector;"
sudo -u postgres psql -d sih_platform -c "GRANT ALL PRIVILEGES ON DATABASE sih_platform TO sankhyai_user;"
sudo -u postgres psql -d sih_platform -c "GRANT ALL ON SCHEMA public TO sankhyai_user;"

# 5. Setup Python Virtual Environment & Backend
echo "🐍 [5/7] Configuring Python Backend..."
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_DIR/backend"

if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Configure .env if not present
if [ ! -f ".env" ]; then
    cp .env.example .env
    # Update DB URL for server PostgreSQL
    sed -i 's|DATABASE_URL=.*|DATABASE_URL=postgresql://sankhyai_user:sankhyai_secure_pass@localhost:5432/sih_platform|g' .env
fi

# Run Database Migrations & Seeds
echo "Running Alembic migrations..."
alembic upgrade head

echo "Seeding initial MoSPI competency framework data..."
python3 -m app.core.seed_data || true

# 6. Build Frontend for Production
echo "⚛️  [6/7] Building React Frontend..."
cd "$PROJECT_DIR/frontend"
npm install
VITE_API_BASE_URL=/api/v1 npm run build

# 7. Configure Nginx and Systemd Services
echo "⚙️  [7/7] Configuring Systemd and Nginx Services..."
CURRENT_USER=$(whoami)

# Systemd Service for FastAPI
sudo bash -c "cat > /etc/systemd/system/sankhyai-backend.service <<EOF
[Unit]
Description=SANKHYAI FastAPI Backend Service
After=network.target postgresql.service

[Service]
User=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR/backend
ExecStart=$PROJECT_DIR/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5
EnvironmentFile=$PROJECT_DIR/backend/.env

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl enable sankhyai-backend
sudo systemctl restart sankhyai-backend

# Nginx Site Configuration
sudo bash -c "cat > /etc/nginx/sites-available/sankhyai <<EOF
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    root $PROJECT_DIR/frontend/dist;
    index index.html;

    # Gzip Compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    location / {
        try_files \\\$uri \\\$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \\\$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \\\$host;
        proxy_cache_bypass \\\$http_upgrade;
        proxy_set_header X-Real-IP \\\$remote_addr;
        proxy_set_header X-Forwarded-For \\\$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \\\$scheme;
        proxy_read_timeout 180s;
        proxy_connect_timeout 60s;
    }
}
EOF"

sudo rm -f /etc/nginx/sites-enabled/default
sudo ln -sf /etc/nginx/sites-available/sankhyai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

echo ""
echo "=========================================================="
echo "🎉 DEPLOYMENT COMPLETE!"
echo "Public App URL: http://$(curl -s http://checkip.amazonaws.com || echo 'YOUR_EC2_PUBLIC_IP')"
echo "Backend API Docs: http://$(curl -s http://checkip.amazonaws.com || echo 'YOUR_EC2_PUBLIC_IP')/api/v1/docs"
echo "Check Status: sudo systemctl status sankhyai-backend"
echo "=========================================================="
