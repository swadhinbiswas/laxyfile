"""
Performance Logging and Monitoring System

This module provides comprehensive performance monitoring and logging
capabilities for LaxyFile, including metrics collection, analysis,
and reporting.
"""

import time
import threading
import psutil
import gc
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque
import json


class MetricType(Enum):
    """Types of performance metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class MetricUnit(Enum):
    """Units for performance metrics"""
    MILLISECONDS = "ms"
    SECONDS = "s"
    BYTES = "bytes"
    MEGABYTES = "MB"
    PERCENT = "percent"
    COUNT = "count"
    OPERATIONS_PER_SECOND = "ops/s"


@dataclass
class MetricValue:
    """Represents a single metric measurement"""
    timestamp: datetime
    value: float
    unit: MetricUnit
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceMetric:
    """Performance metric definition and storage"""
    name: str
    metric_type: MetricType
    unit: MetricUnit
    description: str
    values: deque = field(default_factory=lambda: deque(maxlen=1000))
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class SystemMetrics:
    """System-level performance metrics"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    disk_free_gb: float
    process_memory_mb: float
    process_cpu_percent: float
    thread_count: int
    file_descriptors: int


@dataclass
class PerformanceReport:
    """Performance analysis report"""
    start_time: datetime
    end_time: datetime
    duration: timedelta
    metrics_summary: Dict[str, Dict[str, float]]
    system_summary: Dict[str, float]
    recommendations: List[str]
    alerts: List[str]


class PerformanceTimer:
    """Context manager for timing operations"""

    def __init__(self, performance_logger: 'PerformanceLogger', metric_name: str,
                 tags: Optional[Dict[str, str]] = None):
        self.performance_logger = performance_logger
        self.metric_name = metric_name
        self.tags = tags or {}
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time is not None:
            duration_ms = (time.time() - self.start_time) * 1000
            self.performance_logger.record_metric(
                self.metric_name,
                duration_ms,
                MetricUnit.MILLISECONDS,
                "timer",
                self.tags
            )


