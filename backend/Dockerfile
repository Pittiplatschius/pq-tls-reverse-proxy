# backend/Dockerfile
FROM ubuntu:22.04

# Install Python, pip, and Flask
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    && pip3 install Flask \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy Flask application
COPY ./app.py /app/

# Expose port Flask runs on
EXPOSE 5000

# Command to run Flask app
CMD ["python3", "app.py"]