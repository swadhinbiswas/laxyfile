#!/usr/bin/env python3
"""
Performance monitoring and regression detection

Continuous performance monitoring system that tracks performance
metrics over time and detects regressions automatically.
"""

import sys
import time
import json
import psutil
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.performance.benchmark_config import BenchmarkConfig, PerformanceTracker


@dataclass
class PerformanceMetric:
    """Represents a performance metric measurement"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    context: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


@dataclass
class SystemMetrics:
    """System resource metrics"""
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        return result


class PerformanceMonitor:
    """Real-time performance monitoring system"""

    def __init__(self, config: Optional[BenchmarkConfig] = None):
        self.config = config or BenchmarkConfig()
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.system_metrics: deque = deque(maxlen=1000)
        self.alerts: List[Dict[str, Any]] = []
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Performance thresholds
        self.thresholds = {
            'cpu_percent': 80.0,
            'memory_percent': 85.0,
            'response_time_ms': 1000.0,
            'error_rate': 0.05,  # 5%
            'cache_hit_ratio': 0.8  # 80%
        }

        # Baseline metrics for comparison
        self.baselines: Dict[str, float] = {}

        # Initialize system monitoring
        self._last_disk_io = psutil.disk_io_counters()
        self._last_network_io = psutil.net_io_counters()
        self._last_check_time = time.time()

    def start_monitoring(self, interval: float = 1.0):
        """Start continuous performance monitoring"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        print(f"Performance monitoring started (interval: {interval}s)")

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)
        print("Performance monitoring stopped")

    def _monitor_loop(self, interval: float):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self.system_metrics.append(system_metrics)

                # Check for threshold violations
                self._check_thresholds(system_metrics)

                time.sleep(interval)

            except Exception as e:
                print(f"Error in monitoring loop: {e}")
                time.sleep(interval)

    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics"""
        current_time = time.time()
        time_delta = current_time - self._last_check_time

        # CPU and memory
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        # Disk I/O
        current_disk_io = psutil.disk_io_counters()
        disk_read_mb = 0
        disk_write_mb = 0

        if self._last_disk_io and time_delta > 0:
            disk_read_mb = (current_disk_io.read_bytes - self._last_disk_io.read_bytes) / (1024 * 1024) / time_delta
            disk_write_mb = (current_disk_io.write_bytes - self._last_disk_io.write_bytes) / (1024 * 1024) / time_delta

        # Network I/O
        current_network_io = psutil.net_io_counters()
        network_sent_mb = 0
        network_recv_mb = 0

        if self._last_network_io and time_delta > 0:
            network_sent_mb = (current_network_io.bytes_sent - self._last_network_io.bytes_sent) / (1024 * 1024) / time_delta
            network_recv_mb = (current_network_io.bytes_recv - self._last_network_io.bytes_recv) / (1024 * 1024) / time_delta

        # Update last values
        self._last_disk_io = current_disk_io
        self._last_network_io = current_network_io
        self._last_check_time = current_time

        return SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            memory_used_mb=memory.used / (1024 * 1024),
            disk_io_read_mb=disk_read_mb,
            disk_io_write_mb=disk_write_mb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            timestamp=datetime.now()
        )

    def _check_thresholds(self, metrics: SystemMetrics):
        """Check if metrics exceed thresholds"""
        checks = [
            ('cpu_percent', metrics.cpu_percent, 'CPU usage'),
            ('memory_percent', metrics.memory_percent, 'Memory usage')
        ]

        for threshold_name, value, description in checks:
            threshold = self.thresholds.get(threshold_name)
            if threshold and value > threshold:
                self._create_alert(
                    'threshold_exceeded',
                    f"{description} exceeded threshold: {value:.1f}% > {threshold:.1f}%",
                    {'metric': threshold_name, 'value': value, 'threshold': threshold}
                )

    def _create_alert(self, alert_type: str, message: str, context: Dict[str, Any]):
        """Create performance alert"""
        alert = {
            'type': alert_type,
            'message': message,
            'context': context,
            'timestamp': datetime.now().isoformat()
        }

        self.alerts.append(alert)
        print(f"🚨 PERFORMANCE ALERT: {message}")

        # Keep only recent alerts
        if len(self.alerts) > 100:
            self.alerts = self.alerts[-100:]

    def record_metric(self, name: str, value: float, unit: str = "", context: Optional[Dict[str, Any]] = None):
        """Record a custom performance metric"""
        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            context=context or {}
        )

        self.metrics[name].append(metric)

        # Check for regression
        self._check_regression(name, value)

    def _check_regression(self, metric_name: str, current_value: float):
        """Check for performance regression"""
        if metric_name not in self.baselines:
            # Establish baseline from recent measurements
            recent_metrics = list(self.metrics[metric_name])[-10:]  # Last 10 measurements
            if len(recent_metrics) >= 5:
                baseline = sum(m.value for m in recent_metrics) / len(recent_metrics)
                self.baselines[metric_name] = baseline
            return

        baseline = self.baselines[metric_name]
        regression_threshold = self.config.performance_regression_threshold

        # Check for regression (higher values are worse for most metrics)
        if current_value > baseline * (1 + regression_threshold):
            regression_percent = ((current_value - baseline) / baseline) * 100
            self._create_alert(
                'performance_regression',
                f"Performance regression detected in {metric_name}: {regression_percent:.1f}% worse than baseline",
                {
                    'metric': metric_name,
                    'current_value': current_value,
                    'baseline': baseline,
                    'regression_percent': regression_percent
                }
            )

    def get_metric_stats(self, metric_name: str, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get statistics for a metric over specified duration"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)

        if metric_name not in self.metrics:
            return {'error': f'Metric {metric_name} not found'}

        recent_metrics = [
            m for m in self.metrics[metric_name]
            if m.timestamp >= cutoff_time
        ]

        if not recent_metrics:
            return {'error': f'No recent data for {metric_name}'}

        values = [m.value for m in recent_metrics]

        return {
            'count': len(values),
            'min': min(values),
            'max': max(values),
            'mean': sum(values) / len(values),
            'median': sorted(values)[len(values) // 2],
            'latest': values[-1],
            'trend': 'improving' if len(values) > 1 and values[-1] < values[0] else 'degrading'
        }

    def get_system_stats(self, duration_minutes: int = 60) -> Dict[str, Any]:
        """Get system resource statistics"""
        cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)

        recent_metrics = [
            m for m in self.system_metrics
            if m.timestamp >= cutoff_time
        ]

        if not recent_metrics:
            return {'error': 'No recent system metrics'}

        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]

        return {
            'cpu': {
                'min': min(cpu_values),
                'max': max(cpu_values),
                'mean': sum(cpu_values) / len(cpu_values),
                'current': cpu_values[-1]
            },
            'memory': {
                'min': min(memory_values),
                'max': max(memory_values),
                'mean': sum(memory_values) / len(memory_values),
                'current': memory_values[-1]
            },
            'sample_count': len(recent_metrics)
        }

    def generate_report(self) -> str:
        """Generate performance monitoring report"""
        report_lines = [
            "# Performance Monitoring Report",
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            ""
        ]

        # System stats
        system_stats = self.get_system_stats()
        if 'error' not in system_stats:
            report_lines.extend([
                "## System Resources (Last Hour)",
                f"CPU: {system_stats['cpu']['current']:.1f}% (avg: {system_stats['cpu']['mean']:.1f}%)",
                f"Memory: {system_stats['memory']['current']:.1f}% (avg: {system_stats['memory']['mean']:.1f}%)",
                ""
            ])

        # Custom metrics
        if self.metrics:
            report_lines.append("## Custom Metrics")
            for metric_name in sorted(self.metrics.keys()):
                stats = self.get_metric_stats(metric_name)
                if 'error' not in stats:
                    report_lines.append(
                        f"- {metric_name}: {stats['latest']:.3f} "
                        f"(avg: {stats['mean']:.3f}, trend: {stats['trend']})"
                    )
            report_lines.append("")

        # Recent alerts
        if self.alerts:
            recent_alerts = [a for a in self.alerts[-10:]]  # Last 10 alerts
            report_lines.extend([
                "## Recent Alerts",
                *[f"- {alert['message']} ({alert['timestamp']})" for alert in recent_alerts],
                ""
            ])

        return "\n".join(report_lines)

    def save_data(self, output_file: Path):
        """Save monitoring data to file"""
        data = {
            'metrics': {
                name: [m.to_dict() for m in metrics]
                for name, metrics in self.metrics.items()
            },
            'system_metrics': [m.to_dict() for m in self.system_metrics],
            'alerts': self.alerts,
            'baselines': self.baselines,
            'thresholds': self.thresholds,
            'export_timestamp': datetime.now().isoformat()
        }

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Monitoring data saved to {output_file}")

    def load_data(self, input_file: Path):
        """Load monitoring data from file"""
        if not input_file.exists():
            print(f"File {input_file} does not exist")
            return

        with open(input_file, 'r') as f:
            data = json.load(f)

        # Load metrics
        for name, metric_list in data.get('metrics', {}).items():
            self.metrics[name] = deque(maxlen=1000)
            for metric_data in metric_list:
                metric_data['timestamp'] = datetime.fromisoformat(metric_data['timestamp'])
                metric = PerformanceMetric(**metric_data)
                self.metrics[name].append(metric)

        # Load system metrics
        self.system_metrics = deque(maxlen=1000)
        for system_data in data.get('system_metrics', []):
            system_data['timestamp'] = datetime.fromisoformat(system_data['timestamp'])
            system_metric = SystemMetrics(**system_data)
            self.system_metrics.append(system_metric)

        # Load other data
        self.alerts = data.get('alerts', [])
        self.baselines = data.get('baselines', {})
        self.thresholds.update(data.get('thresholds', {}))

        print(f"Monitoring data loaded from {input_file}")


class PerformanceProfiler:
    """Context manager for profiling code blocks"""

    def __init__(self, monitor: PerformanceMonitor, operation_name: str, context: Optional[Dict[str, Any]] = None):
        self.monitor = monitor
        self.operation_name = operation_name
        self.context = context or {}
        self.start_time = None
        self.start_memory = None

    def __enter__(self):
        self.start_time = time.time()
        process = psutil.Process()
        self.start_memory = process.memory_info().rss
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        process = psutil.Process()
        end_memory = process.memory_info().rss

        # Record timing
        duration_ms = (end_time - self.start_time) * 1000
        self.monitor.record_metric(
            f"{self.operation_name}_duration_ms",
            duration_ms,
            "ms",
            self.context
        )

        # Record memory usage
        memory_increase_mb = (end_memory - self.start_memory) / (1024 * 1024)
        self.monitor.record_metric(
            f"{self.operation_name}_memory_mb",
            memory_increase_mb,
            "MB",
            self.context
        )

        # Record success/failure
        success = exc_type is None
        self.monitor.record_metric(
            f"{self.operation_name}_success_rate",
            1.0 if success else 0.0,
            "ratio",
            {**self.context, 'success': success}
        )


def main():
    """Main entry point for performance monitoring"""
    import argparse

    parser = argparse.ArgumentParser(description="LaxyFile Performance Monitor")
    parser.add_argument(
        "--duration",
        type=int,
        default=60,
        help="Monitoring duration in seconds (0 for continuous)"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Monitoring interval in seconds"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for monitoring data"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate report at end"
    )

    args = parser.parse_args()

    # Initialize monitor
    monitor = PerformanceMonitor()

    try:
        # Start monitoring
        monitor.start_monitoring(args.interval)

        if args.duration > 0:
            print(f"Monitoring for {args.duration} seconds...")
            time.sleep(args.duration)
        else:
            print("Monitoring continuously (Ctrl+C to stop)...")
            while True:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping monitoring...")

    finally:
        # Stop monitoring
        monitor.stop_monitoring()

        # Generate report
        if args.report:
            print("\n" + monitor.generate_report())

        # Save data
        if args.output:
            monitor.save_data(args.output)


if __name__ == "__main__":
    main()