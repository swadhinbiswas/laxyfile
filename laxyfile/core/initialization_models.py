"""
Initialization Models - Data models for tracking initialization status and component health

This module provides data models for tracking the initialization state and health
of various components in the LaxyFile application.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class ComponentStatus(Enum):
    """Enumeration of component status states"""
    NOT_INITIALIZED = "not_initialized"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    FAILED = "failed"
    RECOVERING = "recovering"


class InitializationPhase(Enum):
    """Enumeration of initialization phases"""
    NOT_STARTED = "not_started"
    CORE_SERVICES = "core_services"
    UI_COMPONENTS = "ui_components"
    INTEGRATION = "integration"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class InitializationState:
    """Tracks overall initialization status and component health"""

    # Phase tracking
    current_phase: InitializationPhase = InitializationPhase.NOT_STARTED
    file_manager_ready: bool = False
    ui_components_ready: bool = False
    integration_complete: bool = False

    # Error tracking
    initialization_errors: List[str] = field(default_factory=list)
    last_initialization_attempt: Optional[datetime] = None
    initialization_start_time: Optional[datetime] = None
    initialization_end_time: Optional[datetime] = None

    # Component status tracking
    component_status: Dict[str, ComponentStatus] = field(default_factory=dict)

    # Performance metrics
    initialization_time: float = 0.0
    total_components: int = 0
    successful_components: int = 0
    failed_components: int = 0

    # Recovery tracking
    recovery_attempts: int = 0
    last_recovery_attempt: Optional[datetime] = None
    recovery_successful: bool = False

    def get_initialization_progress(self) -> float:
        """Get initialization progress as a percentage

        Returns:
            float: Progress percentage (0.0 to 100.0)
        """
        if self.total_components == 0:
            return 0.0

        return (self.successful_components / self.total_components) * 100.0

    def is_initialization_complete(self) -> bool:
        """Check if initialization is complete

        Returns:
            bool: True if initialization is complete and successful
        """
        return (self.current_phase == InitializationPhase.COMPLETED and
                self.file_manager_ready and
                self.ui_components_ready and
                self.integration_complete)

    def has_critical_errors(self) -> bool:
        """Check if there are critical initialization errors

        Returns:
            bool: True if there are critical errors
        """
        critical_keywords = ['file_manager', 'critical', 'fatal', 'core']
        return any(
            any(keyword in error.lower() for keyword in critical_keywords)
            for error in self.initialization_errors
        )

    def get_failed_components(self) -> List[str]:
        """Get list of components that failed to initialize

        Returns:
            List of component names that failed
        """
        return [
            component for component, status in self.component_status.items()
            if status == ComponentStatus.FAILED
        ]

    def get_healthy_components(self) -> List[str]:
        """Get list of healthy components

        Returns:
            List of component names that are healthy
        """
        return [
            component for component, status ionent_status.items()
            if status == ComponentStatus.HEALTHY
        ]

    def add_error(self, error_message: str) -> None:
        """Add an initialization error

        Args:
            error_message: Error message to add
        """
        self.initialization_errors.append(error_message)

        # Update failed components count
        if not any('recovery' in error_message.lower() for _ in [None]):
            self.failed_components += 1

    def set_component_status(self, component: str, status: ComponentStatus) -> None:
        """Set the status of a component

        Args:
            component: Component name
            status: New status
        """
        old_status = self.component_status.get(component)
        self.component_status[component] = status

        # Update counters
        if old_status != status:
            if status == ComponentStatus.HEALTHY:
                if old_status != ComponentStatus.HEALTHY:
                    self.successful_components += 1
                if old_status == ComponentStatus.FAILED:
                    self.failed_components -= 1
            elif status == ComponentStatus.FAILED:
                if old_status != ComponentStatus.FAILED:
                    self.failed_components += 1
                if old_status == ComponentStatus.HEALTHY:
                    self.successful_components -= 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization

        Returns:
            Dict representation of the initialization state
        """
        return {
            'current_phase': self.current_phase.value,
            'file_manager_ready': self.file_manager_ready,
            'ui_components_ready': self.ui_components_ready,
            'integration_complete': self.integration_complete,
            'initialization_errors': self.initialization_errors,
            'last_initialization_attempt': self.last_initialization_attempt.isoformat() if self.last_initialization_attempt else None,
            'initialization_time': self.initialization_time,
            'total_components': self.total_components,
            'successful_components': self.successful_components,
            'failed_components': self.failed_components,
            'progress_percentage': self.get_initialization_progress(),
            'is_complete': self.is_initialization_complete(),
            'has_critical_errors': self.has_critical_errors(),
            'component_status': {k: v.value for k, v in self.component_status.items()},
            'recovery_attempts': self.recovery_attempts,
            'recovery_successful': self.recovery_successful
        }


