#!/usr/bin/env python3
"""
Test script to verify the media viewer NoneType error fix
"""

import sys
from pathlib import Path

# Add the laxyfile package to the path
sys.path.insert(0, str(Path(__file__).parent))

def test_media_viewer_error_handling():
    """Test that media viewer handles initialization errors gracefully"""
    print("🧪 Testing Media Viewer Error Handling...")

    try:
        from laxyfile.main import LaxyFileApp

        # Create LaxyFile app
        app = LaxyFileApp()
        print("  ✅ LaxyFile app created successfully")

        # Test create_preview_panel method - this should not crash even if media viewer is None
        print("  🔍 Testing create_preview_panel method...")

        try:
            preview_panel = app.create_preview_panel()
            print("  ✅ Preview panel created successfully without crashing")

            # Check if the panel has content (even if it's an error message)
            if hasattr(preview_panel, 'renderable'):
                print("  ✅ Preview panel has renderable content")
            else:
                print("  ✅ Preview panel created (may be fallback content)")

        except Exception as e:
            print(f"  ❌ Preview panel creation failed: {e}")
            return False

        # Test that media viewer lazy initialization works
        print("  🔍 Testing media viewer lazy initialization...")

        try:
            media_viewer = app._get_media_viewer()
            if media_viewer is not None:
                print("  ✅ Media viewer initialized successfully")
            else:
                print("  ⚠️  Media viewer is None (expected if dependencies missing)")

        except Exception as e:
            print(f"  ❌ Media viewer initialization failed: {e}")
            return False

        print("  ✅ Media viewer error handling test completed successfully")
        return True

    except Exception as e:
        print(f"  ❌ Media viewer test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_file_manager_service_integration():
    """Test that file manager service integration works correctly"""
    print("\n🧪 Testing File Manager Service Integration...")

    try:
        from laxyfile.main import LaxyFileApp
        from laxyfile.core.file_manager_service import FileManagerService

        # Reset file manager service to test initialization
        FileManagerService.reset()

        # Create LaxyFile app
        app = LaxyFileApp()
        print("  ✅ LaxyFile app created successfully")

        # Test file manager property access
        print("  🔍 Testing file manager property access...")

        try:
            file_manager = app.file_manager
            if file_manager is not None:
                print("  ✅ File manager accessed successfully through property")
            else:
                print("  ⚠️  File manager is None (may need initialization)")

        except Exception as e:
            print(f"  ❌ File manager property access failed: {e}")
            return False

        # Test safe file operations
        print("  🔍 Testing safe file operations...")

        try:
            # This should not crash even if file manager is not available
            test_result = app.safe_file_operation(
                operation=lambda: [],
                fallback_value=[],
                cache_key="test_operation"
            )
            print("  ✅ Safe file operation completed successfully")

        except Exception as e:
            print(f"  ❌ Safe file operation failed: {e}")
            return False

        print("  ✅ File manager service integration test completed successfully")
        return True

    except Exception as e:
        print(f"  ❌ File manager service integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests"""
    print("🚀 Starting LaxyFile Media Viewer Error Fix Tests\n")

    test_results = []

    # Test media viewer error handling
    result1 = test_media_viewer_error_handling()
    test_results.append(result1)

    # Test file manager service integration
    result2 = test_file_manager_service_integration()
    test_results.append(result2)

    # Summary
    print(f"\n📊 Test Results:")
    print(f"  ✅ Passed: {sum(test_results)}")
    print(f"  ❌ Failed: {len(test_results) - sum(test_results)}")

    if all(test_results):
        print("\n🎉 All tests passed! Media viewer and file manager error handling is working correctly.")
        return 0
    else:
        print("\n💥 Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)