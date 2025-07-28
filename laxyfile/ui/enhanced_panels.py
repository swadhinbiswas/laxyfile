"""
Enhanced Panel Rendering System

This module provides advanced panel rendering with visual indicators,
selection states, and modern styling for LaxyFile.
"""

from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from datetime import datetime
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.columns import Columns
from rich.align import Align
from rich.box import ROUNDED, HEAVY, DOUBLE, ASCII
from rich.progress import Progress, BarColumn, TextColumn
from rich.tree import Tree
from rich.console import Console

from ..core.types import PanelData, EnhancedFileInfo, SortType
from ..core.interfaces import UIManagerInterface
from ..core.file_manager_service import FileManagerService
from ..core.error_handling_mixin import ErrorHandlingMixin
from .theme import ThemeManager
from ..utils.logger import Logger


class EnhancedPanelRenderer(ErrorHandlingMixin):
    """Enhanced panel rendering with advanced visual features"""

    def __init__(self, theme_manager: ThemeManager, console: Console):
        super().__init__()
        self.theme_manager = theme_manager
        self.console = console
        self.logger = Logger()

        # Get file manager service
        self.file_manager_service = FileManagerService.get_instance()

        # Visual settings
        self.show_file_icons = True
        self.show_file_sizes = True
        self.show_file_dates = True
        self.show_file_permissions = False
        self.show_selection_indicators = True
        self.use_alternating_colors = True

        # Box styles for different states
        self.box_styles = {
            'active': ROUNDED,
            'inactive': ROUNDED,
            'focused': HEAVY,
            'error': ASCII
        }

    def render_file_panel(self, panel_data: PanelData, is_active: bool = False,
                         is_focused: bool = False) -> Panel:
        """Render an enhanced file panel with advanced styling"""
        try:
            theme = self.theme_manager.get_current_theme()

            # Determine panel state and styling
            panel_state = self._get_panel_state(is_active, is_focused)
            border_style = self._get_border_style(panel_state, theme)
            box_style = self.box_styles.get(panel_state, ROUNDED)

            # Create enhanced table
            table = self._create_file_table(panel_data, theme, is_active)

            # Create panel title with enhanced information
            title = self._create_panel_title(panel_data, theme)

            # Create panel with appropriate styling
            panel = Panel(
                table,
                title=title,
                title_align="left",
                border_style=border_style,
                box=box_style,
                padding=(1, 1)
            )

            return panel

        except Exception as e:
            self.logger.error(f"Error rendering enhanced file panel: {e}")
            return self._create_error_panel(str(e))

    def _create_file_table(self, panel_data: PanelData, theme: Dict[str, Any],
                          is_active: bool) -> Table:
        """Create enhanced file table with advanced features"""
        # Create table with dynamic styling
        table = Table(
            show_header=True,
            header_style=f"bold {theme.get('table_header', 'white')} on {theme.get('table_header_bg', 'blue')}",
            border_style=theme.get('table_border', 'blue'),
            box=ROUNDED,
            padding=(0, 1),
            expand=True,
            min_width=50
        )

        # Add columns based on settings
        self._add_table_columns(table, theme)

        # Add file rows with enhanced styling
        for i, file_info in enumerate(panel_data.files):
            row_data = self._create_file_row(
                file_info, i, panel_data, theme, is_active
            )
            table.add_row(*row_data)

        return table

    def _add_table_columns(self, table: Table, theme: Dict[str, Any]) -> None:
        """Add columns to the file table based on settings"""
        # Selection indicator column
        if self.show_selection_indicators:
            table.add_column("", width=3, style="bold", no_wrap=True)

        # Icon column
        if self.show_file_icons:
            table.add_column("", width=3, no_wrap=True)

        # Name column (always shown)
        table.add_column(
            "Name",
            style=theme.get('file_name_color', 'white'),
            no_wrap=False,
            min_width=20,
            ratio=2
        )

        # Size column
        if self.show_file_sizes:
            table.add_column(
                "Size",
                justify="right",
                width=10,
                style=theme.get('file_size_color', 'cyan')
            )
  # Date column
        if self.show_file_dates:
            table.add_column(
                "Modified",
                width=12,
                style=theme.get('file_date_color', 'dim cyan')
            )

        # Permissions column (optional)
        if self.show_file_permissions:
            table.add_column(
                "Perms",
                width=8,
                style=theme.get('file_perms_color', 'yellow')
            )

        # Type column
        table.add_column(
            "Type",
            width=8,
            style=theme.get('file_type_color', 'dim')
        )

    def _create_file_row(self, file_info: EnhancedFileInfo, index: int,
                        panel_data: PanelData, theme: Dict[str, Any],
                        is_active: bool) -> List[Text]:
        """Create enhanced file row with visual indicators"""
        row_data = []

        # Determine file state
        is_current = (index == panel_data.current_selection and is_active)
        is_selected = file_info.path in panel_data.selected_files
        is_parent_dir = file_info.name == ".."

        # Selection indicator
        if self.show_selection_indicators:
            indicator = self._get_selection_indicator(is_current, is_selected, theme)
            row_data.append(indicator)

        # File icon
        if self.show_file_icons:
            icon = self._get_file_icon(file_info, theme)
            row_data.append(icon)

        # File name with styling
        name_text = self._get_file_name(file_info, is_current, is_selected, theme)
        row_data.append(name_text)

        # File size
        if self.show_file_sizes:
            size_text = self._get_file_size(file_info, theme)
            row_data.append(size_text)

        # File date
        if self.show_file_dates:
            date_text = self._get_file_date(file_info, theme)
            row_data.append(date_text)

        # File permissions
        if self.show_file_permissions:
            perms_text = self._get_file_permissions(file_info, theme)
            row_data.append(perms_text)

        # File type
        type_text = self._get_file_type(file_info, theme)
        row_data.append(type_text)

        return row_data

    def _get_selection_indicator(self, is_current: bool, is_selected: bool,
                               theme: Dict[str, Any]) -> Text:
        """Get selection indicator with appropriate styling"""
        if is_current and is_selected:
            return Text("▶●", style=f"bold {theme.get('cursor_selected', 'bright_green')}")
        elif is_current:
            return Text("▶ ", style=f"bold {theme.get('cursor', 'bright_magenta')}")
        elif is_selected:
            return Text(" ●", style=f"bold {theme.get('selected', 'bright_green')}")
        else:
            return Text("  ", style="dim")

    def _get_file_icon(self, file_info: EnhancedFileInfo, theme: Dict[str, Any]) -> Text:
        """Get file icon with appropriate styling"""
        icon = getattr(file_info, 'icon', '📄')

        # Apply special styling for different file types
        if file_info.is_dir:
            style = f"bold {theme.get('directory_icon_color', 'blue')}"
        elif file_info.is_symlink:
            style = f"bold {theme.get('symlink_color', 'cyan')}"
        elif getattr(file_info, 'is_executable', False):
            style = f"bold {theme.get('executable_color', 'green')}"
        else:
            style = "bold"

        return Text(icon, style=style)

    def _get_file_name(self, file_info: EnhancedFileInfo, is_current: bool,
                      is_selected: bool, theme: Dict[str, Any]) -> Text:
        """Get file name with appropriate styling"""
        name = file_info.name

        # Determine base style
        if is_current:
            style = f"bold {theme.get('file_panel_item_selected_fg', 'black')} on {theme.get('file_panel_item_selected_bg', 'white')}"
        elif file_info.is_dir:
            style = f"bold {theme.get('directory_color', 'blue')}"
        elif file_info.is_symlink:
            style = f"bold {theme.get('symlink_color', 'cyan')}"
        elif getattr(file_info, 'is_executable', False):
            style = f"bold {theme.get('executable_color', 'green')}"
        elif name.startswith('.'):
            style = f"dim {theme.get('hidden_color', 'gray')}"
        else:
            style = theme.get('file_color', 'white')

        # Add special indicators
        name_text = Text(name, style=style)

        # Add symlink target if applicable
        if file_info.is_symlink and hasattr(file_info, 'symlink_target'):
            name_text.append(f" → {file_info.symlink_target}", style="dim cyan")

        # Add security flags if any
        if hasattr(file_info, 'security_flags') and file_info.security_flags:
            for flag in file_info.security_flags[:2]:  # Show max 2 flags
                if flag == 'overly_permissive':
                    name_text.append(" ⚠️", style="yellow")
                elif flag == 'suspicious_extension':
                    name_text.append(" 🚨", style="red")
                elif flag == 'hidden_executable':
                    name_text.append(" 🔒", style="orange")

        return name_text

    def _get_file_size(self, file_info: EnhancedFileInfo, theme: Dict[str, Any]) -> Text:
        """Get formatted file size"""
        if file_info.is_dir:
            return Text("<DIR>", style=f"bold {theme.get('directory_color', 'cyan')}")

        size = file_info.size
        if size < 1024:
            return Text(f"{size}B", style="dim")
        elif size < 1024 * 1024:
            return Text(f"{size/1024:.1f}K", style="dim")
        elif size < 1024 * 1024 * 1024:
            return Text(f"{size/(1024*1024):.1f}M", style="cyan")
        else:
            return Text(f"{size/(1024*1024*1024):.1f}G", style="yellow")

    def _get_file_date(self, file_info: EnhancedFileInfo, theme: Dict[str, Any]) -> Text:
        """Get formatted file date"""
        try:
            if isinstance(file_info.modified, datetime):
                date_str = file_info.modified.strftime("%m/%d %H:%M")
            else:
                date_str = "??/??"

            # Color code based on age
            now = datetime.now()
            if isinstance(file_info.modified, datetime):
                age_days = (now - file_info.modified).days
                if age_days < 1:
                    style = "bright_green"  # Today
                elif age_days < 7:
                    style = "green"  # This week
                elif age_days < 30:
                    style = "yellow"  # This month
                else:
                    style = "dim"  # Older
            else:
                style = "dim"

            return Text(date_str, style=style)
        except:
            return Text("??/??", style="dim")

    def _get_file_permissions(self, file_info: EnhancedFileInfo, theme: Dict[str, Any]) -> Text:
        """Get formatted file permissions"""
        try:
            perms = getattr(file_info, 'permissions_octal', '???')

            # Color code based on permissions
            if perms in ['777', '666']:
                style = "bold red"  # Dangerous permissions
            elif perms.startswith('7'):
                style = "yellow"  # Owner has all permissions
            elif perms.startswith('6'):
                style = "green"  # Owner has read/write
            else:
                style = "dim"

            return Text(perms, style=style)
        except:
            return Text("???", style="dim")

    def _get_file_type(self, file_info: EnhancedFileInfo, theme: Dict[str, Any]) -> Text:
        """Get formatted file type"""
        file_type = getattr(file_info, 'file_type', 'unknown')

        # Truncate long type names
        if len(file_type) > 6:
            file_type = file_type[:6]

        # Color code by type
        type_colors = {
            'directory': 'blue',
            'image': 'magenta',
            'video': 'red',
            'audio': 'green',
            'code': 'cyan',
            'document': 'yellow',
            'archive': 'bright_blue',
            'executable': 'bright_green'
        }

        style = type_colors.get(file_type, 'dim')
        return Text(file_type.upper(), style=style)

    def _create_panel_title(self, panel_data: PanelData, theme: Dict[str, Any]) -> Text:
        """Create enhanced panel title with statistics"""
        title = Text()

        # Path with icon
        title.append("📁 ", style="bold cyan")

        # Truncate long paths
        path_str = str(panel_data.path)
        if len(path_str) > 50:
            path_str = "..." + path_str[-47:]

        title.append(path_str, style="bold white")

        # File statistics
        dir_count = sum(1 for f in panel_data.files if f.is_dir and f.name != "..")
        file_count = len(panel_data.files) - dir_count - (1 if any(f.name == ".." for f in panel_data.files) else 0)
        selected_count = len(panel_data.selected_files)

        stats = f" ({dir_count}📂 {file_count}📄"
        if selected_count > 0:
            stats += f" {selected_count}✓"
        stats += ")"
        title.append(stats, style="dim cyan")

        # Sort indicator
        sort_indicators = {
            SortType.NAME: "🔤",
            SortType.SIZE: "📏",
            SortType.MODIFIED: "🕒",
            SortType.TYPE: "🏷️",
            SortType.EXTENSION: "📎"
        }

        if hasattr(panel_data, 'sort_type'):
            sort_icon = sort_indicators.get(panel_data.sort_type, "")
            if sort_icon:
                title.append(f" {sort_icon}", style="yellow")
                if getattr(panel_data, 'sort_reverse', False):
                    title.append("↓", style="yellow")
                else:
                    title.append("↑", style="yellow")

        # Search indicator
        if panel_data.search_query:
            title.append(f" 🔍\"{panel_data.search_query}\"", style="bright_yellow")

        return title

    def _get_panel_state(self, is_active: bool, is_focused: bool) -> str:
        """Determine panel state for styling"""
        if is_focused:
            return 'focused'
        elif is_active:
            return 'active'
        else:
            return 'inactive'

    def _get_border_style(self, panel_state: str, theme: Dict[str, Any]) -> str:
        """Get border style based on panel state"""
        if panel_state == 'focused':
            return theme.get('file_panel_border_focused', 'bright_blue')
        elif panel_state == 'active':
            return theme.get('file_panel_border_active', 'blue')
        else:
            return theme.get('file_panel_border', 'dim blue')

    def _create_error_panel(self, error_message: str) -> Panel:
        """Create error panel for display issues"""
        return Panel(
            Text(f"Panel Error: {error_message}", style="bold red"),
            title="❌ Error",
            border_style="red",
            box=ROUNDED
        )

    def render_preview_panel(self, file_path: Optional[Path], content: str = "",
                           preview_type: str = "none") -> Panel:
        """Render preview panel with file content using safe file operations"""
        try:
            theme = self.theme_manager.get_current_theme()

            if not file_path or preview_type == "none":
                return Panel(
                    Align.center(Text("No preview available", style="dim")),
                    title="👁️ Preview",
                    border_style=theme.get('preview_border', 'dim'),
                    box=ROUNDED
                )

            # Check if file manager service is available
            if not self.file_manager_service.ensure_initialized():
                return Panel(
                    Align.center(Text("Preview unavailable - File manager loading...", style="yellow")),
                    title="⚠️ Loading Preview",
                    border_style="yellow",
                    box=ROUNDED
                )

            # Create preview content based on type
            if preview_type == "text":
                preview_content = Text(content[:1000])  # Limit content
                if len(content) > 1000:
                    preview_content.append("\n... [truncated]", style="dim")
            elif preview_type == "image":
                preview_content = Text(f"🖼️ Image Preview\n{file_path.name}\n\n{content}", style="cyan")
            elif preview_type == "video":
                preview_content = Text(f"🎬 Video Preview\n{file_path.name}\n\n{content}", style="magenta")
            elif preview_type == "audio":
                preview_content = Text(f"🎵 Audio Preview\n{file_path.name}\n\n{content}", style="green")
            else:
                preview_content = Text(f"📄 File Preview\n{file_path.name}\n\n{content}")

            return Panel(
                preview_content,
                title=f"👁️ Preview - {file_path.name}",
                title_align="left",
                border_style=theme.get('preview_border', 'cyan'),
                box=ROUNDED,
                padding=(1, 1)
            )

        except Exception as e:
            self.logger.error(f"Error rendering preview panel: {e}")
            return Panel(
                Text(f"Preview Error: {e}", style="red"),
                title="❌ Preview Error",
                border_style="red",
                box=ROUNDED
            )

    def set_visual_options(self, **options) -> None:
        """Set visual rendering options"""
        for key, value in options.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def get_visual_options(self) -> Dict[str, bool]:
        """Get current visual rendering options"""
        return {
            'show_file_icons': self.show_file_icons,
            'show_file_sizes': self.show_file_sizes,
            'show_file_dates': self.show_file_dates,
            'show_file_permissions': self.show_file_permissions,
            'show_selection_indicators': self.show_selection_indicators,
            'use_alternating_colors': self.use_alternating_colors
        }