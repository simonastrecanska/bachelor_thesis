# SWIFT Testing Framework Quick Start Guide

This guide provides the simplest way to get started with the SWIFT Testing Framework.

## Prerequisites

- Python 3.8+ installed
- Docker installed (for easy database setup)
- Git (to clone the repository)

## Setup Steps

### 1. Clone the Repository

```bash
git clone https://github.com/simonastrecanska/bachelor_thesis.git
cd bachelor_thesis
```

### 2. Create a Virtual Environment

```bash
# Create a virtual environment
python3 -m venv venv

# Activate it on macOS/Linux
source venv/bin/activate

# OR on Windows
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install required packages
pip install -r swift_testing/requirements.txt
```

### 4. Start the PostgreSQL Database with Docker

The simplest way to set up the database is using the provided Docker container:

```bash
# Start PostgreSQL
docker-compose -f docker/docker-compose.yml up -d
```

This will:
- Start a PostgreSQL container
- Make it available on port 5433

### 5. Verify Configuration

The default configuration in `config/config.yaml` is already set up to work with the Docker database. However, you should check it to make sure paths are correct for your environment.

### 6. Initialize the Database

```bash
# Set up database tables
python3 swift_testing/src/database/setup_db.py --config config/config.yaml
```

### 7. Populate Templates and Variator Data

```bash
# Load templates
python3 swift_testing/populate_templates.py --config config/config.yaml

# Load variator data
python3 swift_testing/populate_variator_data.py --config config/config.yaml
```

### 8. Generate Test Messages

```bash
# Generate SWIFT messages using templates
python3 generate_swift_messages.py --config config/config.yaml --count 10 --type MT103
```

### 9. Run Tests and Route Messages

```bash
# Test the routing model
python3 swift_testing/src/run_test.py --config config/config.yaml --name "Initial Test" --description "First test run" --messages 20

# Route a test message
python3 swift_testing/route_messages.py --config config/config.yaml --message "{1:F01BANKXXXXXYYY}{2:O1030919111026BANKZZZZ}{4::20:REF12345678:32A:091026EUR12500,00:50K:/123456789:ORDERING CUSTOMER:71A:SHA-}"
```

## Troubleshooting

### Database Connection Issues

1. Check if Docker is running
2. Verify the database connection in `config/config.yaml`
3. Try stopping and restarting the PostgreSQL container:
   ```bash
   docker stop swift_testing_postgres
   docker-compose -f docker/docker-compose.yml up -d
   ```

### Import Errors

If you get import errors, make sure you're running commands from the correct directory:

1. Run commands from the root `bachelor_thesis` directory, not the swift_testing subdirectory
2. Make sure paths to Python files include the swift_testing directory when needed

### Model Setup Issues

For model training and routing, make sure:

1. You have generated messages in the database
2. Your model directory exists (`mkdir -p models`)
3. You have the necessary machine learning dependencies installed

## Next Steps

1. **Explore the Bare Bones Router**: Check out the implementation in `swift_testing/models/custom_model.py` and extend it
2. **Customize Templates**: Add your own SWIFT message templates in the templates directory
3. **Configure for Production**: Adjust database settings for your production environment

See the full documentation in the `swift_testing/docs` directory for more advanced usage. 