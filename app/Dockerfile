# Stage 1: Build the Vite app
FROM node:20-slim AS build-stage

WORKDIR /frontend
COPY frontend/package*.json ./

# Install ALL dependencies (including dev dependencies needed for build)
RUN npm ci

# Copy frontend source and build
COPY frontend/ ./

# Debug: Show what we're building
RUN echo "=== Vite Config ===" && cat vite.config.ts

# Build the frontend
RUN npm run build

# Debug: Check what was built and where
RUN echo "=== All contents after build ===" && ls -la
RUN echo "=== Looking for dist folder ===" && find . -name "dist" -type d
RUN echo "=== Looking for built files ===" && find . -name "*.html" -o -name "*.js" -o -name "*.css" | head -10

# Stage 2: Setup Python FastAPI backend
FROM python:3.10-slim AS production-stage

WORKDIR /app

# Install system dependencies (removed audio packages for headless mode)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend code
COPY ./backend/ /app

# Copy built frontend static files from build stage to /app/static
COPY --from=build-stage /frontend/dist /app/static

# Debug: Check if static files were copied
RUN echo "=== Static files after copy ===" && ls -la /app/static/
RUN echo "=== Static file contents ===" && find /app/static -name "*.html" -exec head -5 {} \;

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV HEADLESS_MODE=true

RUN python -m pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]