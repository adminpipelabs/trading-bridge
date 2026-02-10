#!/bin/bash
# Quick deployment script for Hetzner - pull latest code and restart service

set -e

APP_DIR="/opt/trading-bridge"
SERVICE_NAME="trading-bridge"

echo "=========================================="
echo "Deploying Trading Bridge to Hetzner"
echo "=========================================="
echo ""

cd "$APP_DIR"

echo "📥 Pulling latest code from GitHub..."
git pull origin main

echo ""
echo "🔄 Restarting service..."
systemctl restart "$SERVICE_NAME"

echo ""
echo "⏳ Waiting for service to start..."
sleep 3

echo ""
echo "📊 Checking service status..."
systemctl status "$SERVICE_NAME" --no-pager -l | head -20

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Check logs with: journalctl -u trading-bridge -f"
