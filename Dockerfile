# Multi-stage Dockerfile for betslip converter application

# Stage 1: Python automation environment
FROM python:3.11-slim as python-base

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/automation

# Copy Python requirements and install dependencies
COPY automation/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Copy Python automation code
COPY automation/ .

# Stage 2: Node.js backend
FROM node:18-alpine as backend

WORKDIR /app/server

# Copy package files and install dependencies
COPY server/package*.json ./
RUN npm ci --only=production

# Copy server code
COPY server/ .

# Stage 3: Frontend build
FROM node:18-alpine as frontend-build

WORKDIR /app/client

# Copy package files and install dependencies
COPY client/package*.json ./
RUN npm ci

# Copy client code and build
COPY client/ .
RUN npm run build

# Stage 4: Production image
FROM node:18-alpine as production

# Install Python for automation scripts
RUN apk add --no-cache python3 py3-pip

WORKDIR /app

# Copy backend
COPY --from=backend /app/server ./server

# Copy frontend build
COPY --from=frontend-build /app/client ./client

# Copy Python automation with dependencies
COPY --from=python-base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=python-base /usr/local/bin /usr/local/bin
COPY --from=python-base /app/automation ./automation

# Copy Playwright browsers
COPY --from=python-base /root/.cache/ms-playwright /root/.cache/ms-playwright

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Set ownership
RUN chown -R nextjs:nodejs /app
USER nextjs

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node server/health-check.js || exit 1

# Start the application
CMD ["node", "server/server.js"]