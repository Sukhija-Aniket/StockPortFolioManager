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

# Copy the current directory contents into the container at /app
COPY worker/ .

# Create logs directory and set permissions
RUN mkdir -p logs && chmod 755 logs

# Run the worker script when the container launches
CMD ["python", "worker.py"]