@dataclass
class ComponentHealth:
    """Tracks individual component health status and metrics"""

    # Basic information
    component_name: str
    status: ComponentStatus = ComponentStatus.NOT_INITIALIZED
    is_healthy: bool = False

    # Timing information
    last_check: datetime = field(default_factory=datetime.now)
    initialization_time: float = 0.0
    last_successful_operation: Optional[datetime] = None
    last_failed_operation: Optional[datetime] = None

    # Error tracking
    error_message: Optional[str] = None
    error_count: int = 0
    last_error_time: Optional[datetime] = None
    error_history: List[Dict[str, Any]] = field(default_factory=list)

    # Dependency tracking
    dependency_status: Dict[str, bool] = field(default_factory=dict)
    required_dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)

    # Performance metrics
    average_response_time: float = 0.0
    operation_count: int = 0
    success_rate: float = 100.0

    # Recovery tracking
    recovery_attempts: int = 0
    last_recovery_attempt: Optional[datetime] = None
    recovery_successful: bool = False

    def update_health_status(self) -> None:
        """Update the health status based on current metrics"""
        try:
            # Check if all required dependencies are available
            all_deps_available = all(
                self.dependency_status.get(dep, False)
                for dep in self.required_dependencies
            )

            # Determine health based on various factors
            if self.status == ComponentStatus.FAILED:
                self.is_healthy = False
            elif self.status == ComponentStatus.NOT_INITIALIZED:
                self.is_healthy = False
            elif not all_deps_available:
                self.is_healthy = False
            elif self.error_count > 10:  # Too many errors
                self.is_healthy = False
            elif self.success_rate < 50.0:  # Low success rate
                self.is_healthy = False
            else:
                self.is_healthy = True
                self.status = ComponentStatus.HEALTHY

            self.last_check = datetime.now()

        except Exception as e:
            self.is_healthy = False
            self.error_message = f"Health check failed: {e}"

    def record_operation(self, success: bool, response_time: float = 0.0,
                        error_message: Optional[str] = None) -> None:
        """Record the result of an operation

        Args:
            success: Whether the operation was successful
            response_time: Time taken for the operation
            error_message: Error message if operation failed
        """
        self.operation_count += 1

        if success:
            self.last_successful_operation = datetime.now()

            # Update average response time
            if self.operation_count == 1:
                self.average_response_time = response_time
            else:
                self.average_response_time = (
                    (self.average_response_time * (self.operation_count - 1) + response_time) /
                    self.operation_count
                )
        else:
            self.error_count += 1
            self.last_failed_operation = datetime.now()
            self.last_error_time = datetime.now()

            if error_message:
                self.error_message = error_message
                self.error_history.append({
                    'timestamp': datetime.now(),
                    'error': error_message,
                    'operation_count': self.operation_count
                })

                # Limit error history size
                if len(self.error_history) > 50:
                    self.error_history = self.error_history[-50:]

        # Update success rate
        successful_operations = self.operation_count - self.error_count
        self.success_rate = (successful_operations / self.operation_count) * 100.0

        # Update health status
        self.update_health_status()

    def record_dependency_status(self, dependency: str, available: bool) -> None:
        """Record the status of a dependency

        Args:
            dependency: Name of the dependency
            available: Whether the dependency is available
        """
        self.dependency_status[dependency] = available
        self.update_health_status()

    def get_dependency_health(self) -> Dict[str, Any]:
        """Get detailed dependency health information

        Returns:
            Dict containing dependency health information
        """
        return {
            'required_dependencies': {
                dep: self.dependency_status.get(dep, False)
                for dep in self.required_dependencies
            },
            'optional_dependencies': {
                dep: self.dependency_status.get(dep, False)
                for dep in self.optional_dependencies
            },
            'all_required_available': all(
                self.dependency_status.get(dep, False)
                for dep in self.required_dependencies
            ),
            'missing_required': [
                dep for dep in self.required_dependencies
                if not self.dependency_status.get(dep, False)
            ]
        }

    def attempt_recovery(self) -> bool:
        """Attempt to recover the component

        Returns:
            bool: True if recovery was successful
        """
        self.recovery_attempts += 1
        self.last_recovery_attempt = datetime.now()

        try:
            # Basic recovery logic - reset error state
            if self.error_count > 0:
                self.error_count = max(0, self.error_count - 5)  # Reduce error count
                self.error_message = None

                # Update status
                if self.error_count == 0:
                    self.status = ComponentStatus.HEALTHY
                    self.recovery_successful = True
                    return True

            return False

        except Exception as e:
            self.error_message = f"Recovery failed: {e}"
            self.recovery_successful = False
            return False

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for the component

        Returns:
            Dict containing performance metrics
        """
        return {
            'operation_count': self.operation_count,
            'error_count': self.error_count,
            'success_rate': self.success_rate,
            'average_response_time': self.average_response_time,
            'initialization_time': self.initialization_time,
            'last_successful_operation': self.last_successful_operation,
            'last_failed_operation': self.last_failed_operation,
            'recovery_attempts': self.recovery_attempts,
            'recovery_successful': self.recovery_successful
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization

        Returns:
            Dict representation of the component health
        """
        return {
            'component_name': self.component_name,
            'status': self.status.value,
            'is_healthy': self.is_healthy,
            'last_check': self.last_check.isoformat(),
            'initialization_time': self.initialization_time,
            'error_message': self.error_message,
            'error_count': self.error_count,
            'dependency_health': self.get_dependency_health(),
            'performance_metrics': self.get_performance_metrics(),
            'recent_errors': self.error_history[-5:] if self.error_history else []
        }


