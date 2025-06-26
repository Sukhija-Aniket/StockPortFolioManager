FROM python:3.8-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx curl git && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .

# Install shared package from git repository with specific version tag
RUN pip install --force-reinstall git+https://github.com/Sukhija-Aniket/StockPortfolioManager.git@v0.1.3#subdirectory=shared

# Install other dependencies
RUN pip install -r requirements.txt

# Copy backend code
COPY . /app/

# Install additional dependencies
RUN pip install multipart

# Set working directory
WORKDIR /app

# Expose the port used by the backend service
EXPOSE 5000

# Start the backend service
CMD ["python", "app.py"] 