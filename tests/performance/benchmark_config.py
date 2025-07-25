"""
Performance benchmark configuration and utilities

Centralized configuration for performance tests, benchmark utilities,
and performance regression detection.
"""

import os
import json
import time
import psutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class BenchmarkResult:
    """Represents a benchmark test result"""
    test_name: str
    mean_time: float
    min_time: float
    max_time: float
    std_dev: float
    iterations: int
    memory_usage_mb: float
    timestamp: datetime
    system_info: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BenchmarkResult':
        """Create from dictionary"""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark tests"""
    # Test execution settings
    min_iterations: int = 5
    max_iterations: int = 100
    target_duration: float = 1.0  # Target test duration in seconds
    warmup_iterations: int = 2

    # Performance thresholds
    max_memory_increase_mb: float = 100.0
    max_response_time_ms: float = 1000.0
    min_cache_hit_ratio: float = 0.8
    max_cpu_usage_percent: float = 80.0

    # Fimits for testing
    max_test_file_size_mb: float = 10.0
    max_test_directory_files: int = 1000

    # AI-specific settings
    ai_timeout_seconds: float = 30.0
    max_concurrent_ai_requests: int = 10
    ai_cache_size: int = 1000

    # UI-specific settings
    max_ui_render_time_ms: float = 100.0
    max_theme_switch_time_ms: float = 200.0
    ui_animation_duration_ms: float = 300.0

    # Regression detection
    performance_regression_threshold: float = 0.2  # 20% slower is a regression
    memory_regression_threshold: float = 0.15  # 15% more memory is a regression


class BenchmarkUtils:
    """Utilities for performance benchmarking"""

    @staticmethod
    def get_system_info() -> Dict[str, Any]:
        """Get system information for benchmark context"""
        return {
            'cpu_count': psutil.cpu_count(),
            'cpu_freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'platform': os.name,
            'python_version': os.sys.version,
            'hostname': os.uname().nodename if hasattr(os, 'uname') else 'unknown'
        }

    @staticmethod
    def measure_memory_usage(func, *args, **kwargs) -> tuple[Any, float]:
        """Measure memory usage of a function call"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        result = func(*args, **kwargs)

        peak_memory = process.memory_info().rss
        memory_increase_mb = (peak_memory - initial_memory) / (1024 * 1024)

        return result, memory_increase_mb

    @staticmethod
    def create_test_files(directory: Path, count: int, size_range: tuple[int, int] = (100, 10000)) -> List[Path]:
        """Create test files for benchmarking"""
        files = []
        directory.mkdir(parents=True, exist_ok=True)

        file_types = ['.txt', '.py', '.json', '.md', '.csv']

        for i in range(count):
            file_type = file_types[i % len(file_types)]
            filename = f"benchmark_file_{i:04d}{file_type}"
            file_path = directory / filename

            # Generate content based on file type
            size = size_range[0] + (i * (size_range[1] - size_range[0])) // count

            if file_type == '.py':
                content = f'''
def benchmark_function_{i}():
    """Generated function for benchmarking"""
    data = [{j} for j in range({size // 20})]
    return sum(data)

class BenchmarkClass_{i}:
    def __init__(self):
        self.value = {i}
        self.data = "x" * {size // 10}
'''
            elif file_type == '.json':
                content = json.dumps({
                    'id': i,
                    'name': f'benchmark_item_{i}',
                    'data': 'x' * (size // 2),
                    'items': list(range(min(size // 50, 100)))
                }, indent=2)
            else:
                content = f"Benchmark content for file {i}\n" * (size // 30)

            file_path.write_text(content)
            files.append(file_path)

        return files

    @staticmethod
    def cleanup_test_files(files: List[Path]):
        """Clean up test files after benchmarking"""
        for file_path in files:
            try:
                if file_path.exists():
                    file_path.unlink()
            except Exception:
                pass  # Ignore cleanup errors


class PerformanceTracker:
    """Track performance metrics over time"""

    def __init__(self, results_file: Optional[Path] = None):
        self.results_file = results_file or Path("benchmark_results.json")
        self.results: List[BenchmarkResult] = []
        self.load_results()

    def load_results(self):
        """Load previous benchmark results"""
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r') as f:
                    data = json.load(f)
                    self.results = [BenchmarkResult.from_dict(item) for item in data]
            except Exception as e:
                print(f"Warning: Could not load benchmark results: {e}")
                self.results = []

    def save_results(self):
        """Save benchmark results to file"""
        try:
            with open(self.results_file, 'w') as f:
                json.dump([result.to_dict() for result in self.results], f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save benchmark results: {e}")

    def add_result(self, result: BenchmarkResult):
        """Add a new benchmark result"""
        self.results.append(result)
        self.save_results()

    def get_latest_results(self, test_name: str, count: int = 10) -> List[BenchmarkResult]:
        """Get latest results for a specific test"""
        test_results = [r for r in self.results if r.test_name == test_name]
        return sorted(test_results, key=lambda x: x.timestamp, reverse=True)[:count]

    def detect_regression(self, new_result: BenchmarkResult, config: BenchmarkConfig) -> Optional[str]:
        """Detect performance regression"""
        previous_results = self.get_latest_results(new_result.test_name, 5)

        if len(previous_results) < 2:
            return None  # Not enough data for comparison

        # Calculate baseline performance (average of previous results)
        baseline_time = sum(r.mean_time for r in previous_results) / len(previous_results)
        baseline_memory = sum(r.memory_usage_mb for r in previous_results) / len(previous_results)

        # Check for time regression
        time_increase = (new_result.mean_time - baseline_time) / baseline_time
        if time_increase > config.performance_regression_threshold:
            return f"Performance regression detected: {time_increase:.1%} slower than baseline"

        # Check for memory regression
        memory_increase = (new_result.memory_usage_mb - baseline_memory) / baseline_memory
        if memory_increase > config.memory_regression_threshold:
            return f"Memory regression detected: {memory_increase:.1%} more memory than baseline"

        return None

    def generate_report(self) -> str:
        """Generate performance report"""
        if not self.results:
            return "No benchmark results available"

        # Group results by test name
        test_groups = {}
        for result in self.results:
            if result.test_name not in test_groups:
                test_groups[result.test_name] = []
            test_groups[result.test_name].append(result)

        report_lines = ["# Performance Benchmark Report\n"]

        for test_name, results in test_groups.items():
            if not results:
                continue

            latest = max(results, key=lambda x: x.timestamp)
            avg_time = sum(r.mean_time for r in results) / len(results)
            avg_memory = sum(r.memory_usage_mb for r in results) / len(results)

            report_lines.extend([
                f"## {test_name}",
                f"- Latest run: {latest.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                f"- Latest time: {latest.mean_time:.3f}s",
                f"- Average time: {avg_time:.3f}s",
                f"- Latest memory: {latest.memory_usage_mb:.1f}MB",
                f"- Average memory: {avg_memory:.1f}MB",
                f"- Total runs: {len(results)}",
                ""
            ])

        return "\n".join(report_lines)


class BenchmarkDecorator:
    """Decorator for automatic benchmark tracking"""

    def __init__(self, config: BenchmarkConfig, tracker: PerformanceTracker):
        self.config = config
        self.tracker = tracker

    def __call__(self, test_name: str):
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Warmup runs
                for _ in range(self.config.warmup_iterations):
                    func(*args, **kwargs)

                # Benchmark runs
                times = []
                memory_usage = 0

                for _ in range(self.config.min_iterations):
                    start_time = time.time()
                    result, mem_usage = BenchmarkUtils.measure_memory_usage(func, *args, **kwargs)
                    end_time = time.time()

                    times.append(end_time - start_time)
                    memory_usage = max(memory_usage, mem_usage)

                # Calculate statistics
                mean_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                std_dev = (sum((t - mean_time) ** 2 for t in times) / len(times)) ** 0.5

                # Create benchmark result
                benchmark_result = BenchmarkResult(
                    test_name=test_name,
                    mean_time=mean_time,
                    min_time=min_time,
                    max_time=max_time,
                    std_dev=std_dev,
                    iterations=len(times),
                    memory_usage_mb=memory_usage,
                    timestamp=datetime.now(),
                    system_info=BenchmarkUtils.get_system_info()
                )

                # Check for regression
                regression = self.tracker.detect_regression(benchmark_result, self.config)
                if regression:
                    print(f"WARNING: {regression}")

                # Add to tracker
                self.tracker.add_result(benchmark_result)

                return result

            return wrapper
        return decorator


# Global benchmark configuration
DEFAULT_CONFIG = BenchmarkConfig()

# Global performance tracker
PERFORMANCE_TRACKER = PerformanceTracker()

# Benchmark decorator with default config
benchmark = BenchmarkDecorator(DEFAULT_CONFIG, PERFORMANCE_TRACKER)