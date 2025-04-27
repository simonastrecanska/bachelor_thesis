# SWIFT Message Testing Framework

SWIFT Message Testing Framework is a tool for generating and managing sample SWIFT messages for testing purposes. 
It is designed to help banks and developers simulate SWIFT payment messages and automate the testing of systems (including machine learning models) that route or process these messages. With this framework, you can create a database of SWIFT message templates, generate large volumes of varied test messages from those templates, and inspect the results – all through simple command-line steps.

## Project Overview

SWIFT messages (like MT103, MT202, etc.) follow strict formats. This framework provides an easy way to produce realistic SWIFT message variations and store them for analysis or use in testing. The main goals of the project are:
* Automated Message Generation: Create many SWIFT messages based on a few example templates, introducing controlled randomness to simulate real-world variations.
* Database Storage: Store both the original templates and the generated messages in a database for easy retrieval and analysis.
* Testing Support: Enable users to use these messages to test routing algorithms or machine learning models in a banking context (for example, verifying that a ML model correctly classifies or routes each message).

By using this framework, a user can quickly populate a database with test data and run experiments or validations without manually writing out numerous SWIFT messages.

## Features
* Database Setup: Automatically create the necessary database tables to store SWIFT message templates, generated messages, and related parameters.
* Template Management: Import and store SWIFT message templates (sample message formats) in the database. The project includes some common SWIFT message templates (e.g., MT103, MT202, MT950) and allows adding your own.
* Message Generation: Generate a specified number of new SWIFT messages from the stored templates. You can control how much random variation is applied, so the generated messages are similar to the template but not identical (simulating real messages with different values).
* Variator Data: Manage supporting data used for introducing variability (for example, lists of names, account numbers, or other fields that can change in the messages). This data can be loaded into the database to enrich the random generation process.
* Message Inspection: Check the database to see what templates and messages have been stored. The framework provides commands to list or view stored templates and generated messages, helping you verify the content.
* Extensible for Routing Tests: (Advanced) The framework is built with testing in mind. It includes placeholders for integrating a routing model or evaluation metrics. This means you could, for instance, plug in a machine learning model and use the generated messages to evaluate the model's routing accuracy. (This feature may require additional setup of model parameters in the config file.)

> **Note:** You do not need to be familiar with the internal code to use these features. They are accessible via simple command-line tools after installation.

## Installation

Before you begin, ensure you have the following requirements:
* Python 3.8 or later – The framework is written in Python and requires version 3.8+.
* Database – A PostgreSQL database is expected by default (you can use another SQL database if you adjust the configuration). You should have access to a database server and credentials (hostname, database name, username, password). If you don't have PostgreSQL, you may use SQLite for a quick start by modifying the configuration, though PostgreSQL is recommended for full functionality.
* Operating System – The project is OS-independent. You can run it on Windows, macOS, or Linux as long as the above requirements are met.

### Step-by-Step Setup
1. **Clone or Download the Repository:**  
   Clone this repository via Git or download the ZIP and extract it. For example:

   ```bash
   git clone https://github.com/simonastrecanska/bachelor_thesis.git
   cd bachelor_thesis
   ```

2. **Install the Python Package and Dependencies:**  
   It's recommended to install the framework as a Python package, which will also install all required dependencies. Run:

   ```bash
   pip install -e .
   ```

   This uses the setup.py in the project to install required libraries (like SQLAlchemy for database interaction, etc.) and sets up command-line tools.  
   Alternatively: You can install dependencies directly without packaging by running:

   ```bash
   pip install -r swift_testing/requirements.txt
   ```

3. **Configure Database Settings:**  
   Locate the configuration file at `swift_testing/config/config.yaml`. Open this file in a text editor and update the database connection settings under the `database:` section. You will need to provide:
   * `host`: the hostname of your database server (e.g., localhost for local DB).
   * `port`: the database port (5432 is default for PostgreSQL).
   * `dbname`: the name of the database you will use for these tests (you may need to create an empty database first using your DB administration tools).
   * `username` and `password`: database credentials with permission to create tables and insert data.
   * If using PostgreSQL, ensure `sslmode` and other settings as needed (you can set `sslmode` to `disable` for local testing if SSL is not configured).
   * Optional: Instead of individual parameters, you can provide a full `connection_string`. By default, an example PostgreSQL connection string is given. Adjust it to match your database. For example:

     ```yaml
     connection_string: "postgresql://user:password@localhost:5432/mydatabase"
     ```

   * If you prefer to use SQLite (for simplicity or testing purposes), you can change the connection_string to use SQLite, for example:

     ```yaml
     connection_string: "sqlite:///swift_messages.db"
     ```
     (In this case, ensure `add_sample_data` is set to `true` so that some initial data can be inserted.)
   
   Save the `config.yaml` after making these changes.

4. **(Optional) Adjust Other Settings:**  
   The `config.yaml` also contains other sections (for example, `paths`, `model`, `logging`, `evaluation`, `message_generation`). For a general user focusing on message generation, you typically do not need to modify these. However, you might want to ensure `message_generation` settings are to your liking (such as default number of messages, variation strategy, etc.). The default settings will work for most cases, and you can also override options via command-line arguments when running commands.

With the installation complete and the configuration set up, you are ready to use the framework.

## How to Run the Project (Usage)

After installation, the framework provides easy command-line tools to perform various tasks. You can call these either by using the provided Python scripts or via convenient command aliases (if you installed the package). Below are common usage scenarios and the steps to execute them.

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


Happy testing!