#!/usr/bin/env python3
"""
Test Runner for Self-Evolution Skill

Runs all unit tests and generates a summary report.

Usage:
    python run_tests.py
    python run_tests.py --verbose
"""

import unittest
import sys
from pathlib import Path


def run_tests(verbosity=1):
    """Run all tests

    Args:
        verbosity: Verbosity level (0-2)

    Returns:
        Exit code (0 for success, 1 for failures)
    """
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent / 'tests'
    suite = loader.discover(start_dir, pattern='test_*.py')

    # Run tests
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    if result.wasSuccessful():
        print("\n[SUCCESS] All tests passed!")
        return 0
    else:
        print("\n[FAILED] Some tests failed")
        return 1


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Self-Evolution Test Runner')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    verbosity = 2 if args.verbose else 1
    sys.exit(run_tests(verbosity))


if __name__ == '__main__':
    main()
