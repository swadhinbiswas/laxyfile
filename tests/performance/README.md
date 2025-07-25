# LaxyFile Performance Testing Framework

This directory contains a comprehensive performance testing framework for LaxyFile, designed to ensure optimal performance across all components and detect performance regressions early.

## Overview

The performance testing framework includes:

- **Benchmark Tests**: Automated performance benchmarks for all major components
- **Stress Tests**: Tests under extreme conditions and high load
- **Memory Profiling**: Memory usage analysis and leak detection
- **Regression Detection**: Automatic detection of performance regressions
- **Continuous Monitoring**: Real-time performance monitoring and alerting
- **Reporting**: Detailed performance reports and visualizations

## Components

### 1. Benchmark Tests

#### File Manager Benchmarks (`test_file_manager_benchmarks.py`)

- Directory listing performance with large directories (1000+ files)
- File information retrieval and caching efficiency
- Search functionality performance (name and content search)
- Concurrent operations handling
- Memory usage during file operations
- Cache performance and cleanup

#### UI Performance Tests (`test_ui_performance.py`)

- File panel rendering with large file lists (2000+ files)
- Theme switching performance
- Modal dialog rendering
- Layout creation and resize handling
- Memory usage during UI operations
- Animation and visual effects performance

#### AI Assistant Benchmarks (`test_ai_performance.py`)

- File analysis response times
- Batch processing efficiency
- Organization suggestion generation
- Security analysis performance
- Caching effectiveness
- Concurrent AI request handling

### 2. Configuration and Utilities

#### Benchmark Configuration (`benchmark_config.py`)

- Centralized performance thresholds and limits
- System information collection
- Test file generation utilities
- Performance tracking and regression detection
- Benchmark result serialization

#### Performance Monitoring (`monitor_performance.py`)

- Real-time system resource monitoring
- Custom metric tracking
- Performance alert system
- Regression detection
- Data export and reporting

#### Benchmark Runner (`run_benchmarks.py`)

- Automated benchmark execution
- HTML and JSON report generation
- Suite-specific benchmark running
- Performance regression detection
- CI/CD integration support

## Usage

### Running Benchmarks

#### Run All Benchmarks

```bash
# Run complete benchmark suite
python tests/performance/run_benchmarks.py --suite all --html-report

# Run with pytest directly
python -m pytest tests/performance/ --benchmark-only -v
```

#### Run Specific Benchmark Suites

```bash
# File manager benchmarks only
python tests/performance/run_benchmarks.py --suite file_manager

# UI performance tests only
python tests/performance/run_benchmarks.py --suite ui

# AI assistant benchmarks only
python tests/performance/run_benchmarks.py --suite ai

# Stress tests (slow tests)
python tests/performance/run_benchmarks.py --suite stress
```

#### Generate Reports

```bash
# Generate HTML report
python tests/performance/run_benchmarks.py --suite all --html-report --output-dir reports/

# Generate JSON results
python tests/performance/run_benchmarks.py --suite all --json-output --output-dir reports/
```

### Performance Monitoring

#### Start Continuous Monitoring

```bash
# Monitor for 5 minutes
python tests/performance/monitor_performance.py --duration 300 --interval 1.0

# Continuous monitoring (Ctrl+C to stop)
python tests/performance/monitor_performance.py --duration 0

# Monitor with report generation
python tests/performance/monitor_performance.py --duration 300 --report --output monitoring_data.json
```

#### Using Performance Profiler in Code

```python
from tests.performance import PerformanceMonitor, PerformanceProfiler

monitor = PerformanceMonitor()
monitor.start_monitoring()

# Profile a code block
with PerformanceProfiler(monitor, "file_operation") as profiler:
    # Your code here
    result = some_expensive_operation()

# Record custom metrics
monitor.record_metric("custom_metric", 123.45, "ms")

# Generate report
print(monitor.generate_report())
```

### Integration with pytest-benchmark

The framework integrates with pytest-benchmark for detailed statistical analysis:

```bash
# Run with benchmark statistics
python -m pytest tests/performance/ --benchmark-only --benchmark-sort=mean

# Save benchmark results
python -m pytest tests/performance/ --benchmark-only --benchmark-json=results.json

# Compare with previous results
python -m pytest tests/performance/ --benchmark-only --benchmark-compare=results.json
```

## Performance Thresholds

The framework enforces the following performance thresholds:

### File Manager Performance

- Directory listing: < 2.0s for 1000 files
- File info retrieval: < 1.0s for 100 files
- Search operations: < 3.0s for 1000 files
- Cache hit ratio: > 80%
- Memory usage: < 100MB increase

