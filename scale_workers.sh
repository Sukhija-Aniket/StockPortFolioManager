#!/bin/bash

# Script to scale worker instances for high load
# Usage: ./scale_workers.sh [number_of_workers]

set -e

# Default number of workers
DEFAULT_WORKERS=2
WORKERS=${1:-$DEFAULT_WORKERS}

echo "Scaling workers to $WORKERS instances..."

# Scale the worker service
docker-compose up -d --scale worker=$WORKERS

echo "Worker scaling completed!"
echo "Current worker instances:"
docker-compose ps worker

echo ""
echo "To monitor worker logs:"
echo "docker-compose logs -f worker"
echo ""
echo "To check RabbitMQ management UI:"
echo "http://localhost:15672 (username: username, password: password)" 