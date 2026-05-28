#!/bin/sh
set -e

cd /app/backend

# Start Telegram bot in background; restart it if it crashes
while true; do
    python bot.py || echo "Bot exited with $?, restarting in 5s..."
    sleep 5
done &

# Start Flask with gunicorn (foreground — container stays alive as long as this runs)
exec gunicorn --workers 2 --bind 0.0.0.0:8000 --timeout 120 --access-logfile - main:app
