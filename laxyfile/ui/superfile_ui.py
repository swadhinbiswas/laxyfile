"""
SuperFile-Inspired UI System

This module provides a comprehensive SuperFile-like interface with dual panels,
sidebar, modern styling, and responsive design for LaxyFile.
"""

import os
import psutil
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path
from datetime import datetime
from rich.layout import Layout
from rich.panel import Panel
from rich.console import Console
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.box import ROUNDED, HEAVY, DOUBLE
from rich.tree import Tree
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.rule import Rule

from ..core.interfaces import UIManagerInterface
from ..core.types import PanelData, SidebarData, StatusData, EnhancedFileInfo
from ..core.advanced_file_manager import AdvancedFileManager
from .theme import ThemeManager
from ..utils.logger import Logger


class SuperFileUI(UIManagerInterface):
    """SuperFile-inspired user interface manager with comprehensive rendering"""

    def __init__(self, theme_manager: ThemeManager, console: Console, config: Any = None):
        self.theme_manager = theme_manager
        self.console = console
        self.config = config
        self.logger = Logger()
        self.layout = None
        self.current_width = 0
        self.current_height = 0

        # UI state
        self.show_sidebar = True
        self.show_preview = True
        self.sidebar_width = 20
        self.preview_width = 30

        # Cache for performance
        self._cached_system_info = None
        self._last_system_info_update = None

    def create_layout(self) -> Layout:
        """Create the main SuperFile-inspired layout"""
        layout = Layout(name="root")

        # Main layout structure similar to SuperFile
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1, minimum_size=15),
            Layout(name="footer", size=4)
        )

        # Split main area into sidebar and panels
        layout["main"].split_row(
            Layout(name="sidebar", size=20, minimum_size=15),
            Layout(name="panels", ratio=1, minimum_size=40),
            Layout(name="preview", size=30, minimum_size=25)
        )

        # Split panels area for dual-pane view
        layout["panels"].split_row(
            Layout(name="left_panel", ratio=1),
            Layout(name="right_panel", ratio=1)
        )

        self.layout = layout
        return layout

    def render_file_panel(self, panel_data: PanelData) -> Panel:
        """Render a file panel with SuperFile styling"""
        try:
            # Get theme colors
            theme = self.theme_manager.get_current_theme()

            # Create table for file listing
            table = Table(
                show_header=True,
                header_style=f"bold {theme.get('file_panel_header', 'white')}",
                border_style=theme.get('file_panel_border', 'blue'),
                box=ROUNDED,
                padding=(0, 1),
                expand=True
            )

            # Add columns
            table.add_column("", width=2, style="bold")  # Selection indicator
            table.add_column("", width=3)  # Icon
            table.add_column("Name", style="white", no_wrap=False, min_width=20)
            table.add_column("Size", justify="right", width=10)
            table.add_column("Modified", width=12, style="dim")
            table.add_column("Type", width=8, style="dim")

            # Add files to table
            for i, file_info in enumerate(panel_data.files):
                # Determine selection state
                is_current = (i == panel_data.current_selection)
                is_selected = file_info.path in panel_data.selected_files

                # Selection indicator
                if is_current and is_selected:
                    cursor = "▶●"
                    cursor_style = f"bold {theme.get('cursor_selected', 'bright_green')}"
                elif is_current:
                    cursor = "▶ "
                    cursor_style = f"bold {theme.get('cursor', 'bright_magenta')}"
                elif is_selected:
                    cursor = " ●"
                    cursor_style = f"bold {theme.get('selected', 'bright_green')}"
                else:
                    cursor = "  "
                    cursor_style = "dim"

                # File icon
                icon = getattr(file_info, 'icon', '📄')

                # File name styling
                if is_current:
                    name_style = f"bold {theme.get('file_panel_item_selected_fg', 'black')} on {theme.get('file_panel_item_selected_bg', 'white')}"
                elif file_info.is_dir:
                    name_style = f"bold {theme.get('directory_color', 'blue')}"
                elif getattr(file_info, 'is_executable', False):
                    name_style = f"bold {theme.get('executable_color', 'green')}"
                elif file_info.name.startswith('.'):
                    name_style = f"dim {theme.get('hidden_color', 'gray')}"
                else:
                    name_style = theme.get('file_color', 'white')

                # Size formatting
                if file_info.is_dir:
                    size_text = Text("<DIR>", style=f"bold {theme.get('directory_color', 'cyan')}")
                else:
                    size_text = self._format_file_size(file_info.size)

                # Date formatting
                try:
                    mod_date = file_info.modified
                    if isinstance(mod_date, datetime):
                        date_str = mod_date.strftime("%m/%d %H:%M")
                    else:
                        date_str = "??/??"
                except:
                    date_str = "??/??"

                # File type
                file_type = getattr(file_info, 'file_type', 'unknown')

                # Add row
                table.add_row(
                    Text(cursor, style=cursor_style),
                    Text(icon, style="bold"),
                    Text(file_info.name, style=name_style),
                    size_text,
                    Text(date_str, style="dim cyan"),
                    Text(file_type[:6], style="dim")
                )

            # Create panel title
            path_str = str(panel_data.path)
            if len(path_str) > 40:
                path_str = "..." + path_str[-37:]

            # Count statistics
            dir_count = sum(1 for f in panel_data.files if f.is_dir and f.name != "..")
            file_count = len(panel_data.files) - dir_count - (1 if any(f.name == ".." for f in panel_data.files) else 0)
            selected_count = len(panel_data.selected_files)

            title = Text()
            title.append("📁 ", style="bold cyan")
            title.append(path_str, style="bold white")

            stats = f" ({dir_count}📂 {file_count}📄"
            if selected_count > 0:
                stats += f" {selected_count}✓"
            stats += ")"
            title.append(stats, style="dim cyan")

            # Search indicator
            if panel_data.search_query:
                title.append(f" 🔍{panel_data.search_query}", style="yellow")

            return Panel(
                table,
                title=title,
                title_align="left",
                border_style=theme.get('file_panel_border_active' if is_current else 'file_panel_border', 'blue'),
                box=ROUNDED,
                padding=(1, 1)
            )

        except Exception as e:
            self.logger.error(f"Error rendering file panel: {e}")
            return Panel(
                Text(f"Error: {e}", style="bold red"),
                title="❌ Panel Error",
                border_style="red",
                box=ROUNDED
            )

    def render_sidebar(self, sidebar_data: SidebarData) -> Panel:
        """Render sidebar with directory tree and system info"""
        try:
            theme = self.theme_manager.get_current_theme()

            # Create main content
            content = []

            # Current path section
            current_path_text = Text()
            current_path_text.append("📍 Current Path\n", style=f"bold {theme.get('sidebar_title', 'cyan')}")
            path_str = str(sidebar_data.current_path)
            if len(path_str) > 18:
                path_str = "..." + path_str[-15:]
            current_path_text.append(path_str, style="white")
            content.append(current_path_text)

            # Separator
            content.append(Rule(style=theme.get('sidebar_divider', 'dim')))

            # Bookmarks section
            if sidebar_data.bookmarks:
                bookmarks_text = Text()
                bookmarks_text.append("🔖 Bookmarks\n", style=f"bold {theme.get('sidebar_title', 'cyan')}")
                for i, bookmark in enumerate(sidebar_data.bookmarks[:5]):  # Show max 5
                    bookmark_name = bookmark.name if bookmark.name != bookmark.parent.name else str(bookmark)
                    if len(bookmark_name) > 16:
                        bookmark_name = bookmark_name[:13] + "..."
                    bookmarks_text.append(f"{i+1}. {bookmark_name}\n", style="white")
                content.append(bookmarks_text)
                content.append(Rule(style=theme.get('sidebar_divider', 'dim')))

            # Recent paths section
            if sidebar_data.recent_paths:
                recent_text = Text()
                recent_text.append("🕒 Recent\n", style=f"bold {theme.get('sidebar_title', 'cyan')}")
                for path in sidebar_data.recent_paths[:3]:  # Show max 3
                    path_name = path.name if path.name else str(path)
                    if len(path_name) > 16:
                        path_name = path_name[:13] + "..."
                    recent_text.append(f"• {path_name}\n", style="dim white")
                content.append(recent_text)
                content.append(Rule(style=theme.get('sidebar_divider', 'dim')))

            # System info section
            system_info = self._get_cached_system_info()
            if system_info:
                sys_text = Text()
                sys_text.append("💻 System\n", style=f"bold {theme.get('sidebar_title', 'cyan')}")

                # Memory usage
                if 'memory_percent' in system_info:
                    memory_bar = self._create_mini_progress_bar(system_info['memory_percent'], 12)
                    sys_text.append(f"RAM: {memory_bar} {system_info['memory_percent']:.0f}%\n", style="white")

                # Disk usage for current drive
                if 'disk_usage' in system_info and sidebar_data.current_path:
                    try:
                        # Find disk usage for current path
                        current_drive = str(sidebar_data.current_path).split('/')[0] if '/' in str(sidebar_data.current_path) else str(sidebar_data.current_path)[:3]
                        for mount, usage in system_info['disk_usage'].items():
                            if current_drive in mount or mount in current_drive:
                                disk_percent = (usage['used'] / usage['total']) * 100 if usage['total'] > 0 else 0
                                disk_bar = self._create_mini_progress_bar(disk_percent, 12)
                                sys_text.append(f"Disk: {disk_bar} {disk_percent:.0f}%\n", style="white")
                                break
                    except:
                        pass

                # CPU usage
                if 'cpu_percent' in system_info:
                    cpu_bar = self._create_mini_progress_bar(system_info['cpu_percent'], 12)
                    sys_text.append(f"CPU: {cpu_bar} {system_info['cpu_percent']:.0f}%", style="white")

                content.append(sys_text)

            # Combine all content
            sidebar_content = Text()
            for i, item in enumerate(content):
                if i > 0:
                    sidebar_content.append("\n")
                if isinstance(item, Text):
                    sidebar_content.append_text(item)
                elif isinstance(item, Rule):
                    sidebar_content.append("─" * 18 + "\n", style=theme.get('sidebar_divider', 'dim'))

            return Panel(
                sidebar_content,
                title=Text("🗂️ Navigation", style=f"bold {theme.get('sidebar_title', 'cyan')}"),
                title_align="left",
                border_style=theme.get('sidebar_border', 'blue'),
                box=ROUNDED,
                padding=(1, 1)
            )

        except Exception as e:
            self.logger.error(f"Error rendering sidebar: {e}")
            return Panel(
                Text(f"Sidebar Error: {e}", style="bold red"),
                title="❌ Sidebar",
                border_style="red",
                box=ROUNDED
            )

    def render_footer(self, status_data: StatusData) -> Panel:
        """Render footer with status and shortcuts"""
        try:
            theme = self.theme_manager.get_current_theme()

            # Create left side with status information
            status_text = Text()

            # Current file info
            if status_data.current_file:
                file_icon = getattr(status_data.current_file, 'icon', '📄')
                status_text.append(f"{file_icon} ", style="bold")
                status_text.append(status_data.current_file.name[:30], style="white")

                if not status_data.current_file.is_dir:
                    size_text = self._format_file_size(status_data.current_file.size)
                    status_text.append(f" ({size_text.plain})", style="dim")

            # Selection info
            if status_data.selected_count > 0:
                status_text.append(f" | {status_data.selected_count} selected", style="yellow")

            # Total files info
            status_text.append(f" | {status_data.total_files} items", style="dim")

            if status_data.total_size > 0:
                total_size = self._format_file_size(status_data.total_size)
                status_text.append(f" ({total_size.plain})", style="dim")

            # Operation status
            if status_data.operation_status:
                status_text.append(f" | {status_data.operation_status}", style="cyan")

            # AI status
            if status_data.ai_status:
                status_text.append(f" | 🤖 {status_data.ai_status}", style="green")

            # Create right side with keyboard shortcuts
            shortcuts_text = Text()
            hotkeys = [
                ("↕", "Nav"), ("Tab", "Switch"), ("Space", "Select"), ("Enter", "Open"),
                ("c", "Copy"), ("m", "Move"), ("d", "Del"), ("v", "View"),
                ("i", "AI"), ("t", "Theme"), ("p", "Preview"), ("?", "Help"), ("q", "Quit")
            ]

            for i, (key, action) in enumerate(hotkeys):
                if i > 0:
                    shortcuts_text.append(" ", style="dim")
                shortcuts_text.append(key, style=f"bold {theme.get('hotkey_color', 'yellow')}")
                shortcuts_text.append(":", style="dim")
                shortcuts_text.append(action, style="cyan")

            # Combine status and shortcuts
            footer_content = Columns([
                status_text,
                shortcuts_text
            ], align="left")

            return Panel(
                footer_content,
                border_style=theme.get('footer_border', 'blue'),
                box=ROUNDED,
                padding=(0, 1)
            )

        except Exception as e:
            self.logger.error(f"Error rendering footer: {e}")
            return Panel(
                Text("Status: Ready ✨", style="cyan"),
                border_style="cyan",
                box=ROUNDED
            )

    def handle_resize(self, width: int, height: int) -> None:
        """Handle terminal resize events"""
        self.current_width = width
        self.current_height = height

        # Adjust layout based on new dimensions
        if self.layout:
            self._adjust_layout_for_size(width, height)

    def apply_theme(self, theme_name: str) -> None:
        """Apply a theme to the UI"""
        self.theme_manager.set_theme(theme_name)

    def _adjust_layout_for_size(self, width: int, height: int) -> None:
        """Adjust layout components based on terminal size"""
        # Hide sidebar if terminal is too narrow
        if width < 80:
            self.layout["main"].split_row(
                Layout(name="panels", ratio=1),
                Layout(name="preview", size=25)
            )

        # Hide preview if terminal is very narrow
        if width < 60:
            self.layout["main"] = Layout(name="panels")

    def _format_file_size(self, size: int) -> Text:
        """Format file size with appropriate units"""
        try:
            if size < 1024:
                return Text(f"{size}B", style="dim")
            elif size < 1024 * 1024:
                return Text(f"{size/1024:.1f}K", style="dim")
            elif size < 1024 * 1024 * 1024:
                return Text(f"{size/(1024*1024):.1f}M", style="cyan")
            else:
                return Text(f"{size/(1024*1024*1024):.1f}G", style="yellow")
        except:
            return Text("0B", style="dim")

    def _create_mini_progress_bar(self, percentage: float, width: int = 10) -> str:
        """Create a mini progress bar for system info"""
        try:
            filled = int((percentage / 100) * width)
            empty = width - filled

            # Choose color based on percentage
            if percentage < 50:
                color = "green"
            elif percentage < 80:
                color = "yellow"
            else:
                color = "red"

            bar = "█" * filled + "░" * empty
            return f"[{color}]{bar}[/{color}]"
        except:
            return "░" * width

    def _get_cached_system_info(self) -> Optional[Dict[str, Any]]:
        """Get cached system information, updating if necessary"""
        try:
            current_time = datetime.now()

            # Update cache every 5 seconds
            if (self._cached_system_info is None or
                self._last_system_info_update is None or
                (current_time - self._last_system_info_update).seconds >= 5):

                self._cached_system_info = self._get_system_info()
                self._last_system_info_update = current_time

            return self._cached_system_info
        except Exception as e:
            self.logger.error(f"Error getting cached system info: {e}")
            return None

    def _get_system_info(self) -> Dict[str, Any]:
        """Get current system information"""
        try:
            info = {}

            # Memory information
            try:
                memory = psutil.virtual_memory()
                info['memory_percent'] = memory.percent
                info['memory_total'] = memory.total
                info['memory_available'] = memory.available
            except:
                pass

            # CPU information
            try:
                info['cpu_percent'] = psutil.cpu_percent(interval=0.1)
            except:
                pass

            # Disk information
            try:
                disk_usage = {}
                for partition in psutil.disk_partitions():
                    try:
                        usage = psutil.disk_usage(partition.mountpoint)
                        disk_usage[partition.mountpoint] = {
                            'total': usage.total,
                            'used': usage.used,
                            'free': usage.free
                        }
                    except:
                        continue
                info['disk_usage'] = disk_usage
            except:
                pass

            return info
        except Exception as e:
            self.logger.error(f"Error getting system info: {e}")
            return {}

    def render_header(self, title: str = "LaxyFile", subtitle: str = "") -> Panel:
        """Render header with title and subtitle"""
        try:
            theme = self.theme_manager.get_current_theme()

            # Create title with gradient effect
            title_text = Text()
            title_text.append("🚀 ", style="bold bright_yellow")

            # LaxyFile with individual letter colors (cappuccino theme)
            letters = [
                ("L", "#8B4513"), ("a", "#A0522D"), ("x", "#D2691E"), ("y", "#CD853F"),
                ("F", "#DEB887"), ("i", "#F4A460"), ("l", "#DAA520"), ("e", "#B8860B")
            ]

            for letter, color in letters:
                title_text.append(letter, style=f"bold {color}")

            title_text.append(" ✨", style="bold bright_yellow")

            # Subtitle with current theme and status
            if not subtitle:
                current_theme = self.theme_manager.current_theme_name if hasattr(self.theme_manager, 'current_theme_name') else 'cappuccino'
                subtitle = f"Modern Terminal File Manager • Theme: {current_theme.title()}"

            subtitle_text = Text(subtitle, style="dim white")

            # Combine title and subtitle
            header_content = Columns([
                Align.center(title_text),
                Align.right(subtitle_text)
            ])

            return Panel(
                header_content,
                border_style=theme.get('header_border', 'blue'),
                box=ROUNDED,
                padding=(0, 2)
            )

        except Exception as e:
            self.logger.error(f"Error rendering header: {e}")
            return Panel(
                Text("🚀 LaxyFile ✨", style="bold cyan"),
                border_style="cyan",
                box=ROUNDED
            )

    def toggle_sidebar(self) -> None:
        """Toggle sidebar visibility"""
        self.show_sidebar = not self.show_sidebar
        if self.layout:
            self._adjust_layout_for_size(self.current_width, self.current_height)

    def toggle_preview(self) -> None:
        """Toggle preview panel visibility"""
        self.show_preview = not self.show_preview
        if self.layout:
            self._adjust_layout_for_size(self.current_width, self.current_height)

    def set_sidebar_width(self, width: int) -> None:
        """Set sidebar width"""
        self.sidebar_width = max(15, min(width, 40))  # Clamp between 15-40
        if self.layout and self.show_sidebar:
            self.layout["sidebar"].size = self.sidebar_width

    def set_preview_width(self, width: int) -> None:
        """Set preview panel width"""
        self.preview_width = max(20, min(width, 60))  # Clamp between 20-60
        if self.layout and self.show_preview:
            self.layout["preview"].size = self.preview_width

    def get_layout_info(self) -> Dict[str, Any]:
        """Get current layout information"""
        return {
            'width': self.current_width,
            'height': self.current_height,
            'show_sidebar': self.show_sidebar,
            'show_preview': self.show_preview,
            'sidebar_width': self.sidebar_width,
            'preview_width': self.preview_width
        }

    def create_modal_overlay(self, content: Panel, title: str = "Modal") -> str:
        """Create a modal overlay for dialogs"""
        try:
            # Calculate overlay position (center of screen)
            modal_width = min(60, self.current_width - 4)
            modal_height = min(20, self.current_height - 4)

            overlay_x = (self.current_width - modal_width) // 2
            overlay_y = (self.current_height - modal_height) // 2

            # Create modal panel
            theme = self.theme_manager.get_current_theme()
            modal_panel = Panel(
                content,
                title=title,
                border_style=theme.get('modal_border_active', 'bright_blue'),
                box=DOUBLE,
                padding=(1, 2)
            )

            return modal_panel

        except Exception as e:
            self.logger.error(f"Error creating modal overlay: {e}")
            return Panel(Text("Modal Error", style="red"), title="Error")

    def render_progress_dialog(self, operation: str, progress: float,
                             current_file: str = "", speed: str = "") -> Panel:
        """Render progress dialog for file operations"""
        try:
            theme = self.theme_manager.get_current_theme()

            # Create progress content
            content = Text()
            content.append(f"Operation: {operation}\n\n", style="bold white")

            if current_file:
                content.append(f"Processing: {current_file}\n", style="cyan")

            # Progress bar
            progress_bar = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                expand=True
            )

            task = progress_bar.add_task("Progress", total=100)
            progress_bar.update(task, completed=progress)

            if speed:
                content.append(f"\nSpeed: {speed}", style="dim")

            return Panel(
                content,
                title="🔄 File Operation",
                border_style=theme.get('modal_border_active', 'bright_blue'),
                box=DOUBLE,
                padding=(1, 2)
            )

        except Exception as e:
            self.logger.error(f"Error rendering progress dialog: {e}")
            return Panel(Text("Progress Error", style="red"), title="Error")

    def render_help_dialog(self) -> Panel:
        """Render help dialog with keyboard shortcuts"""
        try:
            theme = self.theme_manager.get_current_theme()

            # Create help content
            help_content = Text()
            help_content.append("LaxyFile Keyboard Shortcuts\n\n", style="bold cyan")

            shortcuts = [
                ("Navigation", [
                    ("↑↓ or j/k", "Move cursor up/down"),
                    ("←→ or h/l", "Navigate directories"),
                    ("Tab", "Switch between panels"),
                    ("g/G", "Go to top/bottom"),
                    ("~", "Go to home directory"),
                    ("/", "Go to root directory")
                ]),
                ("File Operations", [
                    ("Space", "Select/deselect file"),
                    ("a", "Select all files"),
                    ("c", "Copy selected files"),
                    ("m", "Move selected files"),
                    ("d", "Delete selected files"),
                    ("r", "Rename file"),
                    ("n", "Create new directory")
                ]),
                ("View & Edit", [
                    ("Enter", "Open file/directory"),
                    ("v", "View file"),
                    ("e", "Edit file"),
                    ("p", "Toggle preview panel"),
                    (".", "Toggle hidden files")
                ]),
                ("AI Features", [
                    ("i", "Open AI assistant"),
                    ("F9", "Quick AI analysis"),
                    ("Ctrl+i", "AI chat mode")
                ]),
                ("Other", [
                    ("t", "Cycle themes"),
                    ("F1-F5", "Set specific theme"),
                    ("?", "Show this help"),
                    ("q", "Quit LaxyFile")
                ])
            ]

            for category, items in shortcuts:
                help_content.append(f"{category}:\n", style=f"bold {theme.get('help_category', 'yellow')}")
                for key, desc in items:
                    help_content.append(f"  {key:<12} {desc}\n", style="white")
                help_content.append("\n")

            return Panel(
                help_content,
                title="❓ Help",
                border_style=theme.get('modal_border_active', 'bright_blue'),
                box=DOUBLE,
                padding=(1, 2)
            )

        except Exception as e:
            self.logger.error(f"Error rendering help dialog: {e}")
            return Panel(Text("Help Error", style="red"), title="Error")