#!/bin/bash
# Automated Trading Bridge Deployment Script for Hetzner
# Run as root: bash deploy_hetzner.sh

set -e

echo "=========================================="
echo "Trading Bridge - Hetzner Automated Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/trading-bridge"
APP_USER="root"
REPO_URL="https://github.com/adminpipelabs/trading-bridge.git"
SERVICE_NAME="trading-bridge"
PORT="8080"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}❌ Please run as root${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Running as root${NC}"
echo ""

# Step 1: Update system
echo -e "${YELLOW}📦 Step 1: Updating system packages...${NC}"
apt update -qq
apt upgrade -y -qq
echo -e "${GREEN}✅ System updated${NC}"
echo ""

# Step 2: Install dependencies
echo -e "${YELLOW}📦 Step 2: Installing dependencies...${NC}"
apt install -y python3.11 python3.11-venv python3-pip git build-essential libssl-dev libffi-dev postgresql-client curl ufw > /dev/null 2>&1
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 3: Create app directory
echo -e "${YELLOW}📁 Step 3: Creating app directory...${NC}"
mkdir -p "$APP_DIR"
cd "$APP_DIR"
echo -e "${GREEN}✅ Directory created: $APP_DIR${NC}"
echo ""

# Step 4: Clone repository
echo -e "${YELLOW}📥 Step 4: Cloning repository...${NC}"
if [ -d ".git" ]; then
    echo "Repository already exists, pulling latest..."
    git pull
else
    git clone "$REPO_URL" .
fi
echo -e "${GREEN}✅ Repository cloned${NC}"
echo ""

# Step 5: Create Python virtual environment
echo -e "${YELLOW}🐍 Step 5: Setting up Python environment...${NC}"
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
echo -e "${GREEN}✅ Virtual environment created${NC}"
echo ""

# Step 6: Install Python dependencies
echo -e "${YELLOW}📦 Step 6: Installing Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt -q
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
else
    echo -e "${RED}⚠️  requirements.txt not found${NC}"
fi
echo ""

# Step 7: Create .env file if it doesn't exist
echo -e "${YELLOW}⚙️  Step 7: Setting up environment variables...${NC}"
if [ ! -f ".env" ]; then
    echo "Creating .env file..."
    cat > .env << EOF
# Database
DATABASE_URL=postgresql+psycopg2://postgres:password@host:port/dbname

# Encryption
ENCRYPTION_KEY=your_encryption_key_here

# No proxy needed on Hetzner!
# QUOTAGUARDSTATIC_URL=

# Server IP (for reference)
SERVER_IP=5.161.64.209
EOF
    echo -e "${YELLOW}⚠️  .env file created - PLEASE EDIT IT WITH YOUR VALUES!${NC}"
    echo "   Run: nano $APP_DIR/.env"
else
    echo -e "${GREEN}✅ .env file already exists${NC}"
fi
echo ""

# Step 8: Create systemd service
echo -e "${YELLOW}🔧 Step 8: Creating systemd service...${NC}"
cat > /etc/systemd/system/${SERVICE_NAME}.service << EOF
[Unit]
Description=Trading Bridge API
After=network.target

[Service]
Type=simple
User=${APP_USER}
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
EnvironmentFile=${APP_DIR}/.env
ExecStart=${APP_DIR}/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
echo -e "${GREEN}✅ Systemd service created${NC}"
echo ""

# Step 9: Configure firewall
echo -e "${YELLOW}🔥 Step 9: Configuring firewall...${NC}"
ufw --force enable > /dev/null 2>&1
ufw allow 22/tcp > /dev/null 2>&1  # SSH
ufw allow 80/tcp > /dev/null 2>&1  # HTTP
ufw allow 443/tcp > /dev/null 2>&1 # HTTPS
ufw allow ${PORT}/tcp > /dev/null 2>&1 # App port
echo -e "${GREEN}✅ Firewall configured${NC}"
echo ""

# Step 10: Display summary
echo "=========================================="
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Edit environment variables:"
echo "   ${YELLOW}nano $APP_DIR/.env${NC}"
echo "   - Set DATABASE_URL"
echo "   - Set ENCRYPTION_KEY"
echo ""
echo "2. Whitelist IP on exchanges:"
echo "   - BitMart: Add ${GREEN}5.161.64.209${NC}"
echo "   - Coinstore: Add ${GREEN}5.161.64.209${NC} (if required)"
echo ""
echo "3. Start the service:"
echo "   ${YELLOW}systemctl start ${SERVICE_NAME}${NC}"
echo "   ${YELLOW}systemctl enable ${SERVICE_NAME}${NC}"
echo ""
echo "4. Check status:"
echo "   ${YELLOW}systemctl status ${SERVICE_NAME}${NC}"
echo "   ${YELLOW}journalctl -u ${SERVICE_NAME} -f${NC}"
echo ""
echo "5. Test the API:"
echo "   ${YELLOW}curl http://localhost:${PORT}/health${NC}"
echo ""
echo "=========================================="
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Edit .env file before starting!${NC}"
echo ""
