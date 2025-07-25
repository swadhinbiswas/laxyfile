#!/usr/bin/env python3
"""
LaxyFile - Advanced File Manager

A modern, AI-powered file manager with SuperFile-inspired UI and comprehensive features.
This is the integrated version that uses the component integration system.
"""

import asyncio
import sys
import signal
from pathlib import Path
from typing import Optional

from .core.config import Config
from .integration.component_integration import ComponentIntegrator, initialize_integration
from .utils.logging_system import initialize_logging, get_logger, LogCategory
from .utils.performance_logger import PerformanceLogger


class LaxyFileApplication:
    """
    Main LaxyFile application class that manages the complete application lifecycle
    """

    def __init__(self, config: Optional[Config] = None):
        """Initialize the LaxyFile application"""
        # Initialize configuration
        self.config = config or Config()

        # Initialize logging system
        self.logging_system = initialize_logging(self.config)
        self.logger = get_logger('application', LogCategory.SYSTEM)

        # Initialize component integrator
        self.integrator = initialize_integration(self.config)

        # Application state
        self.running = False
        self.shutdown_requested = False

        # Performance monitoring
        self.performance_logger = PerformanceLogger(self.config)

        self.logger.info("LaxyFile application initialized")

    async def initialize(self) -> bool:
        """Initialize all application components"""
        self.logger.info("Starting LaxyFile application initialization")

        try:
            # Initialize all components through the integrator
            success = await self.integrator.initialize_all_components()

            if not success:
                self.logger.error("Failed to initialize application components")
                return False

            # Setup signal handlers for graceful shutdown
            self._setup_signal_handlers()

            # Test component interactions
            self.logger.info("Testing component interactions")
            test_results = await self.integrator.test_component_interactions()

            failed_tests = [test for test, result in test_results.items() if not result]
            if failed_tests:
                self.logger.warning(f"Some component interaction tests failed: {failed_tests}")
            else:
                self.logger.info("All component interaction tests passed")

            self.logger.info("LaxyFile application initialization complete")
            return True

        except Exception as e:
            self.logger.error(f"Application initialization failed: {e}", exc_info=True)
            return False

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, initiating shutdown")
            self.shutdown_requested = True

            # Create shutdown task
            if self.running:
                asyncio.create_task(self.shutdown())

        # Setup handlers for common signals
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        # On Unix systems, also handle SIGHUP
        if hasattr(signal, 'SIGHUP'):
            signal.signal(signal.SIGHUP, signal_handler)

    async def run(self):
        """Run the main application loop"""
        if not await self.initialize():
            self.logger.error("Failed to initialize application")
            return False

        self.running = True
        self.logger.info("Starting LaxyFile application")

        try:
            # Get the UI manager from the integrator
            ui_manager = self.integrator.get_component('ui_manager')

            if ui_manager is None:
                self.logger.error("UI manager not available")
                return False

            # Start the UI
            await ui_manager.run()

        except KeyboardInterrupt:
            self.logger.info("Application interrupted by user")
        except Exception as e:
            self.logger.error(f"Application error: {e}", exc_info=True)
        finally:
            self.running = False
            await self.shutdown()

        return True

    async def set_current_directory(self, directory: Path):
        """Set the current working directory"""
        file_manager = self.integrator.get_component('file_manager')
        if file_manager and hasattr(file_manager, 'set_current_directory'):
            await file_manager.set_current_directory(directory)

    async def shutdown(self):
        """Shutdown the application gracefully"""
        if self.shutdown_requested:
            return  # Already shutting down

        self.shutdown_requested = True
        self.logger.info("Shutting down LaxyFile application")

        try:
            # Shutdown component integrator
            await self.integrator.shutdown()

            # Stop performance monitoring
            if hasattr(self.performance_logger, 'stop_system_monitoring'):
                self.performance_logger.stop_system_monitoring()

            # Log final statistics
            if hasattr(self.integrator, 'logging_system'):
                stats = self.integrator.logging_system.get_log_statistics()
                self.logger.info(f"Final application statistics: {stats}")

            self.logger.info("LaxyFile application shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}", exc_info=True)

    def get_component(self, name: str):
        """Get a component by name"""
        return self.integrator.get_component(name)

    def is_healthy(self) -> bool:
        """Check if the application is healthy"""
        return self.integrator.is_healthy()

    def get_status(self) -> dict:
        """Get application status information"""
        return {
            'running': self.running,
            'shutdown_requested': self.shutdown_requested,
            'healthy': self.is_healthy(),
            'components': self.integrator.get_all_component_status(),
            'startup_time': getattr(self.integrator, 'startup_time', None)
        }


async def main():
    """Main entry point for LaxyFile"""
    try:
        # Create and run the application
        app = LaxyFileApplication()
        success = await app.run()

        if not success:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


def run_laxyfile():
    """Entry point for console script"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    run_laxyfile()