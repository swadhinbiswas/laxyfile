#!/usr/bin/env python3
"""
Test runner for LaxyFile test suite

This script provides a comprehensive test runner with various options for
running different types of tests, generating reports, and managing test execution.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> int:
    """Run a command and return the exit code"""
    print(f"Running: {' '.join(cmd)}")
    if cwd:
        print(f"Working directory: {cwd}")

    try:
        result = subprocess.run(cmd, cwd=cwd, check=False)
        return result.returncode
    except FileNotFoundError:
        print(f"Error: Command not found: {cmd[0]}")
        return 1


def run_unit_tests(verbose: bool = False, coverage: bool = False,
                  specific_test: Optional[str] = None) -> int:
    """Run unit tests"""
    print("=" * 60)
    print("Running Unit Tests")
    print("=" * 60)

    cmd = ["python", "-m", "pytest", "tests/unit/"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(["--cov=laxyfile", "--cov-report=term-missing", "--cov-report=html"])

    if specific_test:
        cmd.append(f"tests/unit/{specific_test}")

    cmd.extend(["-x", "--tb=short"])  # Stop on first failure, short traceback

    return run_command(cmd, project_root)


def run_integration_tests(verbose: bool = False) -> int:
    """Run integration tests"""
    print("=" * 60)
    print("Running Integration Tests")
    print("=" * 60)

    cmd = ["python", "-m", "pytest", "tests/integration/", "-m", "integration"]

    if verbose:
        cmd.append("-v")

    cmd.extend(["-x", "--tb=short", "--asyncio-mode=auto"])

    return run_command(cmd, project_root)


def run_e2e_tests(verbose: bool = False) -> int:
    """Run end-to-end tests"""
    print("=" * 60)
    print("Running End-to-End Tests")
    print("=" * 60)

    cmd = ["python", "-m", "pytest", "tests/e2e/", "-m", "e2e"]

    if verbose:
        cmd.append("-v")

    cmd.extend(["-x", "--tb=short", "--asyncio-mode=auto"])

    return run_command(cmd, project_root)


def run_performance_tests(verbose: bool = False) -> int:
    """Run performance tests"""
    print("=" * 60)
    print("Running Performance Tests")
    print("=" * 60)

    cmd = ["python", "-m", "pytest", "tests/", "-m", "performance"]

    if verbose:
        cmd.append("-v")

    cmd.extend(["--tb=short", "--benchmark-only"])

    return run_command(cmd, project_root)


def run_all_tests(verbose: bool = False, coverage: bool = False) -> int:
    """Run all tests"""
    print("=" * 60)
    print("Running All Tests")
    print("=" * 60)

    cmd = ["python", "-m", "pytest", "tests/"]

    if verbose:
        cmd.append("-v")

    if coverage:
        cmd.extend(["--cov=laxyfile", "--cov-report=term-missing", "--cov-report=html"])

    cmd.extend(["--tb=short"])

    return run_command(cmd, project_root)


def run_linting() -> int:
    """Run code linting"""
    print("=" * 60)
    print("Running Code Linting")
    print("=" * 60)

    # Run flake8
    print("Running flake8...")
    flake8_result = run_command(["python", "-m", "flake8", "laxyfile/", "tests/"], project_root)

    # Run mypy
    print("\nRunning mypy...")
    mypy_result = run_command(["python", "-m", "mypy", "laxyfile/"], project_root)

    return max(flake8_result, mypy_result)


def run_formatting_check() -> int:
    """Check code formatting"""
    print("=" * 60)
    print("Checking Code Formatting")
    print("=" * 60)

    cmd = ["python", "-m", "black", "--check", "--diff", "laxyfile/", "tests/"]
    return run_command(cmd, project_root)


def format_code() -> int:
    """Format code"""
    print("=" * 60)
    print("Formatting Code")
    print("=" * 60)

    cmd = ["python", "-m", "black", "laxyfile/", "tests/"]
    return run_command(cmd, project_root)


def generate_test_report() -> int:
    """Generate comprehensive test report"""
    print("=" * 60)
    print("Generating Test Report")
    print("=" * 60)

    cmd = [
        "python", "-m", "pytest", "tests/",
        "--html=test_report.html",
        "--self-contained-html",
        "--cov=laxyfile",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml",
        "--junit-xml=test_results.xml"
    ]

    return run_command(cmd, project_root)


def check_dependencies() -> bool:
    """Check if required test dependencies are installed"""
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "pytest-html",
        "pytest-benchmark",
        "black",
        "flake8",
        "mypy"
    ]

    missing_packages = []

    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        print("Missing required packages:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\nInstall with: pip install " + " ".join(missing_packages))
        return False

    return True


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="LaxyFile Test Runner")

    parser.add_argument(
        "test_type",
        choices=["unit", "integration", "e2e", "performance", "all", "lint", "format", "format-check", "report"],
        help="Type of tests to run"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Generate coverage report"
    )

    parser.add_argument(
        "-t", "--test",
        help="Run specific test file (for unit tests)"
    )

    parser.add_argument(
        "--no-deps-check",
        action="store_true",
        help="Skip dependency check"
    )

    args = parser.parse_args()

    # Check dependencies unless skipped
    if not args.no_deps_check and not check_dependencies():
        return 1

    # Run the requested test type
    if args.test_type == "unit":
        return run_unit_tests(args.verbose, args.coverage, args.test)
    elif args.test_type == "integration":
        return run_integration_tests(args.verbose)
    elif args.test_type == "e2e":
        return run_e2e_tests(args.verbose)
    elif args.test_type == "performance":
        return run_performance_tests(args.verbose)
    elif args.test_type == "all":
        return run_all_tests(args.verbose, args.coverage)
    elif args.test_type == "lint":
        return run_linting()
    elif args.test_type == "format":
        return format_code()
    elif args.test_type == "format-check":
        return run_formatting_check()
    elif args.test_type == "report":
        return generate_test_report()
    else:
        print(f"Unknown test type: {args.test_type}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)