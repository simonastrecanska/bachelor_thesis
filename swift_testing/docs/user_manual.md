# SWIFT Message Testing Framework - User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Workflow Overview](#workflow-overview)
5. [Database Setup](#database-setup)
6. [Template Management](#template-management)
7. [Variator Data](#variator-data)
8. [Message Generation](#message-generation)
9. [Running Tests](#running-tests)
10. [Routing Messages](#routing-messages)
11. [Troubleshooting](#troubleshooting)

## Introduction

The SWIFT Message Testing Framework is a tool for testing and evaluating machine learning models used for routing SWIFT financial messages. This framework allows you to:

- Generate realistic SWIFT messages based on templates
- Store messages and test results in a database
- Train and evaluate message routing models
- Apply trained models to route new messages

The framework uses a combination of template-based generation with random variations to create realistic test data. It supports multiple routing model types and provides detailed evaluation metrics.

## Installation

### Prerequisites

- Python 3.8 or later
- PostgreSQL database

### Installation Steps

1. Clone the repository:
   ```
   git clone https://github.com/simonastrecanska/bachelor_thesis.git
   cd swift-testing
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r swift_testing/requirements.txt
   ```

4. Configure the database settings in the configuration file (see next section)

## Configuration

The framework uses a YAML configuration file to specify settings. The default is located at `config/config.yaml`.

### Required Configuration Sections

```yaml
# Database configuration
database:
  connection_string: "postgresql://username:password@localhost:5432/dbname?sslmode=require"

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
  model_params:
    n_estimators: 100
    max_depth: 10
    random_state: 42
  feature_extraction:
    vectorizer: "tfidf"
    max_features: 1000
    ngram_range: [1, 3]

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

## Workflow Overview

The testing framework workflow consists of these sequential steps:

1. Set up the database tables
2. Add message templates to the database
3. Add variator data for message generation
4. Generate test messages using templates and variator data
5. Run tests that evaluate the routing model
6. Use the trained model to route new messages

Each step is explained in detail in the following sections.

## Database Setup

The first step is to set up the database schema by creating the necessary tables.

```bash
# Create the database tables
python swift_testing/src/database/setup_db.py --config config/config.yaml

# If you need to recreate tables, add the --drop-existing flag
python swift_testing/src/database/setup_db.py --config config/config.yaml --drop-existing
```

This creates the following tables:
- `templates`: Stores SWIFT message templates
- `messages`: Stores generated message variations
- `parameters`: Stores test parameters
- `expected_results`: Stores expected routing labels
- `actual_results`: Stores model predictions
- `variator_data`: Stores data used for field variations

## Template Management

After setting up the database, you need to add SWIFT message templates. Templates are the base patterns used to generate test messages.

```bash
python swift_testing/populate_templates.py --config swift_testing/config/config.yaml
```

This script adds default templates for different SWIFT message types (e.g., Payment, Treasury). You can customize the templates in the `populate_templates.py` script.

## Variator Data

The template variator needs data to create realistic variations of templates. This includes currencies, bank names, reference numbers, etc.

```bash
python swift_testing/populate_variator_data.py --config swift_testing/config/config.yaml

python swift_testing/populate_variator_data.py --config swift_testing/config/config.yaml --clear
```

The `populate_variator_data.py` script contains the following categories of data:
- Currencies
- Bank prefixes and suffixes
- Payment types
- Reference prefixes
- Names (first and last)
- Street names and types
- Cities
- Company details
- Account numbers
- Payment details

## Message Generation

Now you can generate SWIFT messages using the templates and variator data:

```bash
# Generate messages using random variations
python generate_swift_messages.py --config swift_testing/config/config.yaml --count 10 --type MT103

# Generate messages using AI-assisted generation (if available)
python generate_swift_messages.py --config swift_testing/config/config.yaml --count 5 --type MT103 --ai --model llama3
```

Parameters:
- `--count`: Number of messages to generate
- `--type`: Template type to use (e.g., MT103, MT202)
- `--ai`: Use AI-based generation (optional)
- `--model`: AI model to use (default: llama3)
- `--temperature`: Creativity setting for AI generation (default: 0.7)

## Running Tests

Once you have templates, variator data, and messages, you can run a complete test that includes:
1. Message generation (if needed)
2. Model training (if requested)
3. Model evaluation

```bash
# Run a complete test
python python generate_swift_messages.py --config config/config.yaml --count 5 --type MT103 --ai --model llama3/src/run_test.py --config config/config.yaml --name "Initial Test" --description "Testing SWIFT message routing accuracy" --messages 100

# To train the model before testing
python swift_testing/src/run_test.py --config swift_testing/config/config.yaml --name "Training Test" --description "Train and test model" --messages 100 --train

# To save results to a JSON file
python swift_testing/src/run_test.py --config config/config.yaml --name "Saved Results Test" --description "Save test results" --messages 100 --output results.json
```

Parameters:
- `--name`: Test name
- `--description`: Test description
- `--messages`: Number of messages to use
- `--train`: Whether to train the model before testing
- `--output`: File path to save results

## Routing Messages

After training a model, you can use it to route new SWIFT messages using the `route_messages.py` script:

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

# Save routing results to a file
python swift_testing/route_messages.py --config config/config.yaml --batch --output results.json
```

Parameters:
- `--message`: Text of a message to route
- `--message-id`: ID of a message in the database
- `--batch`: Route multiple messages from the database
- `--batch-size`: Number of messages to process in batch mode
- `--model`: Path to a specific model file
- `--output`: File to save routing results

## Troubleshooting

### Database Connection Issues

If you encounter database connection issues:
1. Verify the database is running
2. Check the connection string in your config file
3. Ensure database user has proper permissions

### Missing Configuration Elements

If you see errors about missing configuration:
1. Ensure all required sections are present in your config.yaml
2. Check that the paths in your configuration exist

### Training Errors

If model training fails:
1. Make sure you have enough messages in the database
2. Check that your message content is valid
3. Verify the model configuration in your config file

### Evaluation Errors

If evaluation produces errors:
1. Check that your messages have expected routing labels
2. Make sure your model produces valid predictions
3. Verify that prediction types match expected label types 

Happy testing!
