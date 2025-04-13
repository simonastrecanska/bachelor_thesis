#!/usr/bin/env python3
"""
Main entry point for the package.

This module allows the package to be executed as a script.
"""

import sys
from swift_testing.src.interface.cli import main

if __name__ == "__main__":
    sys.exit(main()) 