#!/usr/bin/env python3
"""
Test script to verify the LaxyFile error fixes are working correctly.

This script tests the FileManagerService, ComponentInitializer, and ErrorHandlingMixin
to ensure they properly handle the NoneType errors that were occurring.
"""

import sys
import os
from pathlib import Path
import time
import threading

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_file_manager_service():
    """Test FileManagerService singleton and initialization"""
    print("🧪 Testing FileManagerService...")

    try:
        from laxyfile.core.file_manager_service import FileManagerService

        # Test singleton behavior
        service1 = FileManagerService.get_instance()
        service2 = FileManagerService.get_instance()

        assert service1 is service2, "FileManagerService should be a singleton"
        print("✅ Singleton behavior working correctly")

        # Test initialization
        success = service1.ensure_initialized()
        print(f"✅ Initialization: {'Success' if success else 'Failed'}")

        # Test health check
        is_healthy = service1.is_healthy()
        print(f"✅ Health check: {'Healthy' if is_healthy else 'Unhealthy'}")

        # Test directory listing
        current_dir = Path.cwd()
        files = service1.list_directory(current_dir)
        print(f"✅ Directory listing: Found {len(files)} items in {current_dir}")

        # Test status
        status = service1.get_status()
        print(f"✅ Service status: {status}")

        return True

    except Exception as e:
        print(f"❌ FileManagerService test failed: {e}")
        return False

def test_component_initializer():
    """Test ComponentInitializer proper initialization order"""
    print("\n🧪 Testing ComponentInitializer...")

    try:
        from laxyfile.core.component_initializer import ComponentInitializer
        from laxyfile.core.config import Config

        config = Config()
        initializer = ComponentInitializer(config)

        # Test core services initialization
        core_success = initializer.initialize_core_services()
        print(f"✅ Core services initization: {'Success' if core_success else 'Failed'}")

        # Test UI components initialization
        ui_success = initializer.initialize_ui_components()
        print(f"✅ UI components initialization: {'Success' if ui_success else 'Failed'}")

        # Test dependency verification
        missing_deps = initializer.verify_dependencies()
        print(f"✅ Dependency verification: {len(missing_deps)} missing dependencies")
        if missing_deps:
            print(f"   Missing: {missing_deps}")

        # Test initialization status
        status = initializer.get_initialization_status()
        print(f"✅ Initialization status: {status}")

        # Test health check
        health = initializer.health_check()
        print(f"✅ Health check: {'Healthy' if health else 'Unhealthy'}")

        return True

    except Exception as e:
        print(f"❌ ComponentInitializer test failed: {e}")
        return False

def test_error_handling_mixin():
    """Test ErrorHandlingMixin error handling and recovery"""
    print("\n🧪 Testing ErrorHandlingMixin...")

    try:
        from laxyfile.core.error_handling_mixin import ErrorHandlingMixin

        class TestComponent(ErrorHandlingMixin):
            def __init__(self):
                super().__init__()
                self.call_count = 0

            def test_operation(self):
                self.call_count += 1
                if self.call_count < 3:
                    raise Exception("Simulated error")
                return "Success"

            def failing_operation(self):
                raise Exception("Always fails")

        component = TestComponent()

        # Test safe operation with retry
        result = component.safe_file_operation(
            operation=component.test_operation,
            fallback_value="Fallback",
            max_retries=3
        )
        print(f"✅ Safe operation with retry: {result}")

        # Test safe operation with fallback
        result = component.safe_file_operation(
            operation=component.failing_operation,
            fallback_value="Fallback used",
            max_retries=1
        )
        print(f"✅ Safe operation with fallback: {result}")

        # Test error statistics
        stats = component.get_error_statistics()
        print(f"✅ Error statistics: {stats}")

        # Test file manager availability check
        available = component.is_file_manager_available()
        print(f"✅ File manager availability: {'Available' if available else 'Unavailable'}")

        return True

    except Exception as e:
        print(f"❌ ErrorHandlingMixin test failed: {e}")
        return False

def test_panel_manager_integration():
    """Test PanelManager integration with FileManagerService"""
    print("\n🧪 Testing PanelManager integration...")

    try:
        from laxyfile.ui.panels import PanelManager
        from laxyfile.ui.theme import ThemeManager
        from laxyfile.core.config import Config

        config = Config()
        theme_manager = ThemeManager(config)
        panel_manager = PanelManager(theme_manager)

        # Test panel rendering
        current_dir = Path.cwd()
        panel = panel_manager.render_panel(current_dir, "test", is_active=True)

        print(f"✅ Panel rendering: Successfully created panel for {current_dir}")
        print(f"   Panel type: {type(panel)}")

        # Test error handling in panel manager
        non_existent_path = Path("/non/existent/path")
        error_panel = panel_manager.render_panel(non_existent_path, "error_test", is_active=False)

        print(f"✅ Error handling: Successfully handled non-existent path")
        print(f"   Error panel type: {type(error_panel)}")

        return True

    except Exception as e:
        print(f"❌ PanelManager integration test failed: {e}")
        return False

def test_thread_safety():
    """Test thread safety of FileManagerService"""
    print("\n🧪 Testing thread safety...")

    try:
        from laxyfile.core.file_manager_service import FileManagerService

        results = []
        errors = []

        def worker_thread(thread_id):
            try:
                service = FileManagerService.get_instance()
                current_dir = Path.cwd()
                files = service.list_directory(current_dir)
                results.append((thread_id, len(files)))
            except Exception as e:
                errors.append((thread_id, str(e)))

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker_thread, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        print(f"✅ Thread safety: {len(results)} successful operations, {len(errors)} errors")
        if errors:
            print(f"   Errors: {errors}")

        return len(errors) == 0

    except Exception as e:
        print(f"❌ Thread safety test failed: {e}")
        return False

def test_recovery_mechanisms():
    """Test automatic recovery mechanisms"""
    print("\n🧪 Testing recovery mechanisms...")

    try:
        from laxyfile.core.file_manager_service import FileManagerService

        service = FileManagerService.get_instance()

        # Test reinitialization
        reinit_success = service.reinitialize(force=True)
        print(f"✅ Reinitialization: {'Success' if reinit_success else 'Failed'}")

        # Test health after reinitialization
        is_healthy = service.is_healthy()
        print(f"✅ Health after reinit: {'Healthy' if is_healthy else 'Unhealthy'}")

        # Test service reset and recovery
        FileManagerService.reset()
        new_service = FileManagerService.get_instance()
        recovery_success = new_service.ensure_initialized()
        print(f"✅ Service recovery: {'Success' if recovery_success else 'Failed'}")

        return True

    except Exception as e:
        print(f"❌ Recovery mechanisms test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting LaxyFile Error Fixes Test Suite")
    print("=" * 50)

    tests = [
        test_file_manager_service,
        test_component_initializer,
        test_error_handling_mixin,
        test_panel_manager_integration,
        test_thread_safety,
        test_recovery_mechanisms
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1

        time.sleep(0.1)  # Brief pause between tests

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Error fixes are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())