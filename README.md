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

# SWIFT Testing Framework Quick Start

This guide provides the simplest way to get started with the SWIFT Testing Framework.

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

### 4. Verify Configuration

The default configuration in `config/config.yaml` is already set up to work with the Docker database. However, you should check it to make sure paths are correct for your environment.
Please also add your database password to this line:
      POSTGRES_PASSWORD: "YOUR_PASSWORD" 
in docker/docker-compose.yml

### 5. Start the PostgreSQL Database with Docker

The simplest way to set up the database is using the provided Docker container:

```bash
# Start PostgreSQL
docker-compose -f docker/docker-compose.yml up -d
```

This will:
- Start a PostgreSQL container
- Make it available on port 5433

### 6. Verify Configuration

The default configuration in `config/config.yaml` is already set up to work with the Docker database. However, you should check it to make sure paths are correct for your environment. You can copy config.yaml.example file and put there your confuguration for database and save it as config.yaml
Please also add your database password to this line:
      POSTGRES_PASSWORD: "YOUR_PASSWORD" 
in docker/docker-compose.yml

### 7. Initialize the Database

```bash
# Set up database tables
python3 swift_testing/src/database/setup_db.py --config config/config.yaml
```

### 8. Populate Templates and Variator Data

```bash
# Load templates
python3 swift_testing/populate_templates.py --config config/config.yaml

# Load variator data
python3 swift_testing/populate_variator_data.py --config config/config.yaml
```

### 9. Generate Test Messages

```bash
# Generate SWIFT messages using templates
python3 generate_swift_messages.py --config config/config.yaml --count 10 --type MT103
```

### 10. Run Tests and Route Messages

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
4.  If you see an error like this:
```
Error response from daemon: Ports are not available: exposing port TCP 0.0.0.0:5433 -> 127.0.0.1:0: listen tcp 0.0.0.0:5433: bind: address already in use
```
This means port 5433 is already in use by another process. To fix this either change the port in the docker-compose.yml file change to use a different port or find and stop the process using port 5433

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