class PerformanceLogger:
    """Main performance logging and monitoring system"""

    def __init__(self, config):
        self.config = config
        self.metrics: Dict[str, PerformanceMetric] = {}
        self.system_metrics: deque = deque(maxlen=1000)
        self.lock = threading.Lock()

        # Monitoring configuration
        self.monitoring_enabled = config.get('performance.monitoring_enabled', True)
        self.system_monitoring_interval = config.get('performance.system_interval', 30)
        self.alert_thresholds = config.get('performance.alert_thresholds', {})

        # Background monitoring
        self.monitoring_thread = None
        self.monitoring_active = False

        # Performance analysis
        self.analysis_callbacks: List[Callable] = []

        # Start system monitoring if enabled
        if self.monitoring_enabled:
            self.start_system_monitoring()

    def record_metric(self, name: str, value: float, unit: MetricUnit,
                     metric_type: str = "gauge", tags: Optional[Dict[str, str]] = None):
        """Record a performance metric"""
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = PerformanceMetric(
                    name=name,
                    metric_type=MetricType(metric_type),
                    unit=unit,
                    description=f"Performance metric: {name}",
                    tags=tags or {}
                )

            metric_value = MetricValue(
                timestamp=datetime.now(),
                value=value,
                unit=unit,
                tags=tags or {}
            )

            self.metrics[name].values.append(metric_value)

            # Check for alerts
            self._check_metric_alerts(name, value)

    def timer(self, metric_name: str, tags: Optional[Dict[str, str]] = None) -> PerformanceTimer:
        """Create a performance timer context manager"""
        return PerformanceTimer(self, metric_name, tags)

    def increment_counter(self, name: str, value: float = 1.0,
                         tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric"""
        self.record_metric(name, value, MetricUnit.COUNT, "counter", tags)

    def set_gauge(self, name: str, value: float, unit: MetricUnit,
                  tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric value"""
        self.record_metric(name, value, unit, "gauge", tags)

    def start_system_monitoring(self):
        """Start background system monitoring"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            return

        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._system_monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()

    def stop_system_monitoring(self):
        """Stop background system monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)

    def _system_monitoring_loop(self):
        """Background system monitoring loop"""
        while self.monitoring_active:
            try:
                self._collect_system_metrics()
                time.sleep(self.system_monitoring_interval)
            except Exception as e:
                # Log error but continue monitoring
                print(f"System monitoring error: {e}")
                time.sleep(self.system_monitoring_interval)

    def _collect_system_metrics(self):
        """Collect system performance metrics"""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # Get process metrics
            process = psutil.Process()
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent()

            # Create system metrics entry
            system_metrics = SystemMetrics(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                disk_usage_percent=disk.percent,
                disk_free_gb=disk.free / (1024 * 1024 * 1024),
                process_memory_mb=process_memory.rss / (1024 * 1024),
                process_cpu_percent=process_cpu,
                thread_count=process.num_threads(),
                file_descriptors=process.num_fds() if hasattr(process, 'num_fds') else 0
            )

            with self.lock:
                self.system_metrics.append(system_metrics)

            # Record individual metrics
            self.set_gauge("system_cpu_percent", cpu_percent, MetricUnit.PERCENT)
            self.set_gauge("system_memory_percent", memory.percent, MetricUnit.PERCENT)
            self.set_gauge("process_memory_mb", system_metrics.process_memory_mb, MetricUnit.MEGABYTES)
            self.set_gauge("process_cpu_percent", process_cpu, MetricUnit.PERCENT)

            # Check system alerts
            self._check_system_alerts(system_metrics)

        except Exception as e:
            print(f"Error collecting system metrics: {e}")

    def _check_metric_alerts(self, metric_name: str, value: float):
        """Check if metric value triggers any alerts"""
        thresholds = self.alert_thresholds.get(metric_name, {})

        if 'max' in thresholds and value > thresholds['max']:
            alert = f"Metric {metric_name} exceeded maximum threshold: {value} > {thresholds['max']}"
            self._trigger_alert(alert)

        if 'min' in thresholds and value < thresholds['min']:
            alert = f"Metric {metric_name} below minimum threshold: {value} < {thresholds['min']}"
            self._trigger_alert(alert)

    def _check_system_alerts(self, metrics: SystemMetrics):
        """Check system metrics for alert conditions"""
        # CPU usage alert
        if metrics.cpu_percent > 90:
            self._trigger_alert(f"High CPU usage: {metrics.cpu_percent:.1f}%")

        # Memory usage alert
        if metrics.memory_percent > 90:
            self._trigger_(f"High memory usage: {metrics.memory_percent:.1f}%")

        # Disk usage alert
        if metrics.disk_usage_percent > 95:
            self._trigger_alert(f"High disk usage: {metrics.disk_usage_percent:.1f}%")

        # Process memory alert
        if metrics.process_memory_mb > 1000:  # 1GB
            self._trigger_alert(f"High process memory usage: {metrics.process_memory_mb:.1f}MB")

    def _trigger_alert(self, message: str):
        """Trigger a performance alert"""
        print(f"PERFORMANCE ALERT: {message}")
        # Could also log to file, send notifications, etc.

    def get_metric_summary(self, metric_name: str,
                          time_window: Optional[timedelta] = None) -> Dict[str, float]:
        """Get summary statistics for a metric"""
        with self.lock:
            if metric_name not in self.metrics:
                return {}

            metric = self.metrics[metric_name]
            values = list(metric.values)

        # Filter by time window if specified
        if time_window:
            cutoff_time = datetime.now() - time_window
            values = [v for v in values if v.timestamp >= cutoff_time]

        if not values:
            return {}

        numeric_values = [v.value for v in values]

        return {
            'count': len(numeric_values),
            'min': min(numeric_values),
            'max': max(numeric_values),
            'avg': sum(numeric_values) / len(numeric_values),
            'latest': numeric_values[-1] if numeric_values else 0,
            'unit': values[0].unit.value
        }

    def get_all_metrics_summary(self, time_window: Optional[timedelta] = None) -> Dict[str, Dict[str, float]]:
        """Get summary for all metrics"""
        summary = {}
        with self.lock:
            metric_names = list(self.metrics.keys())

        for name in metric_names:
            summary[name] = self.get_metric_summary(name, time_window)

        return summary

    def get_system_metrics_summary(self, time_window: Optional[timedelta] = None) -> Dict[str, float]:
        """Get summary of system metrics"""
        with self.lock:
            metrics = list(self.system_metrics)

        # Filter by time window if specified
        if time_window:
            cutoff_time = datetime.now() - time_window
            metrics = [m for m in metrics if m.timestamp >= cutoff_time]

        if not metrics:
            return {}

        return {
            'avg_cpu_percent': sum(m.cpu_percent for m in metrics) / len(metrics),
            'max_cpu_percent': max(m.cpu_percent for m in metrics),
            'avg_memory_percent': sum(m.memory_percent for m in metrics) / len(metrics),
            'max_memory_percent': max(m.memory_percent for m in metrics),
            'avg_process_memory_mb': sum(m.process_memory_mb for m in metrics) / len(metrics),
            'max_process_memory_mb': max(m.process_memory_mb for m in metrics),
            'latest_disk_free_gb': metrics[-1].disk_free_gb if metrics else 0,
            'avg_thread_count': sum(m.thread_count for m in metrics) / len(metrics)
        }

    def generate_performance_report(self, time_window: Optional[timedelta] = None) -> PerformanceReport:
        """Generate a comprehensive performance report"""
        end_time = datetime.now()
        start_time = end_time - (time_window or timedelta(hours=1))

        # Get metrics summary
        metrics_summary = self.get_all_metrics_summary(time_window)
        system_summary = self.get_system_metrics_summary(time_window)

        # Generate recommendations
        recommendations = self._generate_recommendations(metrics_summary, system_summary)

        # Generate alerts
        alerts = self._generate_alerts(metrics_summary, system_summary)

        return PerformanceReport(
            start_time=start_time,
            end_time=end_time,
            duration=end_time - start_time,
            metrics_summary=metrics_summary,
            system_summary=system_summary,
            recommendations=recommendations,
            alerts=alerts
        )

    def _generate_recommendations(self, metrics_summary: Dict, system_summary: Dict) -> List[str]:
        """Generate performance recommendations"""
        recommendations = []

        # Memory recommendations
        if system_summary.get('max_memory_percent', 0) > 80:
            recommendations.append("Consider increasing system memory or optimizing memory usage")

        # CPU recommendations
        if system_summary.get('max_cpu_percent', 0) > 80:
            recommendations.append("High CPU usage detected - consider optimizing CPU-intensive operations")

        # File operation recommendations
        file_op_metrics = {k: v for k, v in metrics_summary.items() if 'file_op' in k}
        if file_op_metrics:
            slow_ops = [k for k, v in file_op_metrics.items() if v.get('avg', 0) > 1000]  # > 1 second
            if slow_ops:
                recommendations.append(f"Slow file operations detected: {', '.join(slow_ops)}")

        return recommendations

    def _generate_alerts(self, metrics_summary: Dict, system_summary: Dict) -> List[str]:
        """Generate performance alerts"""
        alerts = []

        # Critical system alerts
        if system_summary.get('max_memory_percent', 0) > 95:
            alerts.append("CRITICAL: Memory usage exceeded 95%")

        if system_summary.get('max_cpu_percent', 0) > 95:
            alerts.append("CRITICAL: CPU usage exceeded 95%")

        # Process memory alerts
        if system_summary.get('max_process_memory_mb', 0) > 2000:  # 2GB
            alerts.append("WARNING: Process memory usage exceeded 2GB")

        return alerts

    def export_metrics(self, file_path: Path, time_window: Optional[timedelta] = None):
        """Export metrics to a JSON file"""
        report = self.generate_performance_report(time_window)

        export_data = {
            'report': {
                'start_time': report.start_time.isoformat(),
                'end_time': report.end_time.isoformat(),
                'duration_seconds': report.duration.total_seconds(),
                'metrics_summary': report.metrics_summary,
                'system_summary': report.system_summary,
                'recommendations': report.recommendations,
                'alerts': report.alerts
            },
            'raw_metrics': {}
        }

        # Add raw metric data
        with self.lock:
            for name, metric in self.metrics.items():
                values = list(metric.values)
                if time_window:
                    cutoff_time = datetime.now() - time_window
                    values = [v for v in values if v.timestamp >= cutoff_time]

                export_data['raw_metrics'][name] = [
                    {
                        'timestamp': v.timestamp.isoformat(),
                        'value': v.value,
                        'unit': v.unit.value,
                        'tags': v.tags
                    }
                    for v in values
                ]

        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)

    def clear_metrics(self):
        """Clear all stored metrics"""
        with self.lock:
            self.metrics.clear()
            self.system_metrics.clear()

    def register_analysis_callback(self, callback: Callable):
        """Register a callback for performance analysis"""
        self.analysis_callbacks.append(callback)

    def shutdown(self):
        """Shutdown the performance logger"""
        self.stop_system_monitoring()