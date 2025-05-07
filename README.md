# 🚀 SWIFT Message Testing Framework

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/Docker-Required-blue.svg)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14-blue.svg)](https://www.postgresql.org/)

A powerful framework for testing SWIFT message generation, routing, and processing in financial systems.

## 📋 Table of Contents

- [Features](#-features)
- [Prerequisites](#-prerequisites)
- [Initial Setup](#-initial-setup)
- [Quick Setup](#-quick-setup)
- [Manual Setup](#-manual-setup)
- [Working with the Framework](#-working-with-the-framework)
- [Troubleshooting](#-troubleshooting)
- [Creating Custom Models](#-creating-custom-models)
- [Project Structure](#-project-structure)

## ✨ Features

- 📄 Generate realistic SWIFT MT messages based on templates
- 🧠 Test message routing logic with ML models
- ✓ Validate message formatting against standards
- 🗄️ Docker-based PostgreSQL database for storing templates and test data
- 🔌 Customizable model interface for implementing your own processing logic
- 📊 Analysis tools to evaluate model performance

## 💻 Prerequisites

- **Python 3.8+** installed
- **Docker** installed (for easy database setup)
- **Git** (to clone the repository)

## 🔰 Initial Setup

Before using either the quick or manual setup method, complete these initial steps:

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

### 4. Configure Database Password

The default configuration in `config/config.yaml` is already set up to work with the Docker database. However, you need to set the database password before proceeding:

> ⚠️ **Important**: Update the database password in `docker/docker-compose.yaml`:
> ```yaml
> POSTGRES_PASSWORD: "your_secure_password"  # Use a strong, secure password here
> ```
> 
> Make sure to use the same password in `config/config.yaml` for the database connection.

## 🚀 Quick Setup

After completing the initial setup, the fastest way to set up the entire framework is to use the provided setup script:

```bash
# Make sure the script is executable
chmod +x setup.sh

# Run the setup script
./setup.sh
```

### What the setup script does:

- 🐳 Starts the PostgreSQL Docker container
- ⏱️ Waits for the database to be ready
- 📁 Creates all necessary directories for the project
- 🗄️ Sets up database tables
- 📝 Populates message templates
- 🔄 Loads variator data for message generation

After running this script, your environment will be fully configured and ready to use. You can then generate messages and run tests as described in the [Working with the Framework](#-working-with-the-framework) section.

## 🧩 Manual Setup

If you prefer to set up each component manually after the initial setup, follow these steps:

### 1. Configure the Database

The default configuration in `config/config.yaml` is already set up to work with the Docker database. Check the configuration and update paths as needed.

### 2. Start the PostgreSQL Database

```bash
# Start PostgreSQL
docker-compose -f docker/docker-compose.yml up -d
```

This will start a PostgreSQL container and make it available on port 5433.

### 3. Initialize the Database

```bash
# Set up database tables
python3 swift_testing/src/database/setup_db.py --config config/config.yaml
```

### 4. Populate Templates and Variator Data

```bash
# Load templates
python3 swift_testing/populate_templates.py --config config/config.yaml

# Load variator data
python3 swift_testing/populate_variator_data.py --config config/config.yaml
```

## 🔧 Working with the Framework

Once you've completed the setup (either using the script or manually), you can:

### Generate Test Messages

```bash
# Generate SWIFT messages using templates
python3 generate_swift_messages.py --config config/config.yaml --count 10 --type MT103

# Generate SWIFT messages using AI-based generation
python3 generate_swift_messages.py --config config/config.yaml --count 5 --type MT103 --ai
```

The framework supports two methods of message generation:
- **Template-based**: Uses predefined templates with variator data (default)
- **AI-based**: Uses artificial intelligence to create more diverse messages (use the `--ai` flag)

### Run Tests and Route Messages

```bash
# Test the routing model
python3 swift_testing/src/run_test.py --config config/config.yaml --name "Initial Test" --description "First test run" --messages 20

# Route a test message
python3 swift_testing/route_messages.py --config config/config.yaml --message "{1:F01BANKXXXXXYYY}{2:O1030919111026BANKZZZZ}{4::20:REF12345678:32A:091026EUR12500,00:50K:/123456789:ORDERING CUSTOMER:71A:SHA-}"
```

## ❓ Troubleshooting

### Database Connection Issues

1. Check if Docker is running
2. Verify the database connection in `config/config.yaml`
3. Try stopping and restarting the PostgreSQL container:
   ```bash
   docker-compose -f docker/docker-compose.yml down
   docker-compose -f docker/docker-compose.yml up -d
   ```

### Database Setup Failed During Installation

If the setup.sh script fails with database errors:

1. **Check container creation**: Sometimes Docker assigns different names to containers than expected
   ```bash
   # See what containers are actually running
   docker ps
   ```

2. **Check Docker logs for the PostgreSQL container**:
   ```bash
   # Replace with your actual container name/ID from docker ps
   docker logs swift_testing_postgres
   ```

3. **Database already exists error**: If you see errors about the database or tables already existing:
   ```bash
   # Force a complete reset of the database
   docker-compose -f docker/docker-compose.yml down -v  # Removes volumes!
   docker-compose -f docker/docker-compose.yml up -d
   ```

4. **Container starts but database isn't accessible**: Check that the PostgreSQL service is actually running:
   ```bash
   # Run this AFTER container is started
   docker exec swift_testing_postgres pg_isready -U postgres
   ```

5. **Fix incorrect database configuration**: Update your config/config.yaml file to match what's in docker-compose.yml:
   ```yaml
   database:
     host: "localhost"  # Use this on Mac/Windows, not host.docker.internal
     port: 5433  # Must match the external port in docker-compose.yml
     username: "postgres"  # Must match POSTGRES_USER
     password: "your_secure_password"  # Must match POSTGRES_PASSWORD
     dbname: "swift_testing"  # Must match POSTGRES_DB
   ```

### Port Conflict Issues

If you see an error like this:
```
Error response from daemon: Ports are not available: exposing port TCP 0.0.0.0:5433 -> 127.0.0.1:0: listen tcp 0.0.0.0:5433: bind: address already in use
```

This means port 5433 is already in use by another process. To fix this:

1. Either change the port in the docker-compose.yml file (change "5433:5432" to use a different port like "5434:5432")
2. Or find and stop the process using port 5433:
   ```bash
   # Find the process using port 5433
   lsof -i :5433
   
   # Kill the process using its PID
   kill <PID>
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

## 🔮 Creating Custom Models

To create a custom model for processing SWIFT messages:

1. Create a new Python module in the `models` directory that inherits from the `CustomModel` class in `swift_testing/models/custom_model.py`
2. Implement the required abstract methods
3. Update the configuration to use your custom model

See `swift_testing/models/custom_model.py` for a template implementation and examples.

### Model Structure

The repository already includes a complete model setup for your use:

1. **Model Interface**: `swift_testing/models/custom_model.py` - Template class showing how to implement a custom model
2. **Model Implementation**: Source code that defines message processing logic is in `swift_testing/src/models/`
3. **Pre-trained Model**: A working serialized model file (`model_v1.0.0.pkl`) is available in the root `models/` directory

The config.yaml references the pre-trained model with the path `models/model_v1.0.0.pkl`. This path is relative to the project root.

If you create your own model, you can either:
- Replace the existing model file at `models/model_v1.0.0.pkl`
- Create a new model file and update the path in the config.yaml file

## 📁 Project Structure

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

---

## 📚 Documentation

For more advanced usage and detailed documentation, refer to the files in the `swift_testing/docs` directory.