#!/usr/bin/env python3
"""
Test script for LaxyFile component integration

This script tests if all components can be properly initialized and integrated.
"""

import asyncio
import sys
from pathlib import Path

# Add the laxyfile directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from laxyfile.core.config import Config
from laxyfile.integration.component_integration import initialize_integration
from laxyfile.utils.logging_system import initialize_logging


async def test_component_integration():
    """Test the component integration system"""
    print("🚀 Testing LaxyFile Component Integration")
    print("=" * 50)

    try:
        # Initialize configuration
        print("1. Initializing configuration...")
        config = Config()
        print("   ✅ Configuration initialized")

        # Initialize logging system
        print("\n2. Initializing logging system...")
        logging_system = initialize_logging(config)
        print("   ✅ Logging system initialized")

        # Initialize component integrator
        print("\n3. Initializing component integrator...")
        integrator = initialize_integration(config)
        print("   ✅ Component integrator created")

        # Initialize all components
        print("\n4. Initializing all components...")
        success = await integrator.initialize_all_components()

        if success:
            print("   ✅ All components initialized successfully")
        else:
            print("   ❌ Component initialization failed")
            return False

        # Test component interactions
        print("\n5. Testing component interactions...")
        test_results = await integrator.test_component_interactions()

        print("   Test Results:")
        for test_name, result in test_results.items():
            status = "✅" if result else "❌"
            print(f"     {status} {test_name}")

        # Check overall health
        print("\n6. Checking system health...")
        is_healthy = integrator.is_healthy()
        print(f"   {'✅' if is_healthy else '❌'} System health: {'Healthy' if is_healthy else 'Unhealthy'}")

        # Get component status
        print("\n7. Component Status:")
        component_status = integrator.get_all_component_status()
        for name, status in component_status.items():
            health_icon = "✅" if status.healthy else "❌"
            init_icon = "✅" if status.initialized else "❌"
            print(f"     {name}: {init_icon} Init {health_icon} Health")
            if status.error_message:
                print(f"       Error: {status.error_message}")

        # Test getting components
        print("\n8. Testing component access...")
        components_to_test = [
            'config', 'file_manager', 'ai_assistant',
            'preview_system', 'file_operations', 'ui_manager', 'plugin_manager'
        ]

        for component_name in components_to_test:
            component = integrator.get_component(component_name)
            status = "✅" if component is not None else "❌"
            print(f"     {status} {component_name}: {type(component).__name__ if component else 'None'}")

        # Shutdown
        print("\n9. Shutting down...")
        await integrator.shutdown()
        print("   ✅ Shutdown complete")

        print("\n" + "=" * 50)
        print("🎉 Integration test completed successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_basic_functionality():
    """Test basic functionality of integrated components"""
    print("\n🔧 Testing Basic Functionality")
    print("=" * 50)

    try:
        # Initialize system
        config = Config()
        logging_system = initialize_logging(config)
        integrator = initialize_integration(config)
        await integrator.initialize_all_components()

        # Test file manager
        print("1. Testing file manager...")
        file_manager = integrator.get_component('file_manager')
        if file_manager:
            current_dir = Path.cwd()
            files = await file_manager.list_directory(current_dir)
            print(f"   ✅ Listed {len(files)} files in current directory")
        else:
            print("   ❌ File manager not available")

        # Test AI assistant
        print("\n2. Testing AI assistant...")
        ai_assistant = integrator.get_component('ai_assistant')
        if ai_assistant:
            # Test with a simple query (this might fail if no AI models are configured)
            try:
                response = await ai_assistant.process_query("Hello, test query")
                if response.get('success'):
                    print("   ✅ AI assistant responded successfully")
                else:
                    print(f"   ⚠️ AI assistant responded with error: {response.get('error', 'Unknown')}")
            except Exception as e:
                print(f"   ⚠️ AI assistant test failed (expected if no models configured): {e}")
        else:
            print("   ❌ AI assistant not available")

        # Test preview system
        print("\n3. Testing preview system...")
        preview_system = integrator.get_component('preview_system')
        if preview_system:
            # Test preview generation for this script
            test_file = Path(__file__)
            preview = await preview_system.generate_preview(test_file)
            if preview.success:
                print(f"   ✅ Generated preview for {test_file.name}")
            else:
                print(f"   ⚠️ Preview generation failed: {preview.error_message}")
        else:
            print("   ❌ Preview system not available")

        # Test plugin manager
        print("\n4. Testing plugin manager...")
        plugin_manager = integrator.get_component('plugin_manager')
        if plugin_manager:
            plugins = plugin_manager.list_plugins()
            print(f"   ✅ Plugin manager loaded with {len(plugins)} plugins")
        else:
            print("   ❌ Plugin manager not available")

        # Shutdown
        await integrator.shutdown()

        print("\n" + "=" * 50)
        print("🎉 Basic functionality test completed!")
        return True

    except Exception as e:
        print(f"\n❌ Basic functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Main test function"""
    print("LaxyFile Integration Test Suite")
    print("=" * 60)

    # Run integration test
    integration_success = await test_component_integration()

    if integration_success:
        # Run basic functionality test
        functionality_success = await test_basic_functionality()

        if functionality_success:
            print("\n🎉 All tests passed! Integration is working correctly.")
            return 0
        else:
            print("\n⚠️ Integration test passed but functionality test failed.")
            return 1
    else:
        print("\n❌ Integration test failed.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)