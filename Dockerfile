# Use a highly stable, widely tested base image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install only the essential system packages for the healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirement file first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port Streamlit will run on
EXPOSE 8080

# Configure Streamlit to run on Cloud Run's expected port
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Set health check
HEALTHCHECK CMD curl --fail http://localhost:8080/_stcore/health

# Define the command to run the app
ENTRYPOINT ["streamlit", "run", "app.py"]
