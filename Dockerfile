# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including wget for healthcheck and gosu for user switching
RUN apt-get update && apt-get install -y \
    wget \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/database /app/data && \
    chown -R appuser:appuser /app

# Copy requirements first for better caching
COPY --chown=appuser:appuser requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY --chown=appuser:appuser . .

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Expose port

# Expose port
EXPOSE 5003

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Use entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
