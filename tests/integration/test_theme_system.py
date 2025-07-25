"""
Integration tests for theme system

Tests the integration between theme management, UI components, and user preferences
for comprehensive theming functionality.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from laxyfile.ui.theme import ThemeManager
from laxyfile.ui.superfile_ui import SuperFileUI
from laxyfile.core.advanced_file_manager import AdvancedFileManager
from laxyfile.core.types import PanelData, SidebarData, StatusData


@pytest.mark.integration
class TestThemeSystemIntegration:
    """Test theme system integration across all components"""

    @pytest.fixture
    def theme_system(self, mock_config, console, temp_dir):
        """Create integrated theme system"""
        theme_manager = ThemeManager()
        ui = SuperFileUI(theme_manager, console, mock_config)
        file_manager = AdvancedFileManager(mock_config)

        return {
            'theme_manager': theme_manager,
            'ui': ui,
            'file_manager': file_manager,
            'temp_dir': temp_dir
        }

    def test_theme_application_across_components(self, theme_system, sample_file_info):
        """Test theme application across all UI components"""
        theme_manager = theme_system['theme_manager']
        ui = theme_system['ui']
        temp_dir = theme_system['temp_dir']

        # Test different themes
        themes_to_test = ["cappuccino", "dracula", "nord", "catppuccin"]

        for theme_name in themes_to_test:
            # Apply theme
            theme_manager.set_theme(theme_name)
            ui.apply_theme(theme_name)

            # Create test data
            panel_data = PanelData(
                path=temp_dir,
                files=sample_file_info,
                current_selection=0,
                selected_files=set(),
                sort_type="name",
                reverse_sort=False,
                search_query=""
            )

            sidebar_data = SidebarData(
                current_path=temp_dir,
                bookmarks=[temp_dir / "bookmark1"],
                recent_paths=[temp_dir / "recent1"],
                directory_tree={}
            )

            status_data = StatusData(
                current_file=sample_file_info[0],
                selected_count=1,
                total_files=len(sample_file_info),
                total_size=sum(f.size for f in sample_file_info),
                operation_status="",
                ai_status=""
            )

            # Render all components with theme
            file_panel = ui.render_file_panel(panel_data)
            sidebar_panel = ui.render_sidebar(sidebar_data)
            footer_panel = ui.render_footer(status_data)
            header_panel = ui.render_header()

            # All components should render successfully
            assert file_panel is not None
            assert sidebar_panel is not None
            assert footer_panel is not None
            assert header_panel is not None

            # Verify theme is applied (basic check)
            current_theme = theme_manager.get_current_theme()
            assert current_theme is not None
            assert theme_manager.current_theme_name == theme_name

    @pytest.mark.asyncio
    async def test_dynamic_theme_switching_workflow(self, theme_system, sample_files):
        """Test dynamic theme switching during active file management"""
        theme_manager = theme_system['theme_manager']
        ui = theme_system['ui']
        file_manager = theme_system['file_manager']
        temp_dir = theme_system['temp_dir']

        # Step 1: Start with default theme
        initial_theme = "cappuccino"
        theme_manager.set_theme(initial_theme)

        # Step 2: Load file data
        files = await file_manager.list_directory(temp_dir)

        # Step 3: Create UI components with initial theme
        panel_data = PanelData(
            path=temp_dir,
            files=files,
            current_selection=0,
            selected_files=set(),
            sort_type="name",
            reverse_sort=False,
            search_query=""
        )

        initial_panel = ui.render_file_panel(panel_data)
        assert initial_panel is not None

        # Step 4: Switch themes dynamically
        theme_sequence = [cula", "nord", "catppuccin", "gruvbox"]

        for new_theme in theme_sequence:
            # Apply new theme
            theme_manager.set_theme(new_theme)
            ui.apply_theme(new_theme)

            # Re-render components with new theme
            updated_panel = ui.render_file_panel(panel_data)
            assert updated_panel is not None

            # Verify theme change
            current_theme = theme_manager.get_current_theme()
            assert current_theme is not None
            assert theme_manager.current_theme_name == new_theme

        # Step 5: Verify final theme state
        final_theme = theme_manager.get_current_theme()
        assert final_theme is not None
        assert theme_manager.current_theme_name == theme_sequence[-1]

    def test_theme_persistence_integration(self, theme_system):
        """Test theme persistence across sessions"""
        theme_manager = theme_system['theme_manager']

        # Step 1: Set custom theme
        custom_theme = "nord"
        theme_manager.set_theme(custom_theme)

        # Step 2: Save theme preferences
        theme_manager.save_preferences()

        # Step 3: Create new theme manager (simulate restart)
        new_theme_manager = ThemeManager()

        # Step 4: Load preferences
        new_theme_manager.load_preferences()

        # Step 5: Verify theme was restored
        assert new_theme_manager.current_theme_name == custom_theme

    def test_custom_theme_creation_integration(self, theme_system):
        """Test custom theme creation and application"""
        theme_manager = theme_system['theme_manager']
        ui = theme_system['ui']

        # Step 1: Create custom theme
        custom_theme_data = {
            "name": "custom_test_theme",
            "file_panel_header": "bright_cyan",
            "file_panel_border": "magenta",
            "cursor": "bright_yellow",
            "selected": "bright_green",
            "directory_color": "bright_blue",
            "file_color": "white",
            "sidebar_title": "bright_cyan",
            "sidebar_border": "cyan",
            "footer_border": "blue",
            "header_border": "bright_blue"
        }

        # Step 2: Register custom theme
        theme_manager.add_custom_theme("custom_test", custom_theme_data)

        # Step 3: Apply custom theme
        theme_manager.set_theme("custom_test")
        ui.apply_theme("custom_test")

        # Step 4: Verify custom theme is active
        current_theme = theme_manager.get_current_theme()
        assert current_theme["name"] == "custom_test_theme"
        assert current_theme["cursor"] == "bright_yellow"
        assert theme_manager.current_theme_name == "custom_test"

    def test_theme_export_import_integration(self, theme_system, temp_dir):
        """Test theme export and import functionality"""
        theme_manager = theme_system['theme_manager']

        # Step 1: Create and apply custom theme
        custom_theme = {
            "name": "export_test_theme",
            "file_panel_header": "red",
            "file_panel_border": "green",
            "cursor": "blue"
        }

        theme_manager.add_custom_theme("export_test", custom_theme)
        theme_manager.set_theme("export_test")

        # Step 2: Export theme
        export_path = temp_dir / "exported_theme.json"
        theme_manager.export_theme("export_test", export_path)

        assert export_path.exists()

        # Step 3: Create new theme manager and import
        new_theme_manager = ThemeManager()
        new_theme_manager.import_theme(export_path, "imported_test")

        # Step 4: Verify imported theme
        imported_theme = new_theme_manager.get_theme("imported_test")
        assert imported_theme is not None
        assert imported_theme["name"] == "export_test_theme"
        assert imported_theme["cursor"] == "blue"

    @pytest.mark.asyncio
    async def test_theme_responsive_design_integration(self, theme_system, sample_files):
        """Test theme integration with responsive design"""
        theme_manager = theme_system['theme_manager']
        ui = theme_system['ui']
        file_manager = theme_system['file_manager']
        temp_dir = theme_system['temp_dir']

        # Step 1: Apply theme
        theme_manager.set_theme("dracula")
        ui.apply_theme("dracula")

        # Step 2: Get file data
        files = await file_manager.list_directory(temp_dir)

        # Step 3: Test different screen sizes with theme
        screen_sizes = [
            (80, 24),   # Standard terminal
            (120, 30),  # Wide terminal
            (50, 20),   # Narrow terminal
            (200, 50)   # Very wide terminal
        ]

        for width, height in screen_sizes:
            # Apply screen size
            ui.handle_resize(width, height)

            # Create panel data
            panel_data = PanelData(
                path=temp_dir,
                files=files,
                current_selection=0,
                selected_files=set(),
                sort_type="name",
                reverse_sort=False,
                search_query=""
            )

            # Render components
            file_panel = ui.render_file_panel(panel_data)
            header = ui.render_header()

            # Should render successfully with theme at any size
            assert file_panel is not None
            assert header is not None

            # Verify layout info
            layout_info = ui.get_layout_info()
            assert layout_info['width'] == width
            assert layout_info['height'] == height

    def test_theme_accessibility_integration(self, theme_system, sample_file_info):
        """Test theme accessibility features"""
        theme_manager = theme_system['theme_manager']
        ui = theme_system['ui']
        temp_dir = theme_system['temp_dir']

        # Test high contrast themes
        high_contrast_themes = ["high_contrast_dark", "high_contrast_light"]

        for theme_name in high_contrast_themes:
            if theme_manager.has_theme(theme_name):
                # Apply high contrast theme
                theme_manager.set_theme(theme_name)
                ui.apply_theme(theme_name)

                # Create test data
                panel_data = PanelData(
                    path=temp_dir,
                    files=sample_file_info,
                    current_selection=0,
                    selected_files={sample_file_info[0].path},
                    sort_type="name",
                    reverse_sort=False,
                    search_query=""
                )

                # Render with high contrast
                panel = ui.render_file_panel(panel_data)
                assert panel is not None

                # Verify theme applied
                current_theme = theme_manager.get_current_theme()
                assert current_theme is not None

    def test_theme_performance_integration(self, theme_system, temp_dir):
        """Test theme system performance with large datasets"""
        theme_manager = theme_system['theme_manager']
        ui = theme_system['ui']

        # Create large file list
        large_file_list = []
        for i in range(100):
            from laxyfile.core.types import EnhancedFileInfo
            from datetime import datetime

            file_info = EnhancedFileInfo(
                path=temp_dir / f"file_{i:03d}.txt",
                name=f"file_{i:03d}.txt",
                size=1024 * i,
                modified=datetime.now(),
                is_dir=False,
                is_symlink=False,
                file_type="text",
                icon="📄"
            )
            large_file_list.append(file_info)

        # Test theme switching with large dataset
        themes = ["cappuccino", "dracula", "nord"]

        for theme_name in themes:
            # Apply theme
            theme_manager.set_theme(theme_name)
            ui.apply_theme(theme_name)

            # Create panel with large dataset
            panel_data = PanelData(
                path=temp_dir,
                files=large_file_list,
                current_selection=0,
                selected_files=set(),
                sort_type="name",
                reverse_sort=False,
                search_query=""
            )

            # Render should complete efficiently
            import time
            start_time = time.time()
            panel = ui.render_file_panel(panel_data)
            end_time = time.time()

            assert panel is not None
            # Should complete within reasonable time
            assert (end_time - start_time) < 1.0  # 1 second max

    def test_theme_error_handling_integration(self, theme_system):
        """Test theme system error handling"""
        theme_manager = theme_system['theme_manager']
        ui = theme_system['ui']

        # Test invalid theme application
        invalid_theme = "nonexistent_theme"

        # Should handle gracefully
        try:
            theme_manager.set_theme(invalid_theme)
            ui.apply_theme(invalid_theme)
        except Exception:
            # Should not crash, might fall back to default
            pass

        # Should still have a valid theme
        current_theme = theme_manager.get_current_theme()
        assert current_theme is not None

        # Test corrupted theme data
        corrupted_theme = {
            "name": "corrupted_theme",
            # Missing required fields
        }

        try:
            theme_manager.add_custom_theme("corrupted", corrupted_theme)
            theme_manager.set_theme("corrupted")
        except Exception:
            # Should handle gracefully
            pass

        # Should still function
        current_theme = theme_manager.get_current_theme()
        assert current_theme is not None