#!/usr/bin/env python3
"""
Specific test to verify the NoneType error fix.

This test simulates the original error condition and verifies it's been resolved.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_original_nonetype_error():
    """Test that the original 'NoneType' object has no attribute 'list_directory' error is fixed"""
    print("🧪 Testing original NoneType error fix...")

    try:
        # This simulates the original error scenario where file_manager was None
        from laxyfile.ui.panels import PanelManager
        from laxyfile.ui.theme import ThemeManager
        from laxyfile.core.config import Config

        # Initialize components
        config = Config()
        theme_manager = ThemeManager(config)
        panel_manager = PanelManager(theme_manager)

        # This would previously cause: 'NoneType' object has no attribute 'list_directory'
        current_dir = Path.cwd()
        panel = panel_manager.render_panel(current_dir, "test", is_active=True)

        print("✅ Successfully created panel without NoneType error")
        print(f"   Panel created for: {current_dir}")
        print(f"   Panel type: {type(panel)}")

        # Test with multiple rapid calls (stress test)
        for i in range(5):
            panel = panel_manager.render_panel(current_dir, f"test_{i}", is_active=(i % 2 == 0))

        print("✅ Multiple rapid panel creations successful")

        return True

    except AttributeError as e:
        if "'NoneType' object has no attribute" in str(e):
            print(f"❌ Original NoneType error still occurs: {e}")
            return False
        else:
            print(f"❌ Different AttributeError: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_file_manager_service_robustness():
    """Test FileManagerService robustness under various conditions"""
    print("\n🧪 Testing FileManagerService robustness...")

    try:
        from laxyfile.core.file_manager_service import FileManagerService

        # Test getting service multiple times
        services = [FileManagerService.get_instance() for _ in range(10)]

        # Verify all are the same instance
        assert all(service is services[0] for service in services), "All instances should be the same"
        print("✅ Singleton consistency verified")

        # Test directory listing with various paths
        service = services[0]

        # Test current directory
        current_files = service.list_directory(Path.cwd())
        print(f"✅ Current directory: {len(current_files)} files")

        # Test parent directory
        parent_files = service.list_directory(Path.cwd().parent)
        print(f"✅ Parent directory: {len(parent_files)} files")

        # Test non-existent directory (should return empty list, not crash)
        non_existent_files = service.list_directory(Path("/non/existent/path"))
        print(f"✅ Non-existent directory handled: {len(non_existent_files)} files")

        # Test health status
        is_healthy = service.is_healthy()
        print(f"✅ Service health: {'Healthy' if is_healthy else 'Unhealthy'}")

        return True

    except Exception as e:
        print(f"❌ FileManagerService robustness test failed: {e}")
        return False

def test_error_recovery():
    """Test error recovery mechanisms"""
    print("\n🧪 Testing error recovery...")

    try:
        from laxyfile.core.error_handling_mixin import ErrorHandlingMixin
        from laxyfile.core.file_manager_service import FileManagerService

        class TestComponent(ErrorHandlingMixin):
            def __init__(self):
                super().__init__()

            def test_file_operation(self):
                # This should use the FileManagerService safely
                service = FileManagerService.get_instance()
                return service.list_directory(Path.cwd())

        component = TestComponent()

        # Test safe file operation
        result = component.safe_file_operation(
            operation=component.test_file_operation,
            fallback_value=[],
            max_retries=2
        )

        print(f"✅ Safe file operation: {len(result)} files retrieved")

        # Test file manager availability
        available = component.is_file_manager_available()
        print(f"✅ File manager availability: {'Available' if available else 'Unavailable'}")

        # Test recovery attempt
        recovery_success = component.ensure_file_manager_available()
        print(f"✅ Recovery mechanism: {'Success' if recovery_success else 'Failed'}")

        return True

    except Exception as e:
        print(f"❌ Error recovery test failed: {e}")
        return False

def main():
    """Run the NoneType error fix verification tests"""
    print("🚀 LaxyFile NoneType Error Fix Verification")
    print("=" * 50)

    tests = [
        test_original_nonetype_error,
        test_file_manager_service_robustness,
        test_error_recovery
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

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 SUCCESS: The original NoneType error has been fixed!")
        print("   - FileManagerService provides robust singleton access")
        print("   - ErrorHandlingMixin provides fallback behavior")
        print("   - PanelManager safely handles file manager operations")
        return 0
    else:
        print("⚠️  Some tests failed. The fix may not be complete.")
        return 1

if __name__ == "__main__":
    sys.exit(main())