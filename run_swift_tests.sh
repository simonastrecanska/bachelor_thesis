#!/bin/bash
#
# Swift Testing Framework Execution Script
# 
# This script runs all the necessary steps to set up and run 
# the Swift Testing Framework as described in the README.

set -e  # Exit on error

# Configuration
CONFIG_PATH="swift_testing/config/config.yaml"
TEST_NAME="Initial Test"
TEST_DESC="Testing SWIFT message routing accuracy"
MSG_COUNT=100
BATCH_SIZE=1000  # Number of messages to route in each batch

print_header() {
    echo "=============================================="
    echo "  $1"
    echo "=============================================="
}

# Step 1: Set up the database
print_header "Step 1: Setting up the database"
python swift_testing/src/database/setup_db.py --config $CONFIG_PATH --drop-existing

# Step 2: Add templates
print_header "Step 2: Adding templates"
python swift_testing/populate_templates.py --config $CONFIG_PATH

# Step 3: Add variator data for message generation
print_header "Step 3: Adding variator data"
python swift_testing/populate_variator_data.py --config $CONFIG_PATH

# Step 4: Generate some messages
print_header "Step 4: Generating SWIFT messages"
python generate_swift_messages.py --config $CONFIG_PATH --count $MSG_COUNT

# Step 5: Route the generated messages
print_header "Step 5: Routing the generated messages"
python swift_testing/route_messages.py --config $CONFIG_PATH --batch --batch-size $BATCH_SIZE --output routing_results.json

# Step 6: Run a complete test
print_header "Step 6: Running complete test"
python swift_testing/src/run_test.py --config $CONFIG_PATH --name "$TEST_NAME" --description "$TEST_DESC" --train --messages $MSG_COUNT

print_header "Testing complete!"
