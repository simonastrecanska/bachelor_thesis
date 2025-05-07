# SWIFT Message Testing Framework

A comprehensive framework for testing SWIFT message generation, parsing, and routing.

## Features

- Generate SWIFT MT messages based on templates
- Test message routing logic
- Validate message formatting
- Docker-based PostgreSQL database for storing message templates and test data
- Customizable model interface for implementing your own message processing logic

## Quick Start

### Option 1: One-step Setup (Recommended)

```bash
# Navigate to the root directory
cd ..

# Make the setup script executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

### Option 2: Manual Setup

1. Start the PostgreSQL database:
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

2. Set up the database tables:
   ```bash
   python3 src/database/setup_db.py --config config/config.yaml
   ```

3. Populate the database with templates and variator data:
   ```bash
   python3 populate_templates.py --config config/config.yaml
   python3 populate_variator_data.py --config config/config.yaml
   ```

4. Generate test messages:
   ```bash
   python3 generate_swift_messages.py --config config/config.yaml
   ```

5. Run tests:
   ```bash
   python3 src/run_test.py --config config/config.yaml
   ```

## Configuration

Configuration is managed through the `config/config.yaml` file. See the comments in the file for detailed explanation of each setting.

## Creating Custom Models

To create a custom model for processing SWIFT messages:

1. Create a new Python module in the `models` directory that inherits from the `CustomModel` class in `models/custom_model.py`
2. Implement the required abstract methods
3. Update the configuration to use your custom model

See `models/custom_model.py` for a template implementation and examples.
