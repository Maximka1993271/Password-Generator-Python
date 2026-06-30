#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test runner for Secure Pass Pro.
Запуск тестов для Secure Pass Pro.
Запуск тестів для Secure Pass Pro.
"""
from __future__ import annotations
import sys
import os
import unittest
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests(verbosity: int = 2, pattern: str = "test_*.py"):
    """
    Run all tests.
    
    Args:
        verbosity: Verbosity level (0-2)
        pattern: Test file pattern
    """
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern=pattern)
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run Secure Pass Pro tests"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "-p", "--pattern",
        default="test_*.py",
        help="Test file pattern (default: test_*.py)"
    )
    parser.add_argument(
        "-m", "--module",
        default=None,
        help="Run specific test module"
    )
    
    args = parser.parse_args()
    
    verbosity = 2 if args.verbose else 1
    
    if args.module:
        # Run specific module
        suite = unittest.TestLoader().loadTestsFromName(args.module)
        runner = unittest.TextTestRunner(verbosity=verbosity)
        result = runner.run(suite)
        success = result.wasSuccessful()
    else:
        # Run all tests
        success = run_tests(verbosity, args.pattern)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()