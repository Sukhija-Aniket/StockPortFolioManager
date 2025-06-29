# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies including git
RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Use build argument for version
ARG SHARED_VERSION=v0.1.14

# Install shared package from git repository with specific version tag
RUN pip install --force-reinstall git+https://github.com/Sukhija-Aniket/StockPortfolioManager.git@${SHARED_VERSION}#subdirectory=shared

# Install other dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY . /app/

# Create logs directory and set permissions
RUN mkdir -p /app/logs && chmod 755 /app/logs

# Set working directory
WORKDIR /app

# Run the worker script when the container launches
CMD ["python", "worker.py"]