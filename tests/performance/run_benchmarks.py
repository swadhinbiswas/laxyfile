#!/usr/bin/env python3
"""
Performance benchmark runner

Comprehensive benchmark runner that executes all performance tests,
generates reports, and detects performance regressions.
"""

import sys
import argparse
import subprocess
import time
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.performance.benchmark_config import (
    BenchmarkConfig, PerformanceTracker, BenchmarkUtils
)


class BenchmarkRunner:
    """Main benchmark runner class"""

    def __init__(self, config: Optional[BenchmarkConfig] = None):
        self.config = config or BenchmarkConfig()
        self.tracker = PerformanceTracker()
        self.results: Dict[str, Any] = {}

    def run_pytest_benchmarks(self, test_pattern: str = "tests/performance/") -> Dict[str, Any]:
        """Run pytest benchmarks and collect results"""
        print(f"Running pytest benchmarks: {test_pattern}")

        # Prepare pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            test_pattern,
            "-v",
            "--benchmark-only",
            "--benchmark-json=benchmark_results.json",
            "--benchmark-sort=mean",
            "--benchmark-columns=min,max,mean,stddev,median",
            "--benchmark-warmup=on",
            "--benchmark-disable-gc",
            "--tb=short"
        ]

        # Add markers if specified
        if hasattr(self, 'markers') and self.markers:
            cmd.extend(["-m", " or ".join(self.markers)])

        try:
            # Run pytest
            start_time = time.time()
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1 hour timeout
            end_time = time.time()

            # Parse results
            benchmark_data = {}
            if Path("benchmark_results.json").exists():
                with open("benchmark_results.json", "r") as f:
                    benchmark_data = json.load(f)

            return {
                'success': result.returncode == 0,
                'duration': end_time - start_time,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'benchmark_data': benchmark_data
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'duration': 3600,
                'error': 'Benchmark execn timed out after 1 hour'
            }
        except Exception as e:
            return {
                'success': False,
                'duration': 0,
                'error': str(e)
            }

    def run_file_manager_benchmarks(self) -> Dict[str, Any]:
        """Run file manager specific benchmarks"""
        print("Running file manager benchmarks...")
        return self.run_pytest_benchmarks("tests/performance/test_file_manager_benchmarks.py")

    def run_ui_benchmarks(self) -> Dict[str, Any]:
        """Run UI specific benchmarks"""
        print("Running UI benchmarks...")
        return self.run_pytest_benchmarks("tests/performance/test_ui_performance.py")

    def run_ai_benchmarks(self) -> Dict[str, Any]:
        """Run AI specific benchmarks"""
        print("Running AI benchmarks...")
        return self.run_pytest_benchmarks("tests/performance/test_ai_performance.py")

    def run_stress_tests(self) -> Dict[str, Any]:
        """Run stress tests"""
        print("Running stress tests...")
        self.markers = ["slow"]
        return self.run_pytest_benchmarks("tests/performance/")

    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmark suites"""
        print("=" * 60)
        print("LAXYFILE PERFORMANCE BENCHMARK SUITE")
        print("=" * 60)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"System info: {BenchmarkUtils.get_system_info()}")
        print("=" * 60)

        all_results = {}
        total_start_time = time.time()

        # Run individual benchmark suites
        benchmark_suites = [
            ("file_manager", self.run_file_manager_benchmarks),
            ("ui", self.run_ui_benchmarks),
            ("ai", self.run_ai_benchmarks),
        ]

        for suite_name, suite_func in benchmark_suites:
            print(f"\n{'='*20} {suite_name.upper()} BENCHMARKS {'='*20}")
            suite_start = time.time()

            try:
                suite_results = suite_func()
                suite_duration = time.time() - suite_start

                all_results[suite_name] = {
                    **suite_results,
                    'suite_duration': suite_duration
                }

                if suite_results['success']:
                    print(f"✅ {suite_name} benchmarks completed in {suite_duration:.2f}s")
                else:
                    print(f"❌ {suite_name} benchmarks failed")
                    if 'error' in suite_results:
                        print(f"Error: {suite_results['error']}")

            except Exception as e:
                print(f"❌ {suite_name} benchmarks crashed: {e}")
                all_results[suite_name] = {
                    'success': False,
                    'error': str(e),
                    'suite_duration': time.time() - suite_start
                }

        total_duration = time.time() - total_start_time

        # Generate summary
        successful_suites = sum(1 for r in all_results.values() if r.get('success', False))
        total_suites = len(all_results)

        print(f"\n{'='*60}")
        print("BENCHMARK SUMMARY")
        print(f"{'='*60}")
        print(f"Total duration: {total_duration:.2f}s")
        print(f"Successful suites: {successful_suites}/{total_suites}")

        for suite_name, results in all_results.items():
            status = "✅ PASSED" if results.get('success', False) else "❌ FAILED"
            duration = results.get('suite_duration', 0)
            print(f"  {suite_name}: {status} ({duration:.2f}s)")

        all_results['summary'] = {
            'total_duration': total_duration,
            'successful_suites': successful_suites,
            'total_suites': total_suites,
            'timestamp': datetime.now().isoformat(),
            'system_info': BenchmarkUtils.get_system_info()
        }

        return all_results

    def generate_html_report(self, results: Dict[str, Any], output_file: Path = Path("benchmark_report.html")) -> None:
        """Generate HTML benchmark report"""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>LaxyFile Performance Benchmark Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .suite {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .success {{ border-left: 5px solid #4CAF50; }}
        .failure {{ border-left: 5px solid #f44336; }}
        .benchmark {{ margin: 10px 0; padding: 10px; background-color: #f9f9f9; }}
        .metric {{ display: inline-block; margin: 5px 10px; }}
        .error {{ color: #f44336; font-family: monospace; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>LaxyFile Performance Benchmark Report</h1>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Total Duration:</strong> {results.get('summary', {}).get('total_duration', 0):.2f}s</p>
        <p><strong>Success Rate:</strong> {results.get('summary', {}).get('successful_suites', 0)}/{results.get('summary', {}).get('total_suites', 0)} suites</p>
    </div>
"""

        # Add suite results
        for suite_name, suite_results in results.items():
            if suite_name == 'summary':
                continue

            success = suite_results.get('success', False)
            css_class = 'success' if success else 'failure'
            status_icon = '✅' if success else '❌'

            html_content += f"""
    <div class="suite {css_class}">
        <h2>{status_icon} {suite_name.title()} Benchmarks</h2>
        <p><strong>Duration:</strong> {suite_results.get('suite_duration', 0):.2f}s</p>
        <p><strong>Status:</strong> {'PASSED' if success else 'FAILED'}</p>
"""

            if not success and 'error' in suite_results:
                html_content += f'<div class="error">Error: {suite_results["error"]}</div>'

            # Add benchmark data if available
            benchmark_data = suite_results.get('benchmark_data', {})
            if benchmark_data and 'benchmarks' in benchmark_data:
                html_content += """
        <h3>Benchmark Results</h3>
        <table>
            <tr>
                <th>Test Name</th>
                <th>Mean (s)</th>
                <th>Min (s)</th>
                <th>Max (s)</th>
                <th>Std Dev</th>
                <th>Iterations</th>
            </tr>
"""
                for benchmark in benchmark_data['benchmarks']:
                    stats = benchmark.get('stats', {})
                    html_content += f"""
            <tr>
                <td>{benchmark.get('name', 'Unknown')}</td>
                <td>{stats.get('mean', 0):.4f}</td>
                <td>{stats.get('min', 0):.4f}</td>
                <td>{stats.get('max', 0):.4f}</td>
                <td>{stats.get('stddev', 0):.4f}</td>
                <td>{stats.get('rounds', 0)}</td>
            </tr>
"""
                html_content += "</table>"

            html_content += "</div>"

        html_content += """
</body>
</html>
"""

        output_file.write_text(html_content)
        print(f"HTML report generated: {output_file}")

    def save_results(self, results: Dict[str, Any], output_file: Path = Path("benchmark_results_full.json")) -> None:
        """Save complete benchmark results to JSON"""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"Full results saved: {output_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Run LaxyFile performance benchmarks")
    parser.add_argument(
        "--suite",
        choices=["all", "file_manager", "ui", "ai", "stress"],
        default="all",
        help="Benchmark suite to run"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("."),
        help="Output directory for reports"
    )
    parser.add_argument(
        "--html-report",
        action="store_true",
        help="Generate HTML report"
    )
    parser.add_argument(
        "--json-output",
        action="store_true",
        help="Save JSON results"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output"
    )

    args = parser.parse_args()

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Initialize runner
    runner = BenchmarkRunner()

    # Run benchmarks
    if args.suite == "all":
        results = runner.run_all_benchmarks()
    elif args.suite == "file_manager":
        results = {"file_manager": runner.run_file_manager_benchmarks()}
    elif args.suite == "ui":
        results = {"ui": runner.run_ui_benchmarks()}
    elif args.suite == "ai":
        results = {"ai": runner.run_ai_benchmarks()}
    elif args.suite == "stress":
        results = {"stress": runner.run_stress_tests()}

    # Generate reports
    if args.html_report:
        html_file = args.output_dir / "benchmark_report.html"
        runner.generate_html_report(results, html_file)

    if args.json_output:
        json_file = args.output_dir / "benchmark_results.json"
        runner.save_results(results, json_file)

    # Print summary
    if 'summary' in results:
        summary = results['summary']
        success_rate = summary['successful_suites'] / summary['total_suites']

        print(f"\n🎯 FINAL RESULT:")
        print(f"   Success Rate: {success_rate:.1%}")
        print(f"   Total Time: {summary['total_duration']:.2f}s")

        # Exit with appropriate code
        sys.exit(0 if success_rate == 1.0 else 1)
    else:
        # Single suite run
        suite_result = list(results.values())[0]
        success = suite_result.get('success', False)
        print(f"\n🎯 RESULT: {'SUCCESS' if success else 'FAILURE'}")
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()