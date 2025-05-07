# SWIFT Message Testing Framework

A framework for testing SWIFT message generation, routing, and processing.

## Features

- Generate SWIFT MT messages based on templates
- Test message routing logic
- Validate message formatting
- Docker-based PostgreSQL database for storing message templates and test data
- Customizable model interface for implementing your own message processing logic

## Prerequisites

- Python 3.8+ installed
- Docker installed (for easy database setup)
- Git (to clone the repository)

## Quick Start

The default configuration in `config/config.yaml` is already set up to work with the Docker database. However, you should check it to make sure paths are correct for your environment. You can copy config.yaml.example file and put there your confuguration for database and save it as config.yaml
Please also add your database password to this line:
      POSTGRES_PASSWORD: "YOUR_PASSWORD" 
in docker-compose.yml

First step you need to do is install dependencies:
```bash
# Install required packages
pip install -r swift_testing/requirements.txt
```

### Option 1: One-step Setup (Recommended)

```bash
# You need to be in the root directorys
# Run the setup script
./setup.sh
```

This script will:
1. Start the PostgreSQL Docker container
2. Create necessary database tables
3. Populate templates and variator data
4. Prepare everything for generating test messages

### Option 2: Manual Setup

If you prefer to run commands individually:

1. Start the PostgreSQL database:
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

2. Set up the database tables:
   ```bash
   python3 swift_testing/src/database/setup_db.py --config config/config.yaml
   ```

3. Populate the database:
   ```bash
   python3 swift_testing/populate_templates.py --config config/config.yaml
   python3 swift_testing/populate_variator_data.py --config config/config.yaml
   ```

## Usage

### Generating Messages

Generate SWIFT messages from templates:

```bash
python3 generate_swift_messages.py --config config/config.yaml --count 10 --type MT103
```

Parameters:
- `--count`: Number of messages to generate
- `--type`: The template type to use (e.g., MT103, MT202)

### Running Tests

Run a complete test with specified parameters:

```bash
python3 swift_testing/src/run_test.py --config config/config.yaml --name "Test Run" --description "Testing routing" --messages 20
```

### Testing a Single Message

Test the routing of a specific SWIFT message:

```bash
python3 swift_testing/route_messages.py --config config/config.yaml --message "{1:F01BANKXXXXXYYY}{2:O1030919111026BANKZZZZ}{4::20:REF12345678:32A:091026EUR12500,00:50K:/123456789:ORDERING CUSTOMER:71A:SHA-}"
```

## Configuration

Configuration is managed through `config/config.yaml`. Key sections include:
- Database connection settings
- Model configuration
- Test parameters
- Evaluation metrics

## Creating Custom Models

To create a custom model for processing SWIFT messages:

1. Create a new Python module in the `models` directory that inherits from the `CustomModel` class in `swift_testing/models/custom_model.py`
2. Implement the required abstract methods
3. Update the configuration to use your custom model

See `swift_testing/models/custom_model.py` for a template implementation and examples.

## Model Structure

The repository already includes a complete model setup for your use:

1. **Model Interface**: `swift_testing/models/custom_model.py` - Template class showing how to implement a custom model
2. **Model Implementation**: Source code that defines message processing logic is in `swift_testing/src/models/`
3. **Pre-trained Model**: A working serialized model file (`model_v1.0.0.pkl`) is available in the root `models/` directory

The config.yaml references the pre-trained model with the path `models/model_v1.0.0.pkl`. This path is relative to the project root.

If you create your own model, you can either:
- Replace the existing model file at `models/model_v1.0.0.pkl`
- Create a new model file and update the path in the config.yaml file

## Project Structure

```
.
├── config/                         - Configuration files
├── docker/                         - Docker configuration
├── generate_swift_messages.py      - Script to generate messages
├── models/                         - Trained model files
│   └── model_v1.0.0.pkl            - Pre-trained model (already included)
├── setup.sh                        - One-step setup script
└── swift_testing/                  - Main package
    ├── populate_templates.py       - Template population script
    ├── populate_variator_data.py   - Variator data script
    ├── requirements.txt            - Python dependencies
    ├── route_messages.py           - Message routing script
    ├── src/                        - Source code
    │   ├── database/               - Database modules
    │   ├── message_generator/      - Message generation modules
    │   └── models/                 - Model implementation code
    │       └── custom_model.py     - Custom model template class
    │   └── run_test.py             - Test runner script
    └── tests/                      - Unit tests
```

For more quick step by step, see `swift_testing/QUICKSTART.md`.
