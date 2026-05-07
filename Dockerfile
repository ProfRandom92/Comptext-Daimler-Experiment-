FROM python:3.11-slim

WORKDIR /app

# Install dependencies first for layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Render uses the PORT environment variable
ENV PORT=10000
EXPOSE 10000

# Default: FastAPI API
CMD uvicorn api:app --host 0.0.0.0 --port ${PORT}
