#!/usr/bin/env python3
"""
Coverage Testing Script

Run comprehensive coverage tests locally and generate reports.
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Command: {cmd}")
        print(f"   Error: {e.stderr}")
        return None


def main():
    """Main coverage testing function"""
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    print("🧪 LaxyFile Coverage Testing")
    print("=" * 50)

    # Clean previous coverage data
    run_command("coverage erase", "Cleaning previous coverage data")

    # Run unit tests with coverage
    result = run_command(
        "python -m pytest tests/unit/ -v --cov=laxyfile --cov-append --cov-report=term-missing",
        "Running unit tests with coverage"
    )
    if not result:
        return 1

    # Run integration tests with coverage
    result = run_command(
        "python -m pytest tests/integration/ -v --cov=laxyfile --cov-append --cov-report=term-missing",
        "Running integration tests with coverage"
    )
    if not result:
        return 1

    # Run e2e tests with coverage
    result = run_command(
        "python -m pytest tests/e2e/ -v --cov=laxyfile --cov-append --cov-report=term-missing",
        "Running e2e tests with coverage"
    )
    if not result:
        return 1

    # Generate HTML report
    run_command("coverage html", "Generating HTML coverage report")

    # Generate XML report for Codecov
    run_command("coverage xml", "Generating XML coverage report")

    # Show coverage summary
    result = run_command("coverage report", "Generating coverage summary")

    print("\n" + "=" * 50)
    print("📊 Coverage Report Generated!")
    print("=" * 50)
    print("📁 HTML Report: htmlcov/index.html")
    print("📄 XML Report: coverage.xml")
    print("🌐 Open HTML report: file://" + str(project_root / "htmlcov" / "index.html"))

    # Check if coverage meets minimum threshold
    if result and result.stdout:
        lines = result.stdout.split('\n')
        for line in lines:
            if 'TOTAL' in line and '%' in line:
                # Extract percentage
                parts = line.split()
                for part in parts:
                    if part.endswith('%'):
                        coverage_pct = int(part[:-1])
                        print(f"\n📈 Total Coverage: {coverage_pct}%")

                        if coverage_pct >= 80:
                            print("✅ Coverage meets target (80%+)")
                            return 0
                        elif coverage_pct >= 70:
                            print("⚠️ Coverage below target but acceptable (70-79%)")
                            return 0
                        else:
                            print("❌ Coverage below minimum threshold (70%)")
                            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())