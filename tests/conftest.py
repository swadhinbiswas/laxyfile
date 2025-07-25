"""
Pytest configuration and shared fixtures for LaxyFile tests
"""

import pytest
import tempfile
import shutil
import asyncio
from pathlib import Path
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, List

# Import LaxyFile components for testing
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from laxyfile.core.config import Config
from laxyfile.core.advanced_file_manager import AdvancedFileManager
from laxyfile.ai.advanced_assistant import AdvancedAIAssistant
from laxyfile.ui.superfile_ui import SuperFileUI
from laxyfile.ui.theme import ThemeManager
from laxyfile.core.types import EnhancedFileInfo, PanelData, SidebarData, StatusData
from rich.console import Console


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def sample_files(temp_dir):
    """Create sample files and directories for testing"""
    files = {}

    # Create directories
    (temp_dir / "documents").mkdir()
    (temp_dir / "images").mkdir()
    (temp_dir / "code").mkdir()
    (temp_dir / ".hidden").mkdir()

    # Create files
    files['text_file'] = temp_dir / "readme.txt"
    files['text_file'].write_text("This is a sample text file for testing.")

    files['python_file'] = temp_dir / "code" / "script.py"
    files['python_file'].write_text("#!/usr/bin/env python3\nprint('Hello, World!')")

    files['large_file'] = temp_dir / "large_file.dat"
    files['large_file'].write_bytes(b"x" * 1024 * 1024)  # 1MB file

    files['empty_file'] = temp_dir / "empty.txt"
    files['empty_file'].touch()

    files['hidden_file'] = temp_dir / ".hidden" / "secret.txt"
    files['hidden_file'].write_text("Hidden content")

    # Create symlink if supported
    try:
        files['symlink'] = temp_dir / "link_to_readme.txt"
        files['symlink'].symlink_to(files['text_file'])
    except OSError:
        # Symlinks not supported on this platform
        pass

    return files


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing"""
    config = Mock(spec=Config)
    config.get = Mock(side_effect=lambda key, default=None: {
        'cache_size': 100,
        'ui.use_magic_detection': True,
        'ui.use_nerd_fonts': False,
        'ui.use_ascii_icons': False,
        'ui.max_files_display': 1000,
        'performance.max_concurrent_operations': 5,
        'performance.chunk_size': 50,
        'performance.memory_threshold_mb': 100,
        'performance.lazy_loading_threshold': 500,
        'performance.background_processing': True,
        'performance.use_threading': True,
        'performance.max_worker_threads': 2,
        'ai_models': {
            'test_model': {
                'provider': 'openrouter',
                'model_name': 'test/model',
                'api_key': 'test_key',
                'capabilities': ['text_analysis', 'code_analysis']
            }
        },
        'cache_ttl': 300,
        'max_analysis_history': 100
    }.get(key, default))

    return config


@pytest.fixture
def file_manager(mock_config):
    """Create a file manager instance for testing"""
    return AdvancedFileManager(mock_config)


@pytest.fixture
def ai_assistant(mock_config):
    """Create an AI assistant instance for testing"""
    return AdvancedAIAssistant(mock_config)


@pytest.fixture
def theme_manager():
    """Create a theme manager instance for testing"""
    return ThemeManager()


@pytest.fixture
def console():
    """Create a Rich console for testing"""
    return Console(force_terminal=True, width=80, height=24)


@pytest.fixture
def superfile_ui(theme_manager, console, mock_config):
    """Create a SuperFile UI instance for testing"""
    return SuperFileUI(theme_manager, console, mock_config)


@pytest.fixture
def sample_file_info(temp_dir):
    """Create sample file info objects for testing"""
    from datetime import datetime

    return [
        EnhancedFileInfo(
            path=temp_dir / "readme.txt",
            name="readme.txt",
            size=1024,
            modified=datetime.now(),
            is_dir=False,
            is_symlink=False,
            file_type="text",
            icon="📄",
            permissions_octal="644",
            owner="user",
            group="group"
        ),
        EnhancedFileInfo(
            path=temp_dir / "documents",
            name="documents",
            size=0,
            modified=datetime.now(),
            is_dir=True,
            is_symlink=False,
            file_type="directory",
            icon="📁",
            permissions_octal="755",
            owner="user",
            group="group"
        )
    ]


@pytest.fixture
def panel_data(temp_dir, sample_file_info):
    """Create sample panel data for testing"""
    return PanelData(
        path=temp_dir,
        files=sample_file_info,
        current_selection=0,
        selected_files=set(),
        sort_type="name",
        reverse_sort=False,
        search_query=""
    )


@pytest.fixture
def sidebar_data(temp_dir):
    """Create sample sidebar data for testing"""
    return SidebarData(
        current_path=temp_dir,
        bookmarks=[temp_dir / "documents", temp_dir / "images"],
        recent_paths=[temp_dir / "code"],
        directory_tree={}
    )


@pytest.fixture
def status_data(sample_file_info):
    """Create sample status data for testing"""
    return StatusData(
        current_file=sample_file_info[0],
        selected_count=0,
        total_files=2,
        total_size=1024,
        operation_status="",
        ai_status=""
    )


@pytest.fixture
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_aiohttp_session():
    """Mock aiohttp session for AI API tests"""
    session = MagicMock()
    response = MagicMock()
    response.status = 200
    response.json = MagicMock(return_value={'response': 'Test AI response'})
    session.post.return_value.__aenter__.return_value = response
    return session


class AsyncMock(MagicMock):
    """Mock class for async functions"""
    async def __call__(self, *args, **kwargs):
        return super().__call__(*args, **kwargs)


@pytest.fixture
def mock_watchdog():
    """Mock watchdog for file watching tests"""
    observer = Mock()
    handler = Mock()

    # Mock the watchdog imports
    import sys
    from unittest.mock import MagicMock

    watchdog_mock = MagicMock()
    watchdog_mock.observers.Observer = Mock(return_value=observer)
    watchdog_mock.events.FileSystemEventHandler = Mock(return_value=handler)

    sys.modules['watchdog'] = watchdog_mock
    sys.modules['watchdog.observers'] = watchdog_mock.observers
    sys.modules['watchdog.events'] = watchdog_mock.events

    return {'observer': observer, 'handler': handler}


# Test utilities
def create_test_file(path: Path, content: str = "test content", size: int = None):
    """Create a test file with specified content or size"""
    if size:
        path.write_bytes(b"x" * size)
    else:
        path.write_text(content)
    return path


def assert_file_info_equal(actual: EnhancedFileInfo, expected: EnhancedFileInfo):
    """Assert that two file info objects are equal"""
    assert actual.path == expected.path
    assert actual.name == expected.name
    assert actual.size == expected.size
    assert actual.is_dir == expected.is_dir
    assert actual.is_symlink == expected.is_symlink
    assert actual.file_type == expected.file_type


# Performance testing utilities
@pytest.fixture
def performance_timer():
    """Timer for performance tests"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.time()

        def stop(self):
            self.end_time = time.time()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0

    return Timer()


# Markers for different test types
pytest.mark.unit = pytest.mark.unit
pytest.mark.integration = pytest.mark.integration
pytest.mark.e2e = pytest.mark.e2e
pytest.mark.performance = pytest.mark.performance
pytest.mark.slow = pytest.mark.slow