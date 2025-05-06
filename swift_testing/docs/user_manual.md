# SWIFT Message Testing Framework - User Manual

## Table of Contents

1. [Introduction](#introduction)
2. [Project Overview](#project-overview)
3. [Features](#features)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Workflow Overview](#workflow-overview)
7. [Database Setup](#database-setup)
8. [Template Management](#template-management)
9. [Variator Data](#variator-data)
10. [Message Generation](#message-generation)
11. [Running Tests](#running-tests)
12. [Routing Messages](#routing-messages)
13. [Troubleshooting](#troubleshooting)

## Introduction

The SWIFT Message Testing Framework is a tool for testing and evaluating machine learning models used for routing SWIFT financial messages. This framework allows you to:

- Generate realistic SWIFT messages based on templates
- Store messages and test results in a database
- Train and evaluate message routing models
- Apply trained models to route new messages

The framework uses a combination of template-based generation with random variations to create realistic test data. It supports multiple routing model types and provides detailed evaluation metrics.

## Project Overview

SWIFT messages (like MT103, MT202, etc.) follow strict formats. This framework provides an easy way to produce realistic SWIFT message variations and store them for analysis or use in testing. The main goals of the project are:
* Automated Message Generation: Create many SWIFT messages based on a few example templates, introducing controlled randomness to simulate real-world variations.
* Database Storage: Store both the original templates and the generated messages in a database for easy retrieval and analysis.
* Testing Support: Enable users to use these messages to test routing algorithms or machine learning models in a banking context (for example, verifying that a ML model correctly classifies or routes each message).

## Features
* Database Setup: Automatically create the necessary database tables to store SWIFT message templates, generated messages, and related parameters.
* Template Management: Import and store SWIFT message templates (sample message formats) in the database. The project includes some common SWIFT message templates (e.g., MT103, MT202, MT950) and allows adding your own.
* Message Generation: Generate a specified number of new SWIFT messages from the stored templates. You can control how much random variation is applied, so the generated messages are similar to the template but not identical (simulating real messages with different values).
* Variator Data: Manage supporting data used for introducing variability (for example, lists of names, account numbers, or other fields that can change in the messages). This data can be loaded into the database to enrich the random generation process.
* Message Inspection: Check the database to see what templates and messages have been stored. The framework provides commands to list or view stored templates and generated messages, helping you verify the content.
* Extensible for Routing Tests: (Advanced) The framework is built with testing in mind. It includes placeholders for integrating a routing model or evaluation metrics. This means you could, for instance, plug in a machine learning model and use the generated messages to evaluate the model's routing accuracy. (This feature may require additional setup of model parameters in the config file.)

> **Note:** You do not need to be familiar with the internal code to use these features. They are accessible via simple command-line tools after installation.

## Installation

### Prerequisites

- Python 3.8 or later
- PostgreSQL database (or SQLite for quick testing)

### Installation Steps

1. **Clone or Download the Repository:**  
   Clone this repository via Git or download the ZIP and extract it. For example:

   ```bash
   git clone https://github.com/simonastrecanska/bachelor_thesis.git
   cd bachelor_thesis
   ```

2. **Create and activate a virtual environment (Optional but Recommended):**
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use venv\Scripts\activate
   ```

3. **Install the Python Package and Dependencies:**  
   It's recommended to install the framework as a Python package, which will also install all required dependencies. Run:

   ```bash
   pip install -e .
   ```

   This uses the setup.py in the project to install required libraries (like SQLAlchemy for database interaction, etc.) and sets up command-line tools.  
   Alternatively: You can install dependencies directly without packaging by running:

   ```bash
   pip install -r swift_testing/requirements.txt
   ```

## Configuration

The framework uses a YAML configuration file to specify settings. The default is located at `swift_testing/config/config.yaml`.

### Required Configuration Sections

```yaml
# Database configuration
database:
  connection_string: "postgresql://username:password@localhost:5432/dbname?sslmode=require"
  # OR individual parameters:
  # host: localhost
  # port: 5432
  # dbname: swift_testing
  # username: your_username
  # password: your_password
  # sslmode: require

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

For SQLite users, you can use a simpler connection string:
```yaml
connection_string: "sqlite:///swift_messages.db"
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

## How to Run the Project (Usage)

### 1. Set Up the Database

Before generating or storing any messages, initialize your database with the required tables.

* **What this does:** Creates tables (such as `message_templates`, `messages`, `parameters`, `variator_data`) in the configured database. If those tables already exist, this step will leave them as-is, unless you force a reset.
* **How to do it:**  
  Run the database setup script. You can do this in two ways:
  * Using Python script:

    ```bash
    python swift_testing/src/database/setup_db.py --config swift_testing/config/config.yaml
    ```

  * Using console command (after package install):

    ```bash
    swift-setup-db --config swift_testing/config/config.yaml
    ```

  Both methods achieve the same result. Using the console command is slightly shorter if the package is installed.  
  By default, this will create the tables if they do not exist. If you want to reset the database (i.e., drop existing tables and recreate them from scratch), you can add the `--drop-existing` flag:

  ```bash
  python swift_testing/src/database/setup_db.py --config swift_testing/config/config.yaml --drop-existing
  ```

  (Use the drop option with caution, as it will erase any existing data in those tables.)

### 2. Add Message Templates (Optional but Recommended)

Templates are the foundation for generating messages. The framework comes with some default SWIFT message templates (stored in `swift_testing/templates/`). You can load these into the database, and you can also add your own templates if needed.

* **What this does:** Reads SWIFT message template files and stores them in the `message_templates` table of the database. Each template is essentially a prototype message with placeholders or generalized content.
* **How to add templates:**  
  Run the template population script:

  ```bash
  python swift_testing/populate_templates.py --config swift_testing/config/config.yaml
  ```

  (Or use the console command `swift-populate-templates --config swift_testing/config/config.yaml`.)  
  This will load the default templates provided by the project. If you have additional custom templates, you can place them in a directory and use an extra option to load them. For example:

  ```bash
  python swift_testing/populate_templates.py --config swift_testing/config/config.yaml --templates-dir /path/to/your/templates
  ```

  Make sure your custom templates are in a similar format as the default ones (SWIFT message text format). By default, if you run the script without specifying `--templates-dir`, it uses the internal `swift_testing/templates` directory.

### 3. Add Variator Data (Optional)

Variator data is used to introduce randomness into the templates when generating messages. It might include lists of example names, account numbers, transaction amounts, dates, etc., which the generator can randomly pick from to replace placeholders in templates.

* **What this does:** Populates the `variator_data` table in the database with sample data used for variations. For instance, it might store a list of currencies, names, or other field values.
* **How to add variator data:**  
  Run the variator data population script:

  ```bash
  python swift_testing/populate_variator_data.py --config swift_testing/config/config.yaml
  ```

  (Or use the console command `swift-populate-variator-data --config swift_testing/config/config.yaml`.)  
  This will insert the default variation data that comes with the project (if any is provided as part of the framework). If you want to clear out existing variation data and start fresh (for example, if you run this twice and want to avoid duplications), you can use the `--clear` flag:

  ```bash
  python swift_testing/populate_variator_data.py --config swift_testing/config/config.yaml --clear
  ```

  This will remove all existing entries in the `variator_data` table before inserting new data.

> **Note:** Steps 2 and 3 are optional because the framework might come with some default templates and data pre-defined (especially if `add_sample_data` is enabled in the config). However, running them ensures your database is populated with the latest templates and variation data. If you skip them, ensure that your database has the necessary content to generate messages (otherwise, message generation might create empty or trivial messages).

### 4. Generate SWIFT Messages

Now the real action – generating messages! Using the templates and variator data stored in the database, you can create any number of SWIFT messages.

* **What this does:** Takes a random or specified template from the database, applies random variations (like changing amounts, dates, names, etc.), and generates new message text. Each generated message is then stored in the `messages` table of the database (and linked to the template it was based on). You can control how many messages to generate and how much randomness to apply.
* **How to generate messages:**  
  Run the message generation script with your desired options. For example:

  ```bash
  python generate_swift_messages.py --config swift_testing/config/config.yaml --count 10 --type MT103 --randomness 0.8
  ```

  (Or use the console command `swift-generate-messages --config swift_testing/config/config.yaml --count 10 --type MT103 --randomness 0.8`.)  
  In the above example:
  * `--count 10` means "generate 10 messages". You can specify any number here.
  * `--type MT103` tells the generator to use the template of type MT103. (If not specified, the framework might choose templates at random or use a default type. It's good to specify which message type you want to generate. Common types included are MT103, MT202, MT950, etc., corresponding to the loaded templates.)
  * `--randomness 0.8` sets the variability factor. This is a value between 0.0 and 1.0 that determines how much random variation to introduce. 0.0 would mean no variation (messages come out almost identical to the template), and 1.0 means high variation (as much change as allowed, replacing most fields with random data). The default if not given is typically moderate (around 0.5 to 1.0). Adjust this based on how diverse you want the test messages to be.

  After running this command, the specified number of new messages will be created and saved in the database. The script will likely output a confirmation, for example indicating that messages were successfully generated.

### 5. Check or View the Stored Messages

After generation, you may want to verify that messages were created or inspect them.

* **What this does:** Retrieves information from the database and displays it so you can confirm the contents. There are a couple of ways to do this:
  * Check database contents: Using the `check_database` utility, you can get a summary of what's in the database (how many templates, how many messages, etc., and possibly sample entries).
  * View messages: Using the `view_messages` tool (if available), you can fetch and display the actual text of generated messages.
* **How to check the database:**  
  Run:

  ```bash
  python swift_testing/check_database.py --config swift_testing/config/config.yaml
  ```

  (Or use the console command `swift-check-db --config swift_testing/config/config.yaml`.)  
  This will print out a summary of the database contents. For example, it may show how many templates are stored, how many messages have been generated, and possibly list a few entries or their IDs. This is useful to ensure that previous steps worked as expected.

* **How to view messages (optional):**  
  There is a script `view_messages.py` included in the project which can retrieve and show the actual message texts from the database. If you installed the package, you might have a command-line tool `swift-view-messages`. You can use it to fetch messages by type or other criteria. For instance:

  ```bash
  swift-view-messages --config swift_testing/config/config.yaml --type MT103
  ```

  This might display the generated MT103 messages on the console. You can also specify other options (such as limiting how many to view). If you prefer, you can directly query the database using SQL or a database client to see all data in the `messages` table. Each generated message record will typically include the message text and reference to the template used.

Following these steps, you will have a database full of SWIFT messages that you can use for testing and development. The framework's commands can be re-run as needed; for example, you can generate more messages at any time by rerunning the generation step (just ensure you have templates loaded).

## Input and Output Expectations

### Input requirements: 
At minimum, the framework needs some SWIFT message templates and a working database connection to function. By default, the project provides sample input in the form of template files and variation data:

* **Templates:** Located in `swift_testing/templates/`, these are text files representing standard SWIFT message formats (for example, an MT103 payment instruction format). These serve as input for the generation process. You can add more templates or edit these to suit your needs.
* **Variator Data:** Defined within the code (and possibly in data files or the config), this includes lists of values that can fill in template placeholders. For example, a list of random names, country codes, currency codes, etc. The default variator data is provided to simulate realistic field values.
* **User Input via Commands:** When running the tools, you provide input parameters like the number of messages to generate (`--count`), the type of message (`--type`), and randomness level (`--randomness`). These parameters influence how the generation uses the input data.

### Output results: 
The primary output of the framework is the generated SWIFT messages stored in the database. Here's what to expect after running the generation:

* New records in the `messages` table of your database, each containing the text of a generated SWIFT message (and possibly metadata like an ID, timestamp, or link to the template used).
* The console will show messages or summaries indicating progress (e.g., confirmation that messages were generated, or output of the `swift-check-db` command summarizing counts).
* If you enabled logging (by configuring the `logging` section in the config file), a log file (e.g., `swift_testing.log`) will record actions taken, which can be useful for debugging or audit trails.
* If you use the evaluation or test running features (for advanced users who integrate a model), the output could include evaluation metrics (accuracy, precision, etc.) printed to console or saved to files (CSV/JSON) as configured. By default, if you only stick to generation and storage, you won't need to deal with these.

### How to retrieve and use the output: 
Once messages are generated and in the database, you can:

* Use the provided viewing tools (`swift-check-db` or `swift-view-messages`) to fetch and display them.
* Connect to the database with any SQL client and query the `messages` table to export or inspect the messages.
* Feed these messages into other systems or programs for further testing (for example, run them through a parser, or use them as test cases for a message-routing algorithm).
* The framework ensures that each generated message conforms to the general structure of the chosen SWIFT message type, making them suitable as test input for downstream processes.

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
