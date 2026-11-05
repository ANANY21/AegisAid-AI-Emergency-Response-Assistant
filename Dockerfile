# Multi-stage build for AegisAid - AI Emergency Response Assistant

# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python Backend
FROM python:3.11-slim AS production
WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source & data
COPY backend/ ./backend/

# Copy built frontend assets to static directory
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Setup environment variables
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONPATH=/app/backend

EXPOSE 8000

# Run FastAPI production server
CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
