#!/usr/bin/env python3
"""
LaxyFile - Beautiful Terminal File Manager with AI Integration

Main entry point for the application.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from laxyfile.main import main

if __name__ == "__main__":
    main()