"""
Performance tests and benchmarks for LaxyFile

Comprehensive performance testing framework including benchmarks,
load testing, memory profiling, and performance regression detection.

This module provides:
- File manager performance benchmarks
- UI rendering performance tests
- AI assistant response time benchmarks
- Memory usage and leak detection
- Stress tests for extreme conditions
- Performance regression detection
- Continuous performance monitoring

Usage:
    # Run all benchmarks
    python -m pytest tests/performance/ --benchmark-only

    # Run specific benchmark suite
    python tests/performance/run_benchmarks.py --suite file_manager

    # Start performance monitoring
    python tests/performance/monitor_performance.py --duration 300

    # Generate performance report
    python tests/performance/run_benchmarks.py --html-report
"""

from .benchmark_config import (
    BenchmarkConfig,
    BenchmarkResult,
    BenchmarkUtils,
    PerformanceTracker,
    BenchmarkDecorator,
    DEFAULT_CONFIG,
    PERFORMANCE_TRACKER,
    benchmark
)

from .monitor_performance import (
    PerformanceMonitor,
    PerformanceProfiler,
    PerformanceMetric,
    SystemMetrics
)

__all__ = [
    'BenchmarkConfig',
    'BenchmarkResult',
    'BenchmarkUtils',
    'PerformanceTracker',
    'BenchmarkDecorator',
    'DEFAULT_CONFIG',
    'PERFORMANCE_TRACKER',
    'benchmark',
    'PerformanceMonitor',
    'PerformanceProfiler',
    'PerformanceMetric',
    'SystemMetrics'
]