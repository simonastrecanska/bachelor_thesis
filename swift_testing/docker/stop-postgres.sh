#!/bin/bash

# Stop the PostgreSQL Docker container for SWIFT testing

# Get the root directory of the project
ROOT_DIR="$(dirname "$(dirname "$(dirname "$0")")")"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running or not installed"
    exit 1
fi

# Stop the containers
echo "Stopping PostgreSQL container..."
docker-compose -f "${ROOT_DIR}/docker/docker-compose.yml" down

echo "PostgreSQL container stopped."
echo ""
echo "To start it again, run: ./start-postgres.sh" 