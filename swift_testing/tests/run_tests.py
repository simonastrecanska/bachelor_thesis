#!/usr/bin/env python3
"""
Test runner for the SWIFT message routing testing framework.

Examples:
    # Run all tests
    python run_tests.py

    # Run unit tests only
    python run_tests.py --unit

    # Run integration tests only
    python run_tests.py --integration

    # Run with coverage report
    python run_tests.py --coverage

    # Run specific test modules
    python run_tests.py --modules test_message_generator test_db_manager
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run tests for the SWIFT testing framework")
    
    parser.add_argument(
        "--unit", action="store_true", help="Run unit tests only"
    )
    parser.add_argument(
        "--integration", action="store_true", help="Run integration tests only"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Generate coverage report"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Verbose output"
    )
    parser.add_argument(
        "--modules", nargs="+", help="Specific test modules to run (without .py extension)"
    )
    
    return parser.parse_args()


def main():
    """Run the tests based on command line arguments."""
    args = parse_args()
    
    pytest_args = ["pytest"]

    if args.verbose:
        pytest_args.append("-v")
    
    if args.unit and not args.integration:
        pytest_args.append("unit/")
    elif args.integration and not args.unit:
        pytest_args.append("integration/")
    
    if args.coverage:
        pytest_args.extend([
            "--cov=swift_testing/src",
            "--cov-report=term",
            "--cov-report=html:coverage_html"
        ])

    if args.modules:
        for module in args.modules:
            if not module.endswith(".py"):
                module = f"{module}.py"
            
            module_paths = list(Path(".").glob(f"**/test_{module}"))
            if not module_paths:
                module_paths = list(Path(".").glob(f"**/{module}"))
            
            if not module_paths:
                print(f"Warning: Could not find test module {module}")
                continue
            
            pytest_args.append(str(module_paths[0]))
    
    print(f"Running tests with command: {' '.join(pytest_args)}")
    result = subprocess.run(pytest_args)
    
    return result.returncode


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    sys.exit(main()) 