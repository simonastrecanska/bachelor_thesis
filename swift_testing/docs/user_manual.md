# 📘 SWIFT Message Testing Framework - User Manual

## 📋 Table of Contents

1. [Introduction](#introduction)
2. [Project Overview](#project-overview)
3. [Features](#features)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Framework Commands Reference](#framework-commands-reference)
7. [Setup Methods](#setup-methods)
   - [One-Command Setup](#one-command-setup)
   - [Manual Setup](#manual-setup)
8. [Working with the Framework](#working-with-the-framework)
   - [Message Generation](#message-generation)
   - [Running Tests](#running-tests)
   - [Routing Messages](#routing-messages)
9. [Analysis Tools](#analysis-tools)
   - [Jupyter Notebooks](#jupyter-notebooks)
10. [Troubleshooting](#troubleshooting)

## 🚀 Introduction

The SWIFT Message Testing Framework is a tool for testing and evaluating machine learning models used for routing SWIFT financial messages. This framework allows you to:

- Generate realistic SWIFT messages based on templates
- Store messages and test results in a database
- Train and evaluate message routing models
- Apply trained models to route new messages

The framework uses a combination of template-based generation with random variations to create realistic test data. It supports multiple routing model types and provides detailed evaluation metrics.

## 🔍 Project Overview

SWIFT messages (like MT103, MT202, etc.) follow strict formats. This framework provides an easy way to produce realistic SWIFT message variations and store them for analysis or use in testing. The main goals of the project are:

* **Automated Message Generation**: Create many SWIFT messages based on templates, introducing controlled randomness to simulate real-world variations
* **Database Storage**: Store both templates and generated messages in a database for easy retrieval and analysis
* **Testing Support**: Enable users to test routing algorithms or machine learning models in a banking context

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🗄️ **Database Setup** | Automatically create the necessary database tables to store templates, messages, and related data |
| 📝 **Template Management** | Import and store SWIFT message templates in the database (e.g., MT103, MT202, MT950) |
| 🔄 **Message Generation** | Generate realistic SWIFT messages with controlled random variations |
| 🧩 **Variator Data** | Manage supporting data used for introducing variability in messages |
| 🔎 **Message Inspection** | Utilities to examine stored templates and messages |
| 🧠 **Model Testing** | Evaluate model performance on routing SWIFT messages |
| 📊 **Analysis Tools** | Interactive notebooks for analyzing test results |

## 💻 Installation

### Prerequisites

- Python 3.8 or later
- Docker (for PostgreSQL database)
- Git (for cloning the repository)

### Installation Steps

1. **Clone the Repository**  
   ```bash
   git clone https://github.com/simonastrecanska/bachelor_thesis.git
   cd bachelor_thesis
   ```

2. **Create and Activate a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r swift_testing/requirements.txt
   ```

4. **Configure Database Password**  
   Before proceeding, update the database password in:
   - `docker/docker-compose.yml`: Set your chosen password in the `POSTGRES_PASSWORD` field
   - `config/config.yaml`: Set the same password in the database connection parameters

## ⚙️ Configuration

The framework uses a YAML configuration file to specify settings. The default is located at `config/config.yaml` in the project root.

<details>
<summary>📄 View Sample Configuration</summary>

```yaml
# Database Settings
database:
  # Docker PostgreSQL connection
  connection_string: "postgresql://postgres:your_secure_password@localhost:5433/swift_testing"
  
  # Optional: Override individual parameters
  host: "localhost"
  port: 5433
  username: "postgres"
  password: "your_secure_password"
  dbname: "swift_testing"
  
  # Database behavior settings
  add_sample_data: true

# Message generation settings
message_generation:
  num_messages: 100
  variation_strategy: "random"
  variator_config:
    perturbation_factor: 0.5
    field_variation_probability: 0.7

# Model configuration
model:
  version: "1.0.0"
  prediction_threshold: 0.5
  model_type: "random_forest"
  
# File paths
paths:
  output_dir: "output"
  model_dir: "models"

# Evaluation metrics
evaluation:
  metrics: ["accuracy", "precision", "recall", "f1"]
  confusion_matrix: true
  output_format: ["json", "csv"]
```
</details>

> 💡 **Alternative Database Options**: For SQLite users, you can use a simpler connection string:
> ```yaml
> connection_string: "sqlite:///swift_messages.db"
> ```

## 🔧 Framework Commands Reference

This section provides a reference for all the key commands used in the framework.

### 🐳 Docker Commands

```bash
# Start PostgreSQL container
docker-compose -f docker/docker-compose.yml up -d

# Stop PostgreSQL container
docker-compose -f docker/docker-compose.yml down

# Reset database (removes all data)
docker-compose -f docker/docker-compose.yml down -v
docker-compose -f docker/docker-compose.yml up -d
```

### 🗄️ Database Commands

```bash
# Setup database tables
python swift_testing/src/database/setup_db.py --config config/config.yaml

# Reset database tables (caution: deletes all data!)
python swift_testing/src/database/setup_db.py --config config/config.yaml --drop-existing

# Load templates
python swift_testing/populate_templates.py --config config/config.yaml

# Load variator data
python swift_testing/populate_variator_data.py --config config/config.yaml

# Clear and reload variator data
python swift_testing/populate_variator_data.py --config config/config.yaml --clear
```

### 📝 Message Generation Commands

```bash
# Generate messages using template-based approach
python generate_swift_messages.py --config config/config.yaml --count 10 --type MT103

# Generate messages using AI-based approach
python generate_swift_messages.py --config config/config.yaml --count 5 --type MT103 --ai --model llama3
```

### 🧪 Testing Commands

```bash
# Run a complete test
python swift_testing/src/run_test.py --config config/config.yaml --name "Test Name" --description "Description" --messages 100

# Train and test
python swift_testing/src/run_test.py --config config/config.yaml --name "Train Test" --train --messages 100
```

### 🔄 Routing Commands

```bash
# Route a single message (text)
python swift_testing/route_messages.py --config config/config.yaml --message "MESSAGE_TEXT" #you need to add real message to the MESSAGE_TEXT

# Route a message by ID
python swift_testing/route_messages.py --config config/config.yaml --message-id 123

# Route batch of messages
python swift_testing/route_messages.py --config config/config.yaml --batch --batch-size 50
```

## 🛠️ Setup Methods

There are two ways to set up the framework: using the one-command setup script or following the manual setup process.

### ⚡ One-Command Setup

The fastest way to set up the entire framework:

```bash
# Make script executable
chmod +x setup.sh

# Run setup script
./setup.sh
```

This script automates the entire process:
- ✅ Starts the PostgreSQL Docker container
- ✅ Creates necessary directories
- ✅ Sets up database tables
- ✅ Populates templates and variator data

After running this script, your environment will be fully configured and ready to use.

### 🧩 Manual Setup

If you prefer a step-by-step approach:

1. **Start PostgreSQL Container**
   ```bash
   docker-compose -f docker/docker-compose.yml up -d
   ```

2. **Setup Database Tables**
   ```bash
   python swift_testing/src/database/setup_db.py --config config/config.yaml
   ```

3. **Add Message Templates**
   ```bash
   python swift_testing/populate_templates.py --config config/config.yaml
   ```

4. **Add Variator Data**
   ```bash
   python swift_testing/populate_variator_data.py --config config/config.yaml
   ```

> ℹ️ **Note**: Steps 3 and 4 are optional if `add_sample_data` is enabled in the config, but running them ensures your database has the latest data.

## 📊 Working with the Framework

After setup, you can start using the framework's primary functions.

### 🔄 Message Generation

Generate SWIFT messages using the templates and variator data:

```bash
# Template-based generation
python generate_swift_messages.py --config config/config.yaml --count 10 --type MT103

# AI-assisted generation
python generate_swift_messages.py --config config/config.yaml --count 5 --type MT103 --ai --model llama3
```

#### Parameters:

| Parameter | Description | Example |
|-----------|-------------|---------|
| `--count` | Number of messages to generate | `--count 10` |
| `--type` | Template type to use | `--type MT103` |
| `--ai` | Use AI-based generation | `--ai` |
| `--model` | AI model to use | `--model llama3` |
| `--temperature` | Creativity setting (0.0-1.0) | `--temperature 0.7` |

### 🧪 Running Tests

Execute complete tests that include message generation, model training, and evaluation:

```bash
# Basic test
python swift_testing/src/run_test.py --config config/config.yaml --name "Initial Test" --messages 100

# Test with model training
python swift_testing/src/run_test.py --config config/config.yaml --name "Training Test" --train --messages 100

# Save results to file
python swift_testing/src/run_test.py --config config/config.yaml --name "Results Test" --output results.json
```

### 🧠 Routing Messages

Route SWIFT messages using a trained model:

<details>
<summary>View Routing Examples</summary>

```bash
# Route a single message from text
python swift_testing/route_messages.py --config config/config.yaml --message "{1:F01BANKDEFMAXXX0000000000}{2:I103BANKABCMXXXXN}{4:
:20:REFERENCE123
:23B:CRED
:32A:210615USD1000,00
:50K:ORDERING CUSTOMER
:59:BENEFICIARY CUSTOMER
:70:PAYMENT FOR SERVICES
-}"

# Route a message from the database by ID
python swift_testing/route_messages.py --config config/config.yaml --message-id 123

# Route a batch of messages from the database
python swift_testing/route_messages.py --config config/config.yaml --batch --batch-size 50

# Use a specific saved model
python swift_testing/route_messages.py --config config/config.yaml --batch --model path/to/model.pkl
```
</details>

## 📈 Analysis Tools

The framework provides tools to analyze test results and evaluate model performance.

### 📊 Jupyter Notebooks

A set of interactive notebooks for data analysis and visualization:

1. **01_Database_Connection_Setup.ipynb**: Sets up database connection
2. **02_Basic_Analytics.ipynb**: Basic statistics and distributions
3. **03_Advanced_Analysis.ipynb**: In-depth pattern analysis
4. **04_Interactive_Dashboard.ipynb**: Interactive data exploration
5. **05_Reporting_and_Automated_Reports.ipynb**: Automated report generation

To use the notebooks:

```bash
# Launch Jupyter
jupyter lab

# Navigate to: swift_testing/src/notebooks/
```

#### Notebook Connection Settings

When working with notebooks:
1. Use `localhost` for the database host
2. Use port `5433` (or your configured port)
3. Use the same credentials as in your config.yaml

## ❓ Troubleshooting

### 🗄️ Database Connection Issues

<details>
<summary>View Database Troubleshooting</summary>

1. **Check if Docker is running**
   ```bash
   docker ps
   ```

2. **Verify database connection parameters**
   - Host: `localhost` (not host.docker.internal)
   - Port: 5433 (not the default 5432)
   - Username: matches POSTGRES_USER in docker-compose.yml
   - Password: matches POSTGRES_PASSWORD in docker-compose.yml

3. **Restart the container**
   ```bash
   docker-compose -f docker/docker-compose.yml down
   docker-compose -f docker/docker-compose.yml up -d
   ```

4. **Check container logs**
   ```bash
   docker logs swift_testing_postgres
   ```

5. **Test database connection**
   ```bash
   docker exec swift_testing_postgres pg_isready -U postgres
   ```
</details>

### 🔌 Port Conflict Issues

If you see "address already in use" error:

1. **Change the port** in docker-compose.yml (e.g., from "5433:5432" to "5434:5432")

2. **Find and stop the process using the port**
   ```bash
   lsof -i :5433
   kill <PID>
   ```

### 🐳 Docker Issues

<details>
<summary>View Docker Troubleshooting</summary>

1. **Ensure Docker is installed and running**
2. **Check container logs**
   ```bash
   docker logs swift_testing_postgres
   ```
3. **Check for port conflicts**
   ```bash
   lsof -i :5433
   ```
4. **Reset everything**
   ```bash
   docker-compose -f docker/docker-compose.yml down -v
   docker-compose -f docker/docker-compose.yml up -d
   ```
</details>

### 📝 General Troubleshooting Tips

- Always run commands from the project root directory
- Ensure config.yaml is properly configured
- Check that all required directories exist
- Verify that the database container is running before using other commands

---

Happy testing! 🎉
