"""
Command-Line Interface

This module provides a command-line interface for the SWIFT message routing testing framework.
"""

import os
import sys
import json
import csv
import logging
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

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
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json", "csv"],
        default="text",
        help="Format for command output"
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
    
    train_parser = subparsers.add_parser(
        "train", help="Train the routing model"
    )
    train_parser.add_argument(
        "--param-id", 
        type=int,
        help="Parameter ID to use for training (if not specified, uses templates)"
    )
    
    list_parser = subparsers.add_parser(
        "list", help="List test parameters"
    )
    list_parser.add_argument(
        "--param-id", 
        type=int,
        help="Parameter ID to show details (if not specified, lists all)"
    )
    
    delete_parser = subparsers.add_parser(
        "delete", help="Delete test parameter and associated data"
    )
    delete_parser.add_argument(
        "--param-id", 
        type=int,
        required=True,
        help="Parameter ID to delete"
    )
    delete_parser.add_argument(
        "--confirm",
        action="store_true",
        help="Confirm deletion without prompting"
    )
    
    return parser


def format_output(data: Dict[str, Any], output_format: str, filename: Optional[str] = None) -> None:
    """
    Format and output data based on specified format.
    
    Args:
        data: Data to output
        output_format: Format type (text, json, csv)
        filename: If provided, write to this file instead of stdout
    """
    if output_format == "json":
        output = json.dumps(data, indent=2, default=str)
        if filename:
            with open(filename, 'w') as f:
                f.write(output)
        else:
            print(output)
    elif output_format == "csv":
        if not filename:
            filename = f"output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        flattened_data = {}
        for key, value in data.items():
            if isinstance(value, dict):
                for k, v in value.items():
                    flattened_data[f"{key}_{k}"] = v
            else:
                flattened_data[key] = value
                
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=flattened_data.keys())
            writer.writeheader()
            writer.writerow(flattened_data)
        print(f"Output written to {filename}")
    else:
        if 'metrics' in data and isinstance(data['metrics'], dict):
            print("\nMetrics:")
            for metric, value in data['metrics'].items():
                if isinstance(value, tuple):
                    value_str = str(value)
                elif isinstance(value, (float, int)):
                    value_str = f"{value:.4f}"
                else:
                    value_str = str(value)
                print(f"  {metric}: {value_str}")
        else:
            for key, value in data.items():
                if isinstance(value, dict):
                    print(f"\n{key.title()}:")
                    for k, v in value.items():
                        print(f"  {k}: {v}")
                else:
                    print(f"{key.title()}: {value}")


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
            args.train if hasattr(args, 'train') else False
        )
        
        if args.output_format == "text":
            print("\n=== Test Results ===")
            print(f"Parameter ID: {results['parameter']['param_id']}")
            print(f"Test name: {results['parameter']['test_name']}")
            print(f"Messages tested: {results['num_messages']}")
            print(f"Execution time: {results['execution_time']:.2f} seconds")
        
        format_output(results, args.output_format)
        
        if args.output_format == "text":
            print(f"\nDetailed results saved to: {results['output_dir']}")
    except Exception as e:
        print(f"\nError running test: {str(e)}")
        if args.verbose:
            logger.exception("Error in run command")
        else:
            logger.error(f"Error in run command: {str(e)}")


def handle_evaluate_command(args, framework):
    """
    Handle 'evaluate' command.
    
    Args:
        args: Command-line arguments
        framework: Testing framework instance
    """
    try:
        results = framework.get_test_results(args.param_id)
        
        if 'error' in results:
            print(f"Error: {results['error']}")
            return
        
        if args.output_format == "text":
            print("\n=== Evaluation Results ===")
            print(f"Parameter ID: {results['parameter']['param_id']}")
            print(f"Test name: {results['parameter']['test_name']}")
            print(f"Messages evaluated: {results['num_messages']}")
        
        format_output(results, args.output_format)
        
        if args.output_format == "text":
            print(f"\nDetailed results saved to: {results['output_dir']}")
    except Exception as e:
        print(f"\nError evaluating results: {str(e)}")
        if args.verbose:
            logger.exception("Error in evaluate command")
        else:
            logger.error(f"Error in evaluate command: {str(e)}")


def handle_generate_command(args, framework):
    """
    Handle 'generate' command.
    
    Args:
        args: Command-line arguments
        framework: Testing framework instance
    """
    try:
        param_id = framework.generate_test_messages(
            num_messages=args.num_messages,
            test_name=args.name,
            description=args.description,
            variations_per_template=getattr(args, 'variations_per_template', None),
            substitution_rate=getattr(args, 'substitution_rate', None)
        )
        
        if args.output_format == "text":
            print(f"\nSuccessfully generated test messages.")
            print(f"Parameter ID: {param_id}")
            print(f"Test name: {args.name}")
            print(f"Number of messages: {args.num_messages}")
        else:
            data = {
                "status": "success",
                "param_id": param_id,
                "test_name": args.name,
                "num_messages": args.num_messages
            }
            format_output(data, args.output_format)
    except Exception as e:
        print(f"\nError generating test messages: {str(e)}")
        if args.verbose:
            logger.exception("Error in generate command")
        else:
            logger.error(f"Error in generate command: {str(e)}")


