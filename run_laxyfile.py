#!/usr/bin/env python3
"""
LaxyFile Launcher with AI Features
Enhanced terminal file manager with OpenRouter AI integration
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def check_terminal_capabilities():
    """Check terminal capabilities for optimal experience"""
    capabilities = {
        "color_support": False,
        "unicode_support": False,
        "terminal_size": (80, 24),
        "ai_configured": False
    }

    # Check color support
    if os.getenv("COLORTERM") or os.getenv("TERM", "").endswith("color"):
        capabilities["color_support"] = True

    # Check terminal size
    try:
        size = shutil.get_terminal_size()
        capabilities["terminal_size"] = (size.columns, size.lines)
    except:
        pass

    # Check Unicode support
    try:
        "🚀".encode(sys.stdout.encoding or 'utf-8')
        capabilities["unicode_support"] = True
    except:
        pass

    # Check AI configuration
    if os.getenv("OPENROUTER_API_KEY"):
        capabilities["ai_configured"] = True

    return capabilities

def check_dependencies():
    """Check for required and optional dependencies"""
    required_deps = [
        "rich", "pydantic", "yaml", "PIL", "pygments"
    ]

    optional_deps = [
        "cv2", "openai", "psutil", "magic"
    ]

    missing_required = []
    missing_optional = []

    for dep in required_deps:
        try:
            if dep == "yaml":
                import yaml
            elif dep == "PIL":
                from PIL import Image
            else:
                __import__(dep)
        except ImportError:
            missing_required.append(dep)

    for dep in optional_deps:
        try:
            if dep == "cv2":
                import cv2
            elif dep == "magic":
                import magic
            elif dep == "openai":
                import openai
            elif dep == "psutil":
                import psutil
        except ImportError:
            missing_optional.append(dep)

    return missing_required, missing_optional

def show_startup_banner(capabilities):
    """Show startup banner with system info"""
    width = capabilities["terminal_size"][0]

    if capabilities["unicode_support"]:
        banner = """
🚀 LaxyFile - Advanced Terminal File Manager 🚀
   Powered by Kimi AI through OpenRouter
"""
    else:
        banner = """
LaxyFile - Advanced Terminal File Manager
   Powered by Kimi AI through OpenRouter
"""

    print("=" * min(width, 60))
    print(banner)
    print("=" * min(width, 60))

    # System info
    print(f"Terminal: {capabilities['terminal_size'][0]}x{capabilities['terminal_size'][1]}")
    print(f"Colors: {'✅ Supported' if capabilities['color_support'] else '❌ Limited'}")
    print(f"Unicode: {'✅ Supported' if capabilities['unicode_support'] else '❌ Limited'}")
    print(f"AI Features: {'🤖 Ready' if capabilities['ai_configured'] else '🔴 Setup Required'}")
    print()

def show_ai_setup_instructions():
    """Show AI setup instructions"""
    print("🤖 AI ASSISTANT SETUP")
    print("=" * 50)
    print()
    print("To enable the advanced AI features:")
    print()
    print("1. Get an OpenRouter API key:")
    print("   • Visit https://openrouter.ai/")
    print("   • Create an account and get your API key")
    print("   • Free tier includes access to Kimi AI model")
    print()
    print("2. Set the environment variable:")
    print("   export OPENROUTER_API_KEY='your-api-key-here'")
    print()
    print("3. Or add to your shell profile:")
    print("   echo 'export OPENROUTER_API_KEY=\"your-key\"' >> ~/.bashrc")
    print("   source ~/.bashrc")
    print()
    print("🎯 AI Features include:")
    print("   • Complete system analysis with device monitoring")
    print("   • Intelligent file organization suggestions")
    print("   • Security audits and vulnerability detection")
    print("   • Performance optimization recommendations")
    print("   • Video and media analysis with metadata")
    print("   • Duplicate detection and cleanup")
    print("   • Smart backup strategies")
    print("   • Real-time content analysis and insights")
    print()

def main():
    """Main launcher function"""
    try:
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ LaxyFile requires Python 3.8 or higher")
            print(f"   Current version: {sys.version}")
            return 1

        # Check terminal capabilities
        capabilities = check_terminal_capabilities()

        # Show banner
        show_startup_banner(capabilities)

        # Check dependencies
        missing_required, missing_optional = check_dependencies()

        if missing_required:
            print("❌ MISSING REQUIRED DEPENDENCIES:")
            for dep in missing_required:
                print(f"   • {dep}")
            print()
            print("Install with: pip install -r requirements.txt")
            return 1

        if missing_optional:
            print("⚠️  MISSING OPTIONAL DEPENDENCIES:")
            for dep in missing_optional:
                print(f"   • {dep}")
            print()
            print("Some features will be limited. Install with:")
            print("pip install opencv-python openai psutil python-magic")
            print("(Note: These enhance video analysis and AI features)")
            print()

        # AI setup check
        if not capabilities["ai_configured"]:
            show_ai_setup_instructions()
            response = input("Continue without AI features? (y/N): ").lower()
            if response not in ['y', 'yes']:
                return 0
        else:
            print("🤖 AI Assistant: Ready with Kimi AI model")
            print()

        # Performance warning for small terminals
        if capabilities["terminal_size"][0] < 100:
            print("⚠️  Terminal width < 100 columns. Consider resizing for optimal experience.")
            print()

        # Launch LaxyFile
        print("🚀 Launching LaxyFile...")
        print("💡 Press 'i' for AI assistant, '?' for help, 'q' to quit")
        print("=" * 50)
        print()

        # Add current directory to Python path
        current_dir = Path(__file__).parent
        if str(current_dir) not in sys.path:
            sys.path.insert(0, str(current_dir))

        # Import and run
        from laxyfile.main import main as laxyfile_main
        return laxyfile_main()

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        return 0
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return 1
    except Exception as e:
        print(f"❌ Launcher error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())