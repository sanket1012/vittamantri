#!/bin/bash
set -e

cd "$(dirname "$0")/../backend"

# Start Telegram bot in background with auto-restart
while true; do
    python bot.py || echo "Bot exited ($?), restarting in 5s..."
    sleep 5
done &

# Start Flask via gunicorn (foreground — keeps the dyno alive)
exec gunicorn --workers 2 --bind "0.0.0.0:${PORT:-8000}" --timeout 120 --access-logfile - main:app
