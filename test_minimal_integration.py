#!/usr/bin/env python3
"""
Minimal integration test to validate core functionality
"""

import asyncio
import tempfile
from pathlib import Path
import sys

# Add the current directory to Python path
sys.path.insert(0, '.')

from laxyfile.core.config import Config
from laxyfile.core.advanced_file_manager import AdvancedFileManager
from laxyfile.utils.logging_system import initialize_logging, get_logger, LogCategory


async def test_minimal_integration():
    """Test minimal component integration"""
    print("🧪 Testing LaxyFile Minimal Integration...")

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
            }
        })

        try:
            print("  ✅ Created configuration")

            # Initialize logging
            logging_system = initialize_logging(config)
            logger = get_logger('test', LogCategory.SYSTEM)
            print("  ✅ Initialized logging system")

            # Test file manager
            print("  🔄 Testing file manager...")
            file_manager = AdvancedFileManager(config)
            await file_manager.initialize()
            print("  ✅ File manager initialized")

            # Test directory listing
            current_dir = Path.cwd()
            files = await file_manager.list_directory(current_dir)
            print(f"  ✅ Listed {len(files)} files in current directory")

            # Test file operations
            if files:
                first_file = files[0]
                print(f"  📄 First file: {first_file.name} ({first_file.size} bytes)")

            # Test caching
            cache_stats = file_manager.get_cache_stats()
            print(f"  📊 Cache stats: {cache_stats}")

            print("🎉 Minimal integration test completed successfully!")
            return True

        except Exception as e:
            print(f"  ❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Run the minimal integration test"""
    success = await test_minimal_integration()
    if not success:
        sys.exit(1)
    print("\n✨ Core functionality is working correctly!")


if __name__ == "__main__":
    asyncio.run(main())