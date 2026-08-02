FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Expose default port (Render overrides via $PORT env var)
EXPOSE 8000

# Use shell form so $PORT env variable is expanded at runtime
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}
