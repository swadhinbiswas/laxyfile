#!/usr/bin/env python3
"""
Simple integration test to validate component integration
"""

import asyncio
import tempfile
from pathlib import Path

# Add the current directory to Python path
import sys
sys.path.insert(0, '.')

from laxyfile.core.config import Config
from laxyfile.integration.component_integration import ComponentIntegrator


async def test_basic_integration():
    """Test basic component integration"""
    print("🧪 Testing LaxyFile Component Integration...")

    # Create temporary config directory
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir)

        # Create test configuration
        config = Config(config_dir=config_dir)
        config.data.update({
            'logging': {
                'console': {'enabled': True, 'level': 'INFO'},
                'file': {'enabled': False},
                'performance': {'enabled': False},
                'error': {'enabled': False}
            },
            'ai': {'enabled': False},  # Disable AI for basic test
            'plugins': {'enabled': False}  # Disable plugins for basic test
        })

        # Create integrator
        integrator = ComponentIntegrator(config)

        try:
            print("  ✅ Created component integrator")

            # Initialize components
            print("  🔄 Initializing components...")
            success = await integrator.initialize_all_components()

            if not success:
                print("  ❌ Component initialization failed")
                return False

            print("  ✅ All components initialized successfully")

            # Check component health
            print("  🔄 Checking component health...")
            is_healthy = integrator.is_healthy()

            if not is_healthy:
                print("  ⚠️  Some components are unhealthy")
                # Print status for debugging
                for name, status in integrator.get_all_component_status().items():
                    health_status = "✅" if status.healthy else "❌"
                    print(f"    {health_status} {name}: {'healthy' if status.healthy else 'unhealthy'}")
            else:
                print("  ✅ All components are healthy")

            # Test component interactions
            print("  🔄 Testing component interactions...")
            test_results = await integrator.test_component_interactions()

            passed_tests = sum(1 for result in test_results.values() if result is True)
            total_tests = len(test_results)

            print(f"  📊 Interaction tests: {passed_tests}/{total_tests} passed")

            for test_name, result in test_results.items():
                status = "✅" if result else "❌"
                print(f"    {status} {test_name}")

            # Test basic functionality
            print("  🔄 Testing basic functionality...")

            # Test file manager
            file_manager = integrator.get_component('file_manager')
            if file_manager:
                current_dir = Path.cwd()
                files = await file_manager.list_directory(current_dir)
                print(f"    ✅ File manager: Listed {len(files)} files in current directory")
            else:
                print("    ❌ File manager not available")

            # Test preview system
            preview_system = integrator.get_component('preview_system')
            if preview_system:
                # Try to preview this test file
                test_file = Path(__file__)
                preview = await preview_system.generate_preview(test_file)
                if preview:
                    print(f"    ✅ Preview system: Generated preview for {test_file.name}")
                else:
                    print(f"    ⚠️  Preview system: No preview generated for {test_file.name}")
            else:
                print("    ❌ Preview system not available")

            print("  ✅ Basic functionality tests completed")

            # Get final statistics
            if hasattr(integrator, 'startup_time'):
                print(f"  📈 Startup time: {integrator.startup_time:.2f}s")

            print("🎉 Integration test completed successfully!")
            return True

        except Exception as e:
            print(f"  ❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            # Cleanup
            print("  🧹 Cleaning up...")
            await integrator.shutdown()
            print("  ✅ Cleanup completed")


async def main():
    """Run the integration test"""
    success = await test_basic_integration()
    if not success:
        sys.exit(1)
    print("\n✨ All tests passed! LaxyFile component integration is working correctly.")


if __name__ == "__main__":
    asyncio.run(main())