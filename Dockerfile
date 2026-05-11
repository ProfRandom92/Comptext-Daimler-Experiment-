FROM node:20-slim AS frontend-builder

WORKDIR /frontend

COPY showcase/package*.json ./
RUN npm ci

COPY showcase/ ./
RUN npm run build

FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Install Python dependencies first for layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=frontend-builder /frontend/dist ./showcase/dist

# Non-root user for security.
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 10000

CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT}"]
