# SWIFT Message Testing Framework

This project provides a framework for generating, storing, and testing SWIFT messages. It helps automate the testing of machine learning models used for routing SWIFT messages in banking systems.

## Overview

The framework allows you to:
1. Set up a database with sample SWIFT message templates
2. Generate variations of these templates with configurable randomness 
3. Store the generated messages in a database

## Installation

1. Clone this repository
2. Install Python 3.8 or later
3. Install the package:
   ```
   pip install -e .
   ```
   
   Or install dependencies directly:
   ```
   pip install -r swift_testing/requirements.txt
   ```
4. Configure your database settings in `swift_testing/config/config.yaml`

## Quick Start

To get started quickly with a complete setup:

```bash
# 1. Set up the database
python swift_testing/src/database/setup_db.py --config swift_testing/config/config.yaml

# 2. Add templates (optional)
python swift_testing/populate_templates.py --config swift_testing/config/config.yaml

# 3. Add variator data for message generation (optional)
python swift_testing/populate_variator_data.py --config swift_testing/config/config.yaml

# 4. Generate some messages
python generate_swift_messages.py --config swift_testing/config/config.yaml --count 5 --randomness 0.8

```

## Usage

### Setting Up the Database

To create the necessary database tables:

```bash
# Create tables
python swift_testing/src/database/setup_db.py --config swift_testing/config/config.yaml

# To force drop and recreate tables
python swift_testing/src/database/setup_db.py --config swift_testing/config/config.yaml --drop-existing
```

### Adding Templates and Variator Data

To add message templates to the database:

```bash
# Add default templates
python swift_testing/populate_templates.py --config swift_testing/config/config.yaml

# To provide additional templates from a directory
python swift_testing/populate_templates.py --config swift_testing/config/config.yaml --templates-dir /path/to/templates
```

To populate variator data for message generation:

```bash
# Add variator data
python swift_testing/populate_variator_data.py --config swift_testing/config/config.yaml

# To clear existing data before inserting new data
python swift_testing/populate_variator_data.py --config swift_testing/config/config.yaml --clear
```

### Checking the Database

To check what templates and messages are in your database:

```bash
python swift_testing/check_database.py --config swift_testing/config/config.yaml
```

### Generating Messages

To generate SWIFT messages from templates:

```bash
python generate_swift_messages.py --config swift_testing/config/config.yaml --count 10 --type MT103 --randomness 0.8
```

Parameters:
- `--count`: Number of messages to generate
- `--type`: The template type to use (e.g., MT103, MT202, MT950)
- `--randomness`: A float (0.0-1.0) that controls the amount of variation

## Database Structure

The framework uses the following tables:

1. `message_templates` - Stores SWIFT message templates
2. `parameters` - Stores test parameters
3. `messages` - Stores generated messages
4. `variator_data` - Stores data for template variations

## Configuration

The main configuration file is `swift_testing/config/config.yaml`. It contains settings for:
- Database connection
- Message generation parameters
- Evaluation metrics

## Project Structure

```
.
├── generate_swift_messages.py   - Script to generate messages
├── view_messages.py            - Script to view messages
├── swift_testing/
│   ├── check_database.py       - Script to check database contents
│   ├── populate_templates.py   - Script to populate templates
│   ├── populate_variator_data.py - Script to populate variator data
│   ├── config/
│   │   └── config.yaml         - Configuration file
│   ├── src/
│   │   ├── database/           - Database modules
│   │   │   ├── db_manager.py   - Database management functions
│   │   │   ├── models.py       - SQLAlchemy models
│   │   │   └── setup_db.py     - Database setup script
│   │   ├── message_generator/  - Message generation modules
│   │   │   ├── template_variator.py - Template variation engine
│   │   │   ├── generator.py    - Message generation logic
│   │   │   └── field_handlers.py - Field-specific handlers
│   │   ├── evaluation/         - Evaluation modules
│   │   ├── interface/          - Command-line interface
│   │   └── models/             - Machine learning models
│   ├── templates/              - Template files
│   └── tests/                  - Unit tests
└── README.md                   - This file
```

## Console Scripts

After installation, the following commands will be available:

```
swift-testing            - Main CLI interface for testing framework
swift-check-db           - Check database contents
swift-generate-messages  - Generate SWIFT messages
swift-populate-templates - Populate message templates
swift-populate-variator-data - Populate variator data
```

## License

MIT License 
