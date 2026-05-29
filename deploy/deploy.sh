#!/bin/bash
# Re-deploy after a git pull. Run from the repo root: bash deploy/deploy.sh
set -e

APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"
echo "Deploying VittaMantri from: $APP_DIR"

# Pull latest code
git pull

# Update Python dependencies if requirements changed
"$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/backend/requirements.txt"

# Rebuild React frontend
cd "$APP_DIR/frontend"
npm ci --silent
npm run build
cd "$APP_DIR"

# Restart services
sudo systemctl restart vittamantri-api vittamantri-bot

echo "✓ Deploy complete."
sudo systemctl status vittamantri-api --no-pager
