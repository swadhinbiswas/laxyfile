"""
Unit tests for SuperFileUI

Tests the SuperFile-inspired user interface system including layout management,
panel rendering, theme application, and responsive design.
"""

import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text

from laxyfile.ui.superfile_ui import SuperFileUI
from laxyfile.ui.theme import ThemeManager
from laxyfile.core.types import PanelData, SidebarData, StatusData, EnhancedFileInfo


@pytest.mark.unit
class TestSuperFileUI:
    """Test the SuperFileUI class"""

    def test_ui_initialization(self, theme_manager, console, mock_config):
        """Test UI initialization"""
        ui = SuperFileUI(theme_manager, console, mock_config)

        assert ui.theme_manager == theme_manager
        assert ui.console == console
        assert ui.config == mock_config
        assert ui.show_sidebar is True
        assert ui.show_preview is True
        assert ui.sidebar_width == 20
        assert ui.preview_width == 30

    def test_create_layout(self, superfile_ui):
        """Test layout creation"""
        layout = superfile_ui.create_layout()

        assert isinstance(layout, Layout)
        assert layout.name == "root"
        assert superfile_ui.layout == layout

        # Check layout structure
        assert "header" in layout
        assert "main" in layout
        assert "footer" in layout
        assert "sidebar" in layout["main"]
        assert "panels" in layout["main"]
        assert "preview" in layout["main"]
        assert "left_panel" in layout["panels"]
        assert "right_panel" in layout["panels"]

    def test_render_file_panel_basic(self, superfile_ui, panel_data):
        """Test basic file panel rendering"""
        panel = superfile_ui.render_file_panel(panel_data)

        assert isinstance(panel, Panel)
        # Panel should contain file information
        panel_content = str(panel)
        assert "readme.txt" in panel_content
        assert "documents" in panel_content

    def test_render_file_panel_with_selection(self, superfile_ui, temp_dir, sample_file_info):
        """Test file panel rendering with selection"""
        # Create panel data with selection
        panel_data = PanelData(
            path=temp_dir,
            files=sample_file_info,
            current_selection=0,
            selected_files={sample_file_info[0].path},
            sort_type="name",
            reverse_sort=False,
            search_query=""
        )

        panel = superfile_ui.render_file_panel(panel_data)
        panel_content = str(panel)

        # Should show selection indicators
        assert "▶●" in panel_content or "●" in panel_content

    def test_render_file_panel_with_search(self, superfile_ui, temp_dir, sample_file_info):
        """Test file panel rendering with search query"""
        panel_data = PanelData(
            path=temp_dir,
            files=sample_file_info,
            current_selection=0,
            selected_files=set(),
            sort_type="name",
            reverse_sort=False,
            search_query="readme"
        )

        panel = superfile_ui.render_file_panel(panel_data)
        panel_content = str(panel)

        # Should show search indicator
        assert "🔍readme" in panel_content

    def test_render_file_panel_error_handling(self, superfile_ui):
        """Test file panel rendering with error"""
        # Create invalid panel data
        invalid_panel_data = Mock()
        invalid_panel_data.files = None  # This should cause an error

        panel = superfile_ui.render_file_panel(invalid_panel_data)

        assert isinstance(panel, Panel)
        panel_content = str(panel)
        assert "Error" in panel_content

    def test_render_sidebar_basic(self, superfile_ui, sidebar_data):
        """Test basic sidebar rendering"""
        panel = superfile_ui.render_sidebar(sidebar_data)

        assert isinstance(panel, Panel)
        panel_content = str(panel)

        # Should contain navigation elements
        assert "📍 Current Path" in panel_content
        assert "🔖 Bookmarks" in panel_content

    def test_render_sidebar_with_bookmarks(self, superfile_ui, temp_dir):
        """Test sidebar rendering with bookmarks"""
        sidebar_data = SidebarData(
            current_path=temp_dir,
            bookmarks=[temp_dir / "documents", temp_dir / "images", temp_dir / "code"],
            recent_paths=[],
            directory_tree={}
        )

        panel = superfile_ui.render_sidebar(sidebar_data)
        panel_content = str(panel)

        assert "🔖 Bookmarks" in panel_content
        assert "documents" in panel_content
        assert "images" in panel_content

    def test_render_sidebar_with_recent_paths(self, superfile_ui, temp_dir):
        """Test sidebar rendering with recent paths"""
        sidebar_data = SidebarData(
            current_path=temp_dir,
            bookmarks=[],
            recent_paths=[temp_dir / "code", temp_dir / "documents"],
            directory_tree={}

        panel = superfile_ui.render_sidebar(sidebar_data)
        panel_content = str(panel)

        assert "🕒 Recent" in panel_content
        assert "code" in panel_content

    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_percent')
    @patch('psutil.disk_partitions')
    @patch('psutil.disk_usage')
    def test_render_sidebar_with_system_info(self, mock_disk_usage, mock_disk_partitions,
                                           mock_cpu_percent, mock_virtual_memory,
                                           superfile_ui, sidebar_data):
        """Test sidebar rendering with system information"""
        # Mock system info
        mock_virtual_memory.return_value = Mock(percent=75.5)
        mock_cpu_percent.return_value = 45.2
        mock_disk_partitions.return_value = [Mock(mountpoint='/')]
        mock_disk_usage.return_value = Mock(total=1000000000, used=600000000, free=400000000)

        panel = superfile_ui.render_sidebar(sidebar_data)
        panel_content = str(panel)

        assert "💻 System" in panel_content
        assert "RAM:" in panel_content
        assert "CPU:" in panel_content

    def test_render_footer_basic(self, superfile_ui, status_data):
        """Test basic footer rendering"""
        panel = superfile_ui.render_footer(status_data)

        assert isinstance(panel, Panel)
        panel_content = str(panel)

        # Should contain file info and shortcuts
        assert "readme.txt" in panel_content
        assert "Nav" in panel_content  # Keyboard shortcuts
        assert "Quit" in panel_content

    def test_render_footer_with_selection(self, superfile_ui, sample_file_info):
        """Test footer rendering with file selection"""
        status_data = StatusData(
            current_file=sample_file_info[0],
            selected_count=3,
            total_files=10,
            total_size=2048,
            operation_status="",
            ai_status=""
        )

        panel = superfile_ui.render_footer(status_data)
        panel_content = str(panel)

        assert "3 selected" in panel_content
        assert "10 items" in panel_content

    def test_render_footer_with_operation_status(self, superfile_ui, sample_file_info):
        """Test footer rendering with operation status"""
        status_data = StatusData(
            current_file=sample_file_info[0],
            selected_count=0,
            total_files=5,
            total_size=1024,
            operation_status="Copying files...",
            ai_status=""
        )

        panel = superfile_ui.render_footer(status_data)
        panel_content = str(panel)

        assert "Copying files..." in panel_content

    def test_render_footer_with_ai_status(self, superfile_ui, sample_file_info):
        """Test footer rendering with AI status"""
        status_data = StatusData(
            current_file=sample_file_info[0],
            selected_count=0,
            total_files=5,
            total_size=1024,
            operation_status="",
            ai_status="Analyzing..."
        )

        panel = superfile_ui.render_footer(status_data)
        panel_content = str(panel)

        assert "🤖 Analyzing..." in panel_content

    def test_render_header_basic(self, superfile_ui):
        """Test basic header rendering"""
        panel = superfile_ui.render_header()

        assert isinstance(panel, Panel)
        panel_content = str(panel)

        assert "LaxyFile" in panel_content
        assert "🚀" in panel_content
        assert "✨" in panel_content

    def test_render_header_with_custom_title(self, superfile_ui):
        """Test header rendering with custom title and subtitle"""
        panel = superfile_ui.render_header("Custom Title", "Custom Subtitle")

        panel_content = str(panel)
        assert "Custom Title" in panel_content
        assert "Custom Subtitle" in panel_content

    def test_handle_resize(self, superfile_ui):
        """Test terminal resize handling"""
        # Create layout first
        superfile_ui.create_layout()

        # Test resize
        superfile_ui.handle_resize(120, 40)

        assert superfile_ui.current_width == 120
        assert superfile_ui.current_height == 40

    def test_handle_resize_narrow_terminal(self, superfile_ui):
        """Test resize handling for narrow terminal"""
        superfile_ui.create_layout()

        # Simulate narrow terminal
        superfile_ui.handle_resize(50, 24)

        assert superfile_ui.current_width == 50
        assert superfile_ui.current_height == 24

    def test_apply_theme(self, superfile_ui):
        """Test theme application"""
        with patch.object(superfile_ui.theme_manager, 'set_theme') as mock_set_theme:
            superfile_ui.apply_theme("dracula")
            mock_set_theme.assert_called_once_with("dracula")

    def test_format_file_size(self, superfile_ui):
        """Test file size formatting"""
        # Test bytes
        size_text = superfile_ui._format_file_size(512)
        assert "512B" in size_text.plain

        # Test kilobytes
        size_text = superfile_ui._format_file_size(1536)  # 1.5K
        assert "1.5K" in size_text.plain

        # Test megabytes
        size_text = superfile_ui._format_file_size(1572864)  # 1.5M
        assert "1.5M" in size_text.plain

        # Test gigabytes
        size_text = superfile_ui._format_file_size(1610612736)  # 1.5G
        assert "1.5G" in size_text.plain

    def test_create_mini_progress_bar(self, superfile_ui):
        """Test mini progress bar creation"""
        # Test low percentage (green)
        bar = superfile_ui._create_mini_progress_bar(25, 10)
        assert "[green]" in bar
        assert "█" in bar
        assert "░" in bar

        # Test medium percentage (yellow)
        bar = superfile_ui._create_mini_progress_bar(65, 10)
        assert "[yellow]" in bar

        # Test high percentage (red)
        bar = superfile_ui._create_mini_progress_bar(90, 10)
        assert "[red]" in bar

    @patch('psutil.virtual_memory')
    @patch('psutil.cpu_percent')
    @patch('psutil.disk_partitions')
    @patch('psutil.disk_usage')
    def test_get_system_info(self, mock_disk_usage, mock_disk_partitions,
                           mock_cpu_percent, mock_virtual_memory, superfile_ui):
        """Test system information retrieval"""
        # Mock system calls
        mock_virtual_memory.return_value = Mock(
            percent=75.0, total=8000000000, available=2000000000
        )
        mock_cpu_percent.return_value = 45.5
        mock_disk_partitions.return_value = [
            Mock(mountpoint='/', device='/dev/sda1')
        ]
        mock_disk_usage.return_value = Mock(
            total=1000000000, used=600000000, free=400000000
        )

        info = superfile_ui._get_system_info()

        assert 'memory_percent' in info
        assert 'cpu_percent' in info
        assert 'disk_usage' in info
        assert info['memory_percent'] == 75.0
        assert info['cpu_percent'] == 45.5

    def test_get_cached_system_info(self, superfile_ui):
        """Test cached system information"""
        # Mock the system info method
        with patch.object(superfile_ui, '_get_system_info', return_value={'test': 'data'}) as mock_get_info:
            # First call should fetch new data
            info1 = superfile_ui._get_cached_system_info()
            assert mock_get_info.call_count == 1
            assert info1 == {'test': 'data'}

            # Second call within cache time should use cached data
            info2 = superfile_ui._get_cached_system_info()
            assert mock_get_info.call_count == 1  # No additional call
            assert info2 == {'test': 'data'}

    def test_toggle_sidebar(self, superfile_ui):
        """Test sidebar toggle functionality"""
        superfile_ui.create_layout()

        # Initially shown
        assert superfile_ui.show_sidebar is True

        # Toggle off
        superfile_ui.toggle_sidebar()
        assert superfile_ui.show_sidebar is False

        # Toggle on
        superfile_ui.toggle_sidebar()
        assert superfile_ui.show_sidebar is True

    def test_toggle_preview(self, superfile_ui):
        """Test preview panel toggle functionality"""
        superfile_ui.create_layout()

        # Initially shown
        assert superfile_ui.show_preview is True

        # Toggle off
        superfile_ui.toggle_preview()
        assert superfile_ui.show_preview is False

        # Toggle on
        superfile_ui.toggle_preview()
        assert superfile_ui.show_preview is True

    def test_set_sidebar_width(self, superfile_ui):
        """Test sidebar width setting"""
        superfile_ui.create_layout()

        # Test valid width
        superfile_ui.set_sidebar_width(25)
        assert superfile_ui.sidebar_width == 25

        # Test width clamping (too small)
        superfile_ui.set_sidebar_width(10)
        assert superfile_ui.sidebar_width == 15  # Minimum

        # Test width clamping (too large)
        superfile_ui.set_sidebar_width(50)
        assert superfile_ui.sidebar_width == 40  # Maximum

    def test_set_preview_width(self, superfile_ui):
        """Test preview panel width setting"""
        superfile_ui.create_layout()

        # Test valid width
        superfile_ui.set_preview_width(35)
        assert superfile_ui.preview_width == 35

        # Test width clamping (too small)
        superfile_ui.set_preview_width(15)
        assert superfile_ui.preview_width == 20  # Minimum

        # Test width clamping (too large)
        superfile_ui.set_preview_width(70)
        assert superfile_ui.preview_width == 60  # Maximum

    def test_get_layout_info(self, superfile_ui):
        """Test layout information retrieval"""
        superfile_ui.current_width = 100
        superfile_ui.current_height = 30
        superfile_ui.show_sidebar = True
        superfile_ui.show_preview = False
        superfile_ui.sidebar_width = 25
        superfile_ui.preview_width = 35

        info = superfile_ui.get_layout_info()

        assert info['width'] == 100
        assert info['height'] == 30
        assert info['show_sidebar'] is True
        assert info['show_preview'] is False
        assert info['sidebar_width'] == 25
        assert info['preview_width'] == 35

    def test_create_modal_overlay(self, superfile_ui):
        """Test modal overlay creation"""
        superfile_ui.current_width = 80
        superfile_ui.current_height = 24

        content = Panel(Text("Modal content"), title="Test")
        modal = superfile_ui.create_modal_overlay(content, "Test Modal")

        assert isinstance(modal, Panel)

    def test_render_progress_dialog(self, superfile_ui):
        """Test progress dialog rendering"""
        panel = superfile_ui.render_progress_dialog(
            operation="Copying files",
            progress=65.5,
            current_file="test.txt",
            speed="1.2 MB/s"
        )

        assert isinstance(panel, Panel)
        panel_content = str(panel)

        assert "Copying files" in panel_content
        assert "test.txt" in panel_content
        assert "1.2 MB/s" in panel_content

    def test_render_help_dialog(self, superfile_ui):
        """Test help dialog rendering"""
        panel = superfile_ui.render_help_dialog()

        assert isinstance(panel, Panel)
        panel_content = str(panel)

        assert "LaxyFile Keyboard Shortcuts" in panel_content
        assert "Navigation" in panel_content
        assert "File Operations" in panel_content
        assert "AI Features" in panel_content
        assert "↑↓ or j/k" in panel_content  # Navigation shortcuts
        assert "Space" in panel_content  # Selection shortcut

    def test_error_handling_in_rendering(self, superfile_ui):
        """Test error handling in various rendering methods"""
        # Test with None data
        panel = superfile_ui.render_file_panel(None)
        assert isinstance(panel, Panel)

        panel = superfile_ui.render_sidebar(None)
        assert isinstance(panel, Panel)

        panel = superfile_ui.render_footer(None)
        assert isinstance(panel, Panel)

    def test_responsive_design_adjustments(self, superfile_ui):
        """Test responsive design adjustments for different screen sizes"""
        superfile_ui.create_layout()

        # Test very narrow terminal
        superfile_ui._adjust_layout_for_size(50, 24)
        # Should hide sidebar and preview for narrow terminals

        # Test medium terminal
        superfile_ui._adjust_layout_for_size(100, 30)
        # Should show sidebar but might hide preview

        # Test wide terminal
        superfile_ui._adjust_layout_for_size(150, 40)
        # Should show all panels

    def test_theme_integration(self, superfile_ui):
        """Test theme integration across UI components"""
        # Mock theme manager to return specific colors
        mock_theme = {
            'file_panel_header': 'bright_blue',
            'file_panel_border': 'cyan',
            'cursor': 'bright_magenta',
            'directory_color': 'blue',
            'file_color': 'white'
        }

        with patch.object(superfile_ui.theme_manager, 'get_current_theme', return_value=mock_theme):
            # Test that theme colors are used in rendering
            panel = superfile_ui.render_file_panel(Mock(
                path=Path("/test"),
                files=[],
                current_selection=0,
                selected_files=set(),
                sort_type="name",
                reverse_sort=False,
                search_query=""
            ))

            # The panel should use theme colors (this is a basic test)
            assert isinstance(panel, Panel)

    @patch('laxyfile.ui.superfile_ui.psutil')
    def test_system_info_error_handling(self, mock_psutil, superfile_ui):
        """Test system info error handling when psutil fails"""
        # Mock psutil to raise exceptions
        mock_psutil.virtual_memory.side_effect = Exception("Memory error")
        mock_psutil.cpu_percent.side_effect = Exception("CPU error")
        mock_psutil.disk_partitions.side_effect = Exception("Disk error")

        info = superfile_ui._get_system_info()

        # Should return empty dict on errors, not crash
        assert isinstance(info, dict)

    def test_file_panel_with_large_file_list(self, superfile_ui, temp_dir):
        """Test file panel rendering with large number of files"""
        # Create many file info objects
        files = []
        for i in range(100):
            files.append(EnhancedFileInfo(
                path=temp_dir / f"file_{i:03d}.txt",
                name=f"file_{i:03d}.txt",
                size=1024 * i,
                modified=datetime.now(),
                is_dir=False,
                is_symlink=False,
                file_type="text",
                icon="📄"
            ))

        panel_data = PanelData(
            path=temp_dir,
            files=files,
            current_selection=0,
            selected_files=set(),
            sort_type="name",
            reverse_sort=False,
            search_query=""
        )

        # Should handle large file lists without crashing
        panel = superfile_ui.render_file_panel(panel_data)
        assert isinstance(panel, Panel)

    def test_unicode_and_emoji_handling(self, superfile_ui, temp_dir):
        """Test handling of Unicode characters and emojis in file names"""
        files = [
            EnhancedFileInfo(
                path=temp_dir / "测试文件.txt",
                name="测试文件.txt",
                size=1024,
                modified=datetime.now(),
                is_dir=False,
                is_symlink=False,
                file_type="text",
                icon="📄"
            ),
            EnhancedFileInfo(
                path=temp_dir / "🚀rocket.py",
                name="🚀rocket.py",
                size=2048,
                modified=datetime.now(),
                is_dir=False,
                is_symlink=False,
                file_type="code",
                icon="🐍"
            )
        ]

        panel_data = PanelData(
            path=temp_dir,
            files=files,
            current_selection=0,
            selected_files=set(),
            sort_type="name",
            reverse_sort=False,
            search_query=""
        )

        # Should handle Unicode and emojis without crashing
        panel = superfile_ui.render_file_panel(panel_data)
        assert isinstance(panel, Panel)
        panel_content = str(panel)
        assert "测试文件.txt" in panel_content
        assert "🚀rocket.py" in panel_content