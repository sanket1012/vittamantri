FROM python:3.11-slim AS backend-deps
WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt gunicorn

FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --omit=dev
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app

# Copy installed Python packages
COPY --from=backend-deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-deps /usr/local/bin/gunicorn /usr/local/bin/gunicorn

# Copy backend source
COPY backend/ ./backend/

# Copy built React frontend
COPY --from=frontend-build /frontend/dist ./frontend/dist

# Persistent data directory (mounted as a Fly Volume in production)
RUN mkdir -p ./data

COPY scripts/start.sh ./start.sh
RUN chmod +x ./start.sh

EXPOSE 8000

CMD ["./start.sh"]