def handle_train_command(args, framework):
    """
    Handle 'train' command.
    
    Args:
        args: Command-line arguments
        framework: Testing framework instance
    """
    try:
        results = framework.train_model(args.param_id)
        
        if args.output_format == "text":
            print("\n=== Training Results ===")
            print(f"Model ID: {results['model_id']}")
            
            if 'param_id' in results and results['param_id']:
                print(f"Parameter ID: {results['param_id']}")
            else:
                print("Trained using templates (no parameter ID)")
            
            print(f"Accuracy: {results['accuracy']:.4f}")
            print(f"Training time: {results['training_time']:.2f} seconds")
            print(f"Epochs: {results['epochs']}")
        else:
            format_output(results, args.output_format)
    except Exception as e:
        print(f"\nError training model: {str(e)}")
        if args.verbose:
            logger.exception("Error in train command")
        else:
            logger.error(f"Error in train command: {str(e)}")


def handle_list_command(args, framework):
    """
    Handle 'list' command.
    
    Args:
        args: Command-line arguments
        framework: Testing framework instance
    """
    try:
        db_manager = framework.db_manager
        
        if args.param_id:
            param = db_manager.get_parameter(args.param_id)
            if not param:
                print(f"Error: Parameter ID {args.param_id} not found")
                return
            
            messages = db_manager.get_messages_by_param(args.param_id)
            param['message_count'] = len(messages)
            
            if args.output_format == "text":
                print("\n=== Parameter Details ===")
                print(f"Parameter ID: {param['param_id']}")
                print(f"Test name: {param['test_name']}")
                print(f"Description: {param['description']}")
                print(f"Creation date: {param['creation_date']}")
                print(f"Messages: {param['message_count']}")
            else:
                format_output(param, args.output_format)
            
        else:
            sql = "SELECT param_id, test_name, description, creation_date FROM test_parameters ORDER BY param_id DESC"
            params = db_manager.execute_query(sql)
            
            if args.output_format == "text":
                print("\n=== Test Parameters ===")
                if not params:
                    print("No parameters found.")
                else:
                    print(f"{'ID':>5} | {'Test Name':<30} | {'Creation Date':<20} | {'Description':<40}")
                    print("-" * 100)
                    for param in params:
                        print(f"{param['param_id']:>5} | {param['test_name']:<30} | {str(param['creation_date']):<20} | {param['description']:<40}")
            else:
                format_output({"parameters": params}, args.output_format)
    except Exception as e:
        print(f"\nError listing parameters: {str(e)}")
        if args.verbose:
            logger.exception("Error in list command")
        else:
            logger.error(f"Error in list command: {str(e)}")


def handle_delete_command(args, framework):
    """
    Handle 'delete' command.
    
    Args:
        args: Command-line arguments
        framework: Testing framework instance
    """
    try:
        db_manager = framework.db_manager
        
        param = db_manager.get_parameter(args.param_id)
        if not param:
            print(f"Error: Parameter ID {args.param_id} not found")
            return
        
        if not args.confirm:
            confirm = input(f"Are you sure you want to delete parameter {args.param_id} '{param['test_name']}'? (y/N): ")
            if confirm.lower() != 'y':
                print("Deletion cancelled.")
                return
        
        messages = db_manager.get_messages_by_param(args.param_id)
        message_ids = [m['message_id'] for m in messages]
        
        if message_ids:
            placeholders = ','.join(['%s'] * len(message_ids))
            sql = f"DELETE FROM actual_results WHERE message_id IN ({placeholders})"
            db_manager.execute_update(sql, message_ids)
            
        if message_ids:
            placeholders = ','.join(['%s'] * len(message_ids))
            sql = f"DELETE FROM expected_results WHERE message_id IN ({placeholders})"
            db_manager.execute_update(sql, message_ids)
            
        sql = "DELETE FROM messages WHERE param_id = %s"
        db_manager.execute_update(sql, [args.param_id])
        
        sql = "DELETE FROM test_parameters WHERE param_id = %s"
        db_manager.execute_update(sql, [args.param_id])
        
        print(f"Successfully deleted parameter {args.param_id} and all associated data.")
    except Exception as e:
        print(f"\nError deleting parameter: {str(e)}")
        if args.verbose:
            logger.exception("Error in delete command")
        else:
            logger.error(f"Error in delete command: {str(e)}")


def main():
    """
    Main function that parses command-line arguments and runs the appropriate command.
    """
    parser = setup_arg_parser()
    
    try:
        args = parser.parse_args()
        
        if args.verbose:
            logging.basicConfig(
                level=logging.DEBUG,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            logger.debug("Verbose logging enabled")
        
        config = load_config(args.config)
        
        framework = create_testing_framework(config)
        
        if args.command == "generate":
            handle_generate_command(args, framework)
        elif args.command == "run":
            handle_run_command(args, framework)
        elif args.command == "evaluate":
            handle_evaluate_command(args, framework)
        elif args.command == "train":
            handle_train_command(args, framework)
        elif args.command == "list":
            handle_list_command(args, framework)
        elif args.command == "delete":
            handle_delete_command(args, framework)
        else:
            logger.error(f"Unknown command: {args.command}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if getattr(args, 'verbose', False):
            logger.exception("Detailed error traceback:")
        sys.exit(1)


if __name__ == "__main__":
    main() 