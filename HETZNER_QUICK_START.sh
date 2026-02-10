#!/bin/bash
# Quick start script for Hetzner deployment
# Run this on your Hetzner server after SSH'ing in

set -e

echo "=========================================="
echo "Trading Bridge - Hetzner Deployment"
echo "=========================================="
echo ""

# Check Python version
echo "📦 Checking Python..."
python3 --version || echo "❌ Python 3 not found - will install"

# Check Git
echo "📦 Checking Git..."
git --version || echo "❌ Git not found - will install"

# Update system
echo ""
echo "🔄 Updating system packages..."
apt update

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
apt install -y python3.11 python3.11-venv python3-pip git build-essential libssl-dev libffi-dev postgresql-client

# Create app directory
echo ""
echo "📁 Creating app directory..."
mkdir -p /opt/trading-bridge
cd /opt/trading-bridge

# Clone repository
echo ""
echo "📥 Cloning repository..."
echo "Enter your GitHub repo URL (or press Enter to skip):"
read -r REPO_URL

if [ -n "$REPO_URL" ]; then
    git clone "$REPO_URL" .
else
    echo "⚠️  Skipping clone - you can clone manually later"
fi

# Create virtual environment
echo ""
echo "🐍 Creating Python virtual environment..."
python3.11 -m venv venv
source venv/bin/activate

# Install Python dependencies
if [ -f "requirements.txt" ]; then
    echo ""
    echo "📦 Installing Python dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "⚠️  No requirements.txt found - install dependencies manually"
fi

echo ""
echo "✅ Basic setup complete!"
echo ""
echo "Next steps:"
echo "1. Set up environment variables (.env file)"
echo "2. Configure DATABASE_URL"
echo "3. Whitelist IP 5.161.64.209 on BitMart and Coinstore"
echo "4. Start the application"
echo ""
echo "See HETZNER_DEPLOYMENT_GUIDE.md for detailed instructions"
