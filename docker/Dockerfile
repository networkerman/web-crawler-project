FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (only Chromium for production)
RUN playwright install --with-deps chromium

# Copy application code
COPY src/ ./src/
COPY config.yaml .
COPY pyproject.toml .

# Install package
RUN pip install -e .

# Create non-root user for security
RUN useradd -m -u 1000 crawler && \
    chown -R crawler:crawler /app

# Switch to non-root user
USER crawler

# Create directories for state and logs
RUN mkdir -p /app/data /app/logs

# Set volume mount points
VOLUME ["/app/data", "/app/logs"]

# Expose port (if needed for monitoring)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from web_crawler import get_performance_report; print('OK')" || exit 1

# Default command
ENTRYPOINT ["python", "-m", "web_crawler.cli"]

# Default arguments
CMD ["--help"]
