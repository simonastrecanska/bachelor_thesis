#!/bin/bash

# Start the PostgreSQL Docker container for SWIFT testing

# Change to the docker directory
cd "$(dirname "$0")"

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running or not installed"
    echo "Please start Docker and try again"
    exit 1
fi

# Start the containers
echo "Starting PostgreSQL container for SWIFT testing..."
docker-compose up -d

# Wait for container to be healthy
echo "Waiting for PostgreSQL to be ready..."
timeout=60
start_time=$(date +%s)
while true; do
    if docker-compose ps | grep -q "healthy"; then
        echo "PostgreSQL is ready!"
        break
    fi
    
    current_time=$(date +%s)
    elapsed=$((current_time - start_time))
    
    if [ $elapsed -ge $timeout ]; then
        echo "Error: PostgreSQL container did not become healthy within $timeout seconds"
        echo "Check docker logs with: docker-compose logs postgres"
        exit 1
    fi
    
    echo "Waiting for PostgreSQL to start... ($elapsed seconds)"
    sleep 5
done

# Print connection information
echo ""
echo "=============================================================="
echo "PostgreSQL is running!"
echo "=============================================================="
echo "Connection Information:"
echo "  Host:     localhost"
echo "  Port:     5432"
echo "  Database: swift_testing"
echo "  Username: swift_user"
echo "  Password: YOUR_PASSWORD"
echo ""
echo "Use the following PostgreSQL connection string in config.yaml:"
echo "postgresql://swift_user:YOUR_PASSWORD@localhost:5432/swift_testing"
echo ""
echo "To stop the container run: ./stop-postgres.sh"
echo "==============================================================" 