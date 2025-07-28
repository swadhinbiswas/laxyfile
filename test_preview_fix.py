#!/usr/bin/env python3
"""
Test script to verify the preview system NoneType error fix
"""

import asyncio
import sys
from pathlib import Path

# Add the laxyfile package to the path
sys.path.insert(0, str(Path(__file__).parent))

async def test_preview_system_error_handling():
    """Test that preview system handles file manager errors gracefully"""
    print("🧪 Testing Preview System Error Handling...")

    try:
        from laxyfile.preview.preview_system import AdvancedPreviewSystem, PreviewConfig
        from laxyfile.core.file_manager_service import FileManagerService

        # Reset file manager service to simulate uninitialized state
        FileManagerService.reset()

        # Create preview system
        config = PreviewConfig()
        preview_system = AdvancedPreviewSystem(config)

        # Initialize preview system
        await preview_system.initialize()
        print("  ✅ Preview system initialized successfully")

        # Test preview generation with a file that exists
        test_file = Path(__file__)
        print(f"  🔍 Testing preview generation for: {test_file.name}")

        # This should not crash even if file manager is not properly initialized
        preview_result = await preview_system.generate_preview(test_file)

        if preview_result.success:
            print(f"  ✅ Preview generated successfully: {len(preview_result.content)} characters")
        else:
            print(f"  ⚠️  Preview generation failed (expected): {preview_result.error_message}")

        # Test with non-existent file
        fake_file = Path("non_existent_file.txt")
        print(f"  🔍 Testing preview generation for non-existent file: {fake_file.name}")

        preview_result = await preview_system.generate_preview(fake_file)

        if not preview_result.success:
            print(f"  ✅ Non-existent file handled gracefully: {preview_result.error_message}")
        else:
            print(f"  ⚠️  Unexpected success for non-existent file")

        print("  ✅ Preview system error handling test completed successfully")
        return True

    except Exception as e:
        print(f"  ❌ Preview system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_enhanced_panels_error_handling():
    """Test that enhanced panels handle file manager errors gracefully"""
    print("\n🧪 Testing Enhanced Panels Error Handling...")

    try:
        from laxyfile.ui.enhanced_panels import EnhancedPanelRenderer
        from laxyfile.ui.theme import ThemeManager
        from laxyfile.core.config import Config
        from rich.console import Console

        # Create components
        console = Console()
        config = Config()
        theme_manager = ThemeManager(config)
        panel_renderer = EnhancedPanelRenderer(theme_manager, console)

        print("  ✅ Enhanced panel renderer created successfully")

        # Test preview panel rendering with no file
        preview_panel = panel_renderer.render_preview_panel(None)
        print("  ✅ Preview panel rendered successfully with no file")

        # Test preview panel rendering with a file
        test_file = Path(__file__)
        preview_panel = panel_renderer.render_preview_panel(test_file, "Test content", "text")
        print("  ✅ Preview panel rendered successfully with file")

        print("  ✅ Enhanced panels error handling test completed successfully")
        return True

    except Exception as e:
        print(f"  ❌ Enhanced panels test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    print("🚀 Starting LaxyFile Preview System Error Fix Tests\n")

    test_results = []

    # Test preview system
    result1 = await test_preview_system_error_handling()
    test_results.append(result1)

    # Test enhanced panels
    result2 = await test_enhanced_panels_error_handling()
    test_results.append(result2)

    # Summary
    print(f"\n📊 Test Results:")
    print(f"  ✅ Passed: {sum(test_results)}")
    print(f"  ❌ Failed: {len(test_results) - sum(test_results)}")

    if all(test_results):
        print("\n🎉 All tests passed! Preview system error handling is working correctly.")
        return 0
    else:
        print("\n💥 Some tests failed. Please check the error messages above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)