# Stage 1: Runtime
FROM python:3.11-slim

# Set environment variables for quality and performance
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

WORKDIR /app

# Install system dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Use a non-privileged user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app

# Install Python requirements
COPY --chown=appuser:appuser requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY --chown=appuser:appuser . .

# Switch to the non-root user
USER appuser

# Expose port
EXPOSE 8080

# Healthcheck for reliability
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl --fail http://localhost:8080/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "app.py"]
