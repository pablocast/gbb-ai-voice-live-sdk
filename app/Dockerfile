# Stage 1: Build the Vite React frontend
FROM node:20-slim AS build-stage

# Set the working directory for frontend build
WORKDIR /frontend

# Copy package files first for better layer caching
COPY frontend/package*.json ./
RUN npm ci --only=production

# Copy frontend source and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Setup Python FastAPI backend
FROM python:3.10-slim AS production-stage

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies (needed for PyAudio and other audio libs)
RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    libasound-dev \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY backend/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install FastAPI production dependencies
RUN pip install --no-cache-dir \
    uvicorn[standard]==0.24.0 \
    gunicorn==21.2.0

# Copy backend source code
COPY backend/ /app/

# Copy built frontend static files to serve them
COPY --from=build-stage /frontend/dist /app/static

# Create a non-root user for security
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose the port FastAPI will run on
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the FastAPI application with Uvicorn
# For production with multiple workers, use:
# CMD ["gunicorn", "app:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]