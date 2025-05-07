#!/bin/bash
# Root setup script for SWIFT Testing Framework

echo "===== SWIFT Testing Framework Setup ====="
echo ""

# Get the directory where this script is located (project root)
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "Project root: $PROJECT_ROOT"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running. Please start Docker first."
  exit 1
fi

# Start PostgreSQL Docker container
echo "Starting PostgreSQL Docker container..."
docker-compose -f docker/docker-compose.yml up -d

# Wait for database to be ready
echo "Waiting for database to be ready..."
for i in {1..10}; do
  if docker exec swift_testing_postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "Database is ready!"
    break
  fi
  if [ $i -eq 10 ]; then
    echo "Error: Database did not become ready in time. Check Docker logs."
    exit 1
  fi
  echo "Still waiting for database... (attempt $i/10)"
  sleep 3
done

# Create necessary directories
echo "Creating required directories..."
mkdir -p "$PROJECT_ROOT/swift_testing/input"
mkdir -p "$PROJECT_ROOT/swift_testing/output"
mkdir -p "$PROJECT_ROOT/swift_testing/logs"
mkdir -p "$PROJECT_ROOT/swift_testing/models"
mkdir -p "$PROJECT_ROOT/swift_testing/templates"
mkdir -p "$PROJECT_ROOT/swift_testing/test_output"

# Set up the database
echo ""
echo "Setting up database tables..."
python3 "$PROJECT_ROOT/swift_testing/src/database/setup_db.py" --config "$PROJECT_ROOT/config/config.yaml"

# Populate templates
echo ""
echo "Populating templates..."
python3 "$PROJECT_ROOT/swift_testing/populate_templates.py" --config "$PROJECT_ROOT/config/config.yaml"

# Populate variator data
echo ""
echo "Populating variator data..."
python3 "$PROJECT_ROOT/swift_testing/populate_variator_data.py" --config "$PROJECT_ROOT/config/config.yaml"

echo ""
echo "===== Setup Complete! ====="
echo ""
echo "You can now generate test messages with:"
echo "python3 $PROJECT_ROOT/generate_swift_messages.py --config $PROJECT_ROOT/config/config.yaml"
echo ""
echo "Or run tests with:"
echo "python3 $PROJECT_ROOT/swift_testing/src/run_test.py --config $PROJECT_ROOT/config/config.yaml" 