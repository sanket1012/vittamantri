#!/bin/bash
# One-time setup for Ubuntu 22.04 EC2 instance.
# Run from the repo root: bash deploy/setup.sh
set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo "Setting up VittaMantri from: $APP_DIR"

# ── System packages ───────────────────────────────────────────────────────────
sudo apt-get update -qq
sudo apt-get install -y nginx python3.11 python3.11-venv python3-pip nodejs npm

# ── Log directory ─────────────────────────────────────────────────────────────
sudo mkdir -p /var/log/vittamantri
sudo chown ubuntu:ubuntu /var/log/vittamantri

# ── Python virtual environment (3.11 — stable wheel support) ─────────────────
python3.11 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
"$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/backend/requirements.txt"

# ── React frontend build ──────────────────────────────────────────────────────
cd "$APP_DIR/frontend"
npm ci --silent
npm run build
cd "$APP_DIR"

# ── Data directory ────────────────────────────────────────────────────────────
mkdir -p "$APP_DIR/data"

# ── Nginx ─────────────────────────────────────────────────────────────────────
sudo cp "$APP_DIR/deploy/nginx.conf" /etc/nginx/sites-available/vittamantri
sudo ln -sf /etc/nginx/sites-available/vittamantri /etc/nginx/sites-enabled/vittamantri
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

# ── Systemd services ──────────────────────────────────────────────────────────
sudo cp "$APP_DIR/deploy/vittamantri-api.service" /etc/systemd/system/
sudo cp "$APP_DIR/deploy/vittamantri-bot.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vittamantri-api vittamantri-bot
sudo systemctl restart vittamantri-api vittamantri-bot

echo ""
echo "✓ Setup complete."
echo "  API:       http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)/api/health"
echo "  Dashboard: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)"
echo ""
echo "Check service status:"
echo "  sudo systemctl status vittamantri-api"
echo "  sudo systemctl status vittamantri-bot"
