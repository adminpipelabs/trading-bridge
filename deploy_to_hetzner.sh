#!/bin/bash
# Complete automated deployment script for Trading Bridge on Hetzner
# Run this on your Hetzner server: bash deploy_to_hetzner.sh

set -e

echo "=========================================="
echo "Trading Bridge - Hetzner Deployment"
echo "Server IP: 5.161.64.209"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/trading-bridge"
REPO_URL="https://github.com/adminpipelabs/trading-bridge.git"
PYTHON_VERSION="3.11"

# Step 1: Update system
echo -e "${GREEN}[1/8]${NC} Updating system packages..."
apt update -qq
apt upgrade -y -qq

# Step 2: Install dependencies
echo -e "${GREEN}[2/8]${NC} Installing system dependencies..."
apt install -y -qq \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python3-pip \
    git \
    build-essential \
    libssl-dev \
    libffi-dev \
    postgresql-client \
    curl \
    ufw

# Step 3: Create app directory
echo -e "${GREEN}[3/8]${NC} Creating app directory..."
mkdir -p ${APP_DIR}
cd ${APP_DIR}

# Step 4: Clone repository
echo -e "${GREEN}[4/8]${NC} Cloning repository..."
if [ -d ".git" ]; then
    echo -e "${YELLOW}Repository already exists, pulling latest...${NC}"
    git pull
else
    git clone ${REPO_URL} .
fi

# Step 5: Create virtual environment
echo -e "${GREEN}[5/8]${NC} Setting up Python virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment exists, skipping...${NC}"
else
    python${PYTHON_VERSION} -m venv venv
fi

source venv/bin/activate

# Step 6: Install Python dependencies
echo -e "${GREEN}[6/8]${NC} Installing Python dependencies..."
pip install --upgrade pip -q
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
else
    echo -e "${RED}⚠️  requirements.txt not found!${NC}"
    echo "Installing common dependencies..."
    pip install fastapi uvicorn sqlalchemy psycopg2-binary aiohttp ccxt cryptography python-dotenv -q
fi

# Step 7: Set up environment variables
echo -e "${GREEN}[7/8]${NC} Setting up environment variables..."
if [ ! -f ".env" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  .env file not found. Creating template...${NC}"
    cat > .env << EOF
# Database
DATABASE_URL=postgresql+psycopg2://postgres:password@host:port/dbname

# Encryption
ENCRYPTION_KEY=your_encryption_key_here

# No proxy needed on Hetzner!
# QUOTAGUARDSTATIC_URL=

# Optional: Other settings
# SOLANA_RPC_URL=
# HUMMINGBOT_API_URL=
EOF
    echo ""
    echo -e "${RED}⚠️  IMPORTANT: Edit .env file with your actual values!${NC}"
    echo "Run: nano ${APP_DIR}/.env"
    echo ""
    read -p "Press Enter after you've updated .env file..."
else
    echo -e "${GREEN}.env file exists${NC}"
fi

# Step 8: Configure firewall
echo -e "${GREEN}[8/8]${NC} Configuring firewall..."
ufw allow 22/tcp   # SSH
ufw allow 80/tcp   # HTTP
ufw allow 443/tcp  # HTTPS
ufw allow 8080/tcp # App port
echo "y" | ufw enable > /dev/null 2>&1 || true

# Step 9: Create systemd service
echo ""
echo -e "${GREEN}[9/9]${NC} Creating systemd service..."
cat > /etc/systemd/system/trading-bridge.service << EOF
[Unit]
Description=Trading Bridge API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. ${YELLOW}Edit environment variables:${NC}"
echo "   nano ${APP_DIR}/.env"
echo ""
echo "2. ${YELLOW}Whitelist IP on exchanges:${NC}"
echo "   - BitMart: Add 5.161.64.209"
echo "   - Coinstore: Add 5.161.64.209 (if required)"
echo ""
echo "3. ${YELLOW}Start the service:${NC}"
echo "   systemctl start trading-bridge"
echo "   systemctl enable trading-bridge"
echo ""
echo "4. ${YELLOW}Check status:${NC}"
echo "   systemctl status trading-bridge"
echo ""
echo "5. ${YELLOW}View logs:${NC}"
echo "   journalctl -u trading-bridge -f"
echo ""
echo "6. ${YELLOW}Test endpoint:${NC}"
echo "   curl http://localhost:8080/health"
echo ""
echo "=========================================="
