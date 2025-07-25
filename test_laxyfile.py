#!/usr/bin/env python3
"""
Test script for LaxyFile - Verify basic functionality
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")

    try:
        from laxyfile.core.config import Config
        print("✅ Config module imported successfully")

        from laxyfile.core.file_manager import FileManager, FileInfo
        print("✅ FileManager module imported successfully")

        from laxyfile.ui.theme import ThemeManager
        print("✅ ThemeManager module imported successfully")

        from laxyfile.ui.panels import PanelManager
        print("✅ PanelManager module imported successfully")

        from laxyfile.ui.image_viewer import ImageViewer
        print("✅ ImageViewer module imported successfully")

        from laxyfile.ai.assistant import AIAssistant
        print("✅ AIAssistant module imported successfully")

        from laxyfile.utils.logger import Logger
        print("✅ Logger module imported successfully")

        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality"""
    print("\n🔧 Testing basic functionality...")

    try:
        # Test config
        from laxyfile.core.config import Config
        config = Config()
        print(f"✅ Config loaded, theme: {config.get_theme().name}")

        # Test file manager
        from laxyfile.core.file_manager import FileManager
        fm = FileManager()
        files = fm.list_directory(Path.cwd())
        print(f"✅ FileManager working, found {len(files)} items in current directory")

        # Test theme manager
        from laxyfile.ui.theme import ThemeManager
        theme_manager = ThemeManager(config)
        themes = theme_manager.get_available_themes()
        print(f"✅ ThemeManager working, available themes: {', '.join(themes)}")

        # Test logger
        from laxyfile.utils.logger import Logger
        logger = Logger()
        logger.info("Test log message")
        print("✅ Logger working")

        return True
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def test_rich_ui():
    """Test Rich UI components"""
    print("\n🎨 Testing Rich UI...")

    try:
        from rich.console import Console
        from rich.panel import Panel
        from rich.text import Text

        console = Console()

        # Test basic Rich functionality
        test_panel = Panel(
            Text("LaxyFile Test", style="bold green"),
            title="🚀 Test Panel",
            border_style="blue"
        )

        console.print(test_panel)
        print("✅ Rich UI components working")

        return True
    except Exception as e:
        print(f"❌ Rich UI test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 LaxyFile Test Suite")
    print("=" * 50)

    # Run tests
    import_success = test_imports()
    func_success = test_basic_functionality()
    ui_success = test_rich_ui()

    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"   Imports: {'✅ PASS' if import_success else '❌ FAIL'}")
    print(f"   Functionality: {'✅ PASS' if func_success else '❌ FAIL'}")
    print(f"   Rich UI: {'✅ PASS' if ui_success else '❌ FAIL'}")

    if all([import_success, func_success, ui_success]):
        print("\n🎉 All tests passed! LaxyFile is ready to run.")
        print("   Run: python main.py")
    else:
        print("\n⚠️  Some tests failed. Please check the installation.")
        print("   Try: pip install -r requirements.txt")

if __name__ == "__main__":
    main()