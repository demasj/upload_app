FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY config/ ./config/

# Ensure packages have __init__.py
RUN touch backend/__init__.py || true

# Setup config/__init__.py to export both Settings and get_settings
RUN printf 'from .settings import Settings, get_settings\n\n__all__ = ["Settings", "get_settings"]\n' > config/__init__.py

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/config', timeout=5)"

# Run application - set PYTHONPATH to include /app
CMD ["sh", "-c", "PYTHONPATH=/app python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
