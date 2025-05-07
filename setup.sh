#!/bin/bash
# Root setup script for SWIFT Testing Framework

# Enable exit on error
set -e

echo "===== SWIFT Testing Framework Setup ====="
echo ""

# Get the directory where this script is located (project root)
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "Project root: $PROJECT_ROOT"
echo ""

# Function to print errors in red
error_message() {
  echo -e "\033[0;31mERROR: $1\033[0m"
}

# Function to print success messages in green
success_message() {
  echo -e "\033[0;32m$1\033[0m"
}

# Function to print info messages in blue
info_message() {
  echo -e "\033[0;34m$1\033[0m"
}

# Check if config.yaml exists
if [ ! -f "$PROJECT_ROOT/config/config.yaml" ]; then
  error_message "config.yaml not found. Please create this file based on the example."
  exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  error_message "Docker is not running. Please start Docker first."
  exit 1
fi

# Stop any existing containers to avoid conflicts
info_message "Stopping any existing PostgreSQL containers..."
docker-compose -f docker/docker-compose.yml down 2>/dev/null || true

# Start PostgreSQL Docker container
info_message "Starting PostgreSQL Docker container..."
docker-compose -f docker/docker-compose.yml up -d

# Get the actual container name (in case it's different from what we expect)
PG_CONTAINER=$(docker-compose -f docker/docker-compose.yml ps -q postgres)
if [ -z "$PG_CONTAINER" ]; then
  error_message "Failed to get PostgreSQL container ID. Check docker-compose.yml and ensure the service is named 'postgres'."
  
  # Try to get any running postgres container as a fallback
  PG_CONTAINER=$(docker ps | grep postgres | awk '{print $1}' | head -n 1)
  
  if [ -z "$PG_CONTAINER" ]; then
    error_message "No PostgreSQL containers found. Setup failed."
    exit 1
  else
    info_message "Found alternative PostgreSQL container: $PG_CONTAINER"
  fi
fi

echo "PostgreSQL container ID: $PG_CONTAINER"

# Wait for database to be ready
info_message "Waiting for database to be ready..."
for i in {1..20}; do
  if docker exec $PG_CONTAINER pg_isready -U postgres > /dev/null 2>&1; then
    success_message "Database is ready!"
    break
  fi
  if [ $i -eq 20 ]; then
    error_message "Database did not become ready in time. Check Docker logs with:"
    echo "docker logs $PG_CONTAINER"
    
    # Check if there are port conflicts
    if docker logs $PG_CONTAINER 2>&1 | grep -q "address already in use"; then
      error_message "Port conflict detected. Try changing the port in docker-compose.yml."
      echo "Run: lsof -i :5433 # To see which process is using this port"
    fi
    
    exit 1
  fi
  echo "Still waiting for database... (attempt $i/20)"
  sleep 5
done

# Validate database connection
info_message "Validating database connection..."
if ! docker exec $PG_CONTAINER psql -U postgres -c "SELECT 1" > /dev/null 2>&1; then
  error_message "Could not connect to PostgreSQL. Check credentials in docker-compose.yml."
  exit 1
fi

# Create necessary directories
info_message "Creating required directories..."
mkdir -p "$PROJECT_ROOT/models"  # Root models directory for trained model files
mkdir -p "$PROJECT_ROOT/swift_testing/input"
mkdir -p "$PROJECT_ROOT/swift_testing/output"
mkdir -p "$PROJECT_ROOT/swift_testing/logs"
mkdir -p "$PROJECT_ROOT/swift_testing/models"
mkdir -p "$PROJECT_ROOT/swift_testing/templates"
mkdir -p "$PROJECT_ROOT/swift_testing/test_output"

# Set up the database
echo ""
info_message "Setting up database tables..."
python3 "$PROJECT_ROOT/swift_testing/src/database/setup_db.py" --config "$PROJECT_ROOT/config/config.yaml" || {
  error_message "Database setup failed. Check if database settings in config.yaml match docker-compose.yml"
  exit 1
}

# Populate templates
echo ""
info_message "Populating templates..."
python3 "$PROJECT_ROOT/swift_testing/populate_templates.py" --config "$PROJECT_ROOT/config/config.yaml" || {
  error_message "Template population failed."
  exit 1
}

# Populate variator data
echo ""
info_message "Populating variator data..."
python3 "$PROJECT_ROOT/swift_testing/populate_variator_data.py" --config "$PROJECT_ROOT/config/config.yaml" || {
  error_message "Variator data population failed."
  exit 1
}

echo ""
success_message "===== Setup Complete! ====="
echo ""
info_message "You can now generate test messages with:"
echo "python3 $PROJECT_ROOT/generate_swift_messages.py --config $PROJECT_ROOT/config/config.yaml"
echo ""
info_message "Or run tests with:"
echo "python3 $PROJECT_ROOT/swift_testing/src/run_test.py --config $PROJECT_ROOT/config/config.yaml"

echo ""
info_message "If you encounter any issues, please check the troubleshooting section in the README." 