@dataclass
class SystemHealth:
    """Overall system health status combining all components"""

    # Overall status
    is_healthy: bool = False
    health_score: float = 0.0  # 0-100 score
    last_health_check: datetime = field(default_factory=datetime.now)

    # Component tracking
    total_components: int = 0
    healthy_components: int = 0
    unhealthy_components: int = 0
    failed_components: int = 0

    # Critical systems
    file_manager_healthy: bool = False
    ui_system_healthy: bool = False
    core_services_healthy: bool = False

    # Performance metrics
    average_response_time: float = 0.0
    total_operations: int = 0
    total_errors: int = 0
    overall_success_rate: float = 100.0

    def update_from_components(self, components: Dict[str, ComponentHealth]) -> None:
        """Update system health from component health data

        Args:
            components: Dictionary of component health objects
        """
        self.total_components = len(components)
        self.healthy_components = sum(1 for c in components.values() if c.is_healthy)
        self.unhealthy_components = self.total_components - self.healthy_components
        self.failed_components = sum(
            1 for c in components.values()
            if c.status == ComponentStatus.FAILED
        )

        # Check critical systems
        self.file_manager_healthy = components.get('file_manager', ComponentHealth('file_manager')).is_healthy
        self.ui_system_healthy = all(
            components.get(comp, ComponentHealth(comp)).is_healthy
            for comp in ['theme_manager', 'panel_manager', 'media_viewer']
        )
        self.core_services_healthy = all(
            components.get(comp, ComponentHealth(comp)).is_healthy
            for comp in ['file_manager', 'config']
        )

        # Calculate health score
        if self.total_components > 0:
            base_score = (self.healthy_components / self.total_components) * 100

            # Apply penalties for critical system failures
            if not self.file_manager_healthy:
                base_score *= 0.5  # 50% penalty for file manager issues
            if not self.core_services_healthy:
                base_score *= 0.7  # 30% penalty for core service issues

            self.health_score = max(0.0, min(100.0, base_score))
        else:
            self.health_score = 0.0

        # Overall health determination
        self.is_healthy = (
            self.health_score >= 80.0 and
            self.file_manager_healthy and
            self.core_services_healthy
        )

        # Update performance metrics
        if components:
            total_ops = sum(c.operation_count for c in components.values())
            total_errors = sum(c.error_count for c in components.values())

            self.total_operations = total_ops
            self.total_errors = total_errors

            if total_ops > 0:
                self.overall_success_rate = ((total_ops - total_errors) / total_ops) * 100.0
                self.average_response_time = sum(
                    c.average_response_time * c.operation_count for c in components.values()
                ) / total_ops

        self.last_health_check = datetime.now()

    def get_health_summary(self) -> Dict[str, Any]:
        """Get a summary of system health

        Returns:
            Dict containing health summary
        """
        return {
            'is_healthy': self.is_healthy,
            'health_score': self.health_score,
            'last_check': self.last_health_check.isoformat(),
            'component_summary': {
                'total': self.total_components,
                'healthy': self.healthy_components,
                'unhealthy': self.unhealthy_components,
                'failed': self.failed_components
            },
            'critical_systems': {
                'file_manager': self.file_manager_healthy,
                'ui_system': self.ui_system_healthy,
                'core_services': self.core_services_healthy
            },
            'performance': {
                'total_operations': self.total_operations,
                'total_errors': self.total_errors,
                'success_rate': self.overall_success_rate,
                'average_response_time': self.average_response_time
            }
        }