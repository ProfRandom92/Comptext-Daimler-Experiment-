# --- Build Stage ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies if needed (none for now, but good practice)
RUN apt-get update && apt-get install -y --no-install-recommends     build-essential     && rm -rf /var/lib/apt/lists/*

# Install dependencies into a virtual environment to keep them separate
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Final Stage ---
FROM python:3.11-slim

WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Non-root user for security
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Document the port
EXPOSE 8000

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV LLM_BACKEND=mock

# Start the FastAPI application with uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
