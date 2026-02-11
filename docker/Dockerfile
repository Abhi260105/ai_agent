# Multi-stage Dockerfile for Production
# Stage 1: Build dependencies and compile assets
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production && \
    npm cache clean --force

# Copy application source
COPY . .

# Build application (if using TypeScript or bundler)
RUN npm run build

# Stage 2: Python dependencies (if using Python)
FROM python:3.11-slim AS python-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 3: Final production image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && \
    useradd -r -g appuser -u 1001 appuser && \
    chown -R appuser:appuser /app

# Install runtime dependencies only
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=python-builder /root/.local /home/appuser/.local

# Copy Node.js if needed
COPY --from=builder /usr/local/bin/node /usr/local/bin/
COPY --from=builder /usr/local/lib/node_modules /usr/local/lib/node_modules

# Copy application files
COPY --chown=appuser:appuser --from=builder /app/dist ./dist
COPY --chown=appuser:appuser --from=builder /app/node_modules ./node_modules
COPY --chown=appuser:appuser . .

# Set environment variables
ENV NODE_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH=/home/appuser/.local/bin:$PATH

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Switch to non-root user
USER appuser

# Start application
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]