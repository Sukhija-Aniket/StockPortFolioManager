# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy shared package first
COPY shared /app/shared

# Install shared package
RUN pip install -e /app/shared

# Copy the requirements file into the container at /app
COPY worker/requirements.txt .

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker contents to worker subdirectory
COPY worker/ /app/worker/

# Create logs directory and set permissions
RUN mkdir -p /app/worker/logs && chmod 755 /app/worker/logs

# Set working directory to worker
WORKDIR /app/worker

# Run the worker script when the container launches
CMD ["python", "worker.py"]