### UI Performance

- File panel rendering: < 1.0s for 2000 files
- Theme switching: < 2.0s
- Modal rendering: < 0.5s
- Layout operations: < 0.1s
- Memory usage: < 50MB increase

### AI Assistant Performance

- File analysis: < 2.0s per file
- Batch processing: < 1.5s for 5 files
- Organization suggestions: < 3.0s
- Cache hit improvement: > 50%
- Memory usage: < 100MB increase

### System Resources

- CPU usage: < 80% sustained
- Memory usage: < 85% of available
- Response time: < 1000ms
- Error rate: < 5%

## Stress Testing

Stress tests are marked with `@pytest.mark.slow` and test extreme conditions:

### File Manager Stress Tests

- 5000+ files in single directory
- 20+ concurrent operations
- Deep directory recursion (10+ levels)
- Memory stress with repeated operations

### UI Stress Tests

- 10,000+ files in file panel
- 2000+ selected files
- Rapid theme switching (50+ switches)
- Concurrent UI operations

### AI Stress Tests

- 1000+ files for analysis
- 20+ concurrent AI requests
- Memory stress with large responses
- Error handling under failures

## Regression Detection

The framework automatically detects performance regressions:

- **Performance Regression**: > 20% slower than baseline
- **Memory Regression**: > 15% more memory than baseline
- **Automatic Alerts**: Notifications when thresholds are exceeded
- **Historical Tracking**: Performance trends over time

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Performance Tests
on: [push, pull_request]

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-benchmark

      - name: Run performance benchmarks
        run: |
          python tests/performance/run_benchmarks.py --suite all --json-output

      - name: Upload benchmark results
        uses: actions/upload-artifact@v3
        with:
          name: benchmark-results
          path: benchmark_results.json
```

## Troubleshooting

### Common Issues

#### Slow Benchmark Execution

- Reduce test data size in fixtures
- Use `@pytest.mark.slow` for long-running tests
- Increase timeout values in configuration

#### Memory Issues

- Monitor system memory during tests
- Use garbage collection between tests
- Reduce concurrent operation limits

#### Inconsistent Results

- Run on dedicated hardware when possible
- Close unnecessary applications
- Use consistent test data
- Run multiple iterations for statistical significance

### Performance Debugging

#### Enable Verbose Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

#### Profile Specific Operations

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# Your code here
profiler.disable()

stats = pstats.Stats(profiler)
stats.sort_stats('cumulative').print_stats(10)
```

#### Memory Profiling

```python
import tracemalloc

tracemalloc.start()
# Your code here
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
tracemalloc.stop()
```

## Contributing

When adding new performance tests:

1. **Follow Naming Convention**: Use descriptive test names with `test_*_performance` pattern
2. **Set Appropriate Thresholds**: Define realistic performance expectations
3. **Include Documentation**: Document what the test measures and why
4. **Add Regression Detection**: Ensure new metrics are tracked for regressions
5. **Test Under Load**: Include both normal and stress test scenarios

### Example Test Structure

```python
@pytest.mark.performance
class TestNewFeatureBenchmarks:
    """Benchmark tests for new feature performance"""

    @pytest.fixture
    def test_data(self):
        """Create test data for benchmarks"""
        # Setup test data
        pass

    def test_new_feature_performance(self, test_data, benchmark):
        """Benchmark new feature performance"""

        def operation_to_benchmark():
            # Code to benchmark
            return result

        # Run benchmark
        result = benchmark(operation_to_benchmark)

        # Verify results
        assert result is not None

        # Performance assertions
        stats = benchmark.stats
        assert stats.mean < 1.0  # Should complete within 1 second
```

## Reports and Visualization

The framework generates comprehensive reports:

### HTML Reports

- Interactive performance charts
- Trend analysis over time
- Comparison with previous runs
- System resource utilization
- Detailed test results

### JSON Reports

- Machine-readable results
- Integration with external tools
- Historical data storage
- API consumption

### Console Output

- Real-time progress updates
- Performance alerts
- Summary statistics
- Regression warnings

## Future Enhancements

Planned improvements to the performance testing framework:

- **Distributed Testing**: Run benchmarks across multiple machines
- **Performance Budgets**: Set and enforce performance budgets per feature
- **Automated Optimization**: Suggest performance improvements
- **Visual Profiling**: Interactive performance visualization tools
- **Load Testing**: Simulate realistic user workloads
- **Performance Analytics**: Advanced statistical analysis and predictions
