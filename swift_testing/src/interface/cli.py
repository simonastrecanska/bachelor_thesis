#!/usr/bin/env python3
"""
Command-Line Interface

This module provides a command-line interface for the SWIFT message routing testing framework.
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.config_loader import load_config
from src.testing_framework import create_testing_framework

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def setup_arg_parser() -> argparse.ArgumentParser:
    """
    Set up command-line argument parser.
    
    Returns:
        Argument parser instance
    """
    parser = argparse.ArgumentParser(
        description="SWIFT Message Routing Testing Framework",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--config", 
        required=True,
        help="Path to YAML configuration file"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    run_parser = subparsers.add_parser(
        "run", help="Run a complete test"
    )
    run_parser.add_argument(
        "--name", 
        required=True,
        help="Name of the test"
    )
    run_parser.add_argument(
        "--description", 
        default="Test run via CLI",
        help="Description of the test"
    )
    run_parser.add_argument(
        "--num-messages", 
        type=int,
        help="Number of messages to generate (default from config)"
    )
    run_parser.add_argument(
        "--train", 
        action="store_true",
        help="Train the model before testing"
    )

    evaluate_parser = subparsers.add_parser(
        "evaluate", help="Evaluate existing test results"
    )
    evaluate_parser.add_argument(
        "--param-id", 
        type=int,
        required=True,
        help="Parameter ID to evaluate"
    )
    
    generate_parser = subparsers.add_parser(
        "generate", help="Generate test messages"
    )
    generate_parser.add_argument(
        "--name", 
        required=True,
        help="Name of the test"
    )
    generate_parser.add_argument(
        "--description", 
        default="Test data generation via CLI",
        help="Description of the test"
    )
    generate_parser.add_argument(
        "--num-messages", 
        type=int,
        help="Number of messages to generate (default from config)"
    )
    
    list_parser = subparsers.add_parser(
        "list", help="List test parameters"
    )
    list_parser.add_argument(
        "--param-id", 
        type=int,
        help="Parameter ID to show details (if not specified, lists all)"
    )
    
    return parser


def handle_run_command(args, framework):
    """
    Handle 'run' command.
    
    Args:
        args: Command-line arguments
        framework: Testing framework instance
    """
    try:
        results = framework.run_complete_test(
            args.name,
            args.description,
            args.num_messages,
            args.train
        )
        
        print("\n=== Test Results ===")
        print(f"Parameter ID: {results['parameter']['param_id']}")
        print(f"Test name: {results['parameter']['test_name']}")
        print(f"Messages tested: {results['num_messages']}")
        print(f"Execution time: {results['execution_time']:.2f} seconds")
        
        metrics = results['evaluation']['metrics']
        print("\nMetrics:")
        for metric, value in metrics.items():
            if isinstance(value, tuple):
                value_str = str(value)
            elif isinstance(value, (float, int)):
                value_str = f"{value:.4f}"
            else:
                value_str = str(value)
            print(f"  {metric}: {value_str}")
        
        print(f"\nDetailed results saved to: {results['output_dir']}")
    except Exception as e:
        print(f"\nError running test: {str(e)}")
        logger.exception("Error in run command")


def handle_train_command(args, framework):
    """
    Handle 'train' command.
    
    Args:
        args: Command-line arguments
        framework: Testing framework instance
    """
    try:
        metrics = framework.train_model(args.param_id)
        
        print("\n=== Training Results ===")
        if 'error' in metrics:
            print(f"Error: {metrics['error']}")
        else:
            print("Model training completed successfully.")
            print("\nValidation metrics:")
            for metric, value in metrics.items():
                # Convert any tuple value to string for printing
                if isinstance(value, tuple):
                    value_str = str(value)
                elif isinstance(value, (float, int)):
                    value_str = f"{value:.4f}"
                else:
                    value_str = str(value)
                print(f"  {metric}: {value_str}")
    except Exception as e:
        print(f"\nError training model: {str(e)}")
        logger.exception("Error in train command")


def handle_evaluate_command(args, framework):
    """
    Handle 'evaluate' command.
    
    Args:
        args: Command-line arguments
        framework: Testing framework instance
    """
    try:
        results = framework.get_test_results(args.param_id)
        
        print("\n=== Evaluation Results ===")
        if 'error' in results:
            print(f"Error: {results['error']}")
            return
        
        print(f"Parameter ID: {results['parameter']['param_id']}")
        print(f"Test name: {results['parameter']['test_name']}")
        print(f"Messages evaluated: {results['num_messages']}")
        
        metrics = results['evaluation']['metrics']
        print("\nMetrics:")
        for metric, value in metrics.items():
            if isinstance(value, tuple):
                value_str = str(value)
            elif isinstance(value, (float, int)):
                value_str = f"{value:.4f}"
            else:
                value_str = str(value)
            print(f"  {metric}: {value_str}")
        
        print(f"\nDetailed results saved to: {results['output_dir']}")
    except Exception as e:
        print(f"\nError evaluating results: {str(e)}")
        logger.exception("Error in evaluate command")


def handle_generate_command(args, framework):
    """
    Handle 'generate' command.
    
    Args:
        args: Command-line arguments
        framework: Testing framework instance
    """
    param_id = framework.create_test_parameters(args.name, args.description)
    message_ids = framework.generate_messages(param_id, args.num_messages)
    
    print("\n=== Message Generation Results ===")
    print(f"Parameter ID: {param_id}")
    print(f"Test name: {args.name}")
    print(f"Messages generated: {len(message_ids)}")


def handle_list_command(args, framework):
    """
    Handle 'list' command.
    
    Args:
        args: Command-line arguments
        framework: Testing framework instance
    """
    db_manager = framework.db_manager
    
    if args.param_id:
        param = db_manager.get_parameter(args.param_id)
        if not param:
            print(f"Error: Parameter ID {args.param_id} not found")
            return
        
        print("\n=== Parameter Details ===")
        print(f"Parameter ID: {param['param_id']}")
        print(f"Test name: {param['test_name']}")
        print(f"Description: {param['description']}")
        print(f"Creation date: {param['creation_date']}")
        
        messages = db_manager.get_messages_by_param(args.param_id)
        print(f"\nMessages: {len(messages)}")
        
    else:
        print("\n=== Test Parameters ===")
        print("Listing all parameters not implemented yet.")
        print("Use --param-id to view details for a specific parameter.")


def main():
    """Main entry point for the CLI."""
    parser = setup_arg_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        framework = create_testing_framework(args.config)
        
        if args.command == "run":
            handle_run_command(args, framework)
        elif args.command == "evaluate":
            handle_evaluate_command(args, framework)
        elif args.command == "generate":
            handle_generate_command(args, framework)
        elif args.command == "list":
            handle_list_command(args, framework)
        else:
            parser.print_help()
        
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 