#!/usr/bin/env python3
"""
LaxyFile - Modern Terminal File Manager
A beautiful, feature-rich file manager inspired by Superfile
"""

import os
import sys
import signal
import threading
import queue
import time
import shutil
import datetime
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
import asyncio

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.columns import Columns
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.live import Live
from rich.prompt import Prompt, Confirm
from rich.traceback import install
from rich.rule import Rule
from rich.box import ROUNDED, DOUBLE, HEAVY
from rich.style import Style

from .core.file_manager import FileManager
from .core.config import Config
from .core.performance_optimizer import PerformanceOptimizer, PerformanceConfig
from .core.startup_optimizer import StartupOptimizer, StartupConfig
from .ui.theme import ThemeManager
from .ui.panels import PanelManager
from .ui.image_viewer import MediaViewer
from .ui.animation_optimizer import AnimationOptimizer, AnimationConfig, AnimationQuality
from .ai.assistant import AdvancedAIAssistant
from .utils.hotkeys import HotkeyManager
from .utils.navigation import NavigationThrottle, FastNavigationManager, KeyboardDebouncer
from .utils.logger import Logger

# Install rich traceback handler
install(show_locals=True)

class KeyHandler:
    """Advanced keyboard input handler with better terminal support"""

    def __init__(self):
        self.running = True
        self.key_queue = queue.Queue()
        self._setup_terminal()

    def _setup_terminal(self):
        """Setup terminal for optimal input handling"""
        try:
            import termios
            import tty
            self.has_termios = True
        except ImportError:
            self.has_termios = False

    def get_key_input(self) -> Optional[str]:
        """Get keyboard input with improved handling and no echo"""
        if not self.has_termios:
            return self._fallback_input()

        try:
            import termios
            import tty
            import select

            if not sys.stdin.isatty():
                return None

            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)

            try:
                # Use raw mode to prevent key echo and ensure clean input
                tty.setraw(fd, termios.TCSANOW)

                # Non-blocking read with shorter timeout for responsiveness
                ready, _, _ = select.select([sys.stdin], [], [], 0.02)
                if ready:
                    key = sys.stdin.read(1)

                    # Handle escape sequences
                    if ord(key) == 27:  # ESC
                        # Read potential escape sequence
                        ready, _, _ = select.select([sys.stdin], [], [], 0.005)
                        if ready:
                            seq = sys.stdin.read(1)
                            if seq == '[':
                                ready, _, _ = select.select([sys.stdin], [], [], 0.005)
                                if ready:
                                    final = sys.stdin.read(1)

                                    # Arrow keys
                                    if final == 'A':
                                        return 'UP'
                                    elif final == 'B':
                                        return 'DOWN'
                                    elif final == 'C':
                                        return 'RIGHT'
                                    elif final == 'D':
                                        return 'LEFT'
                                    # Function keys
                                    elif final == '5':
                                        return 'PAGE_UP'
                                    elif final == '6':
                                        return 'PAGE_DOWN'
                        # Return ESC if no sequence follows
                        return 'ESC'

                    # Special keys
                    if ord(key) == 9:  # Tab
                        return 'TAB'
                    elif ord(key) == 10 or ord(key) == 13:  # Enter
                        return 'ENTER'
                    elif ord(key) == 127 or ord(key) == 8:  # Backspace/Delete
                        return 'BACKSPACE'
                    elif ord(key) == 3:  # Ctrl+C
                        return 'CTRL_C'
                    elif ord(key) == 4:  # Ctrl+D
                        return 'CTRL_D'

                    # Regular printable characters
                    if 32 <= ord(key) <= 126:
                        return key

                return None

            finally:
                # Always restore terminal settings
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        except Exception:
            return self._fallback_input()

    def _fallback_input(self) -> Optional[str]:
        """Fallback input method"""
        try:
            import select
            if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                return sys.stdin.read(1)
        except:
            pass
        return None

class LaxyFileApp:
    """Modern file manager with Superfile-like interface"""

    def __init__(self):
        # Initialize console with optimized settings for performance
        self.console = Console(
            force_terminal=True,
            width=None,
            height=None,
            legacy_windows=False,
            color_system="truecolor",
            stderr=False,  # Prevent stderr capture that might cause display issues
            file=sys.stdout,  # Explicit stdout binding
            quiet=False,
            _environ=os.environ  # Cache environment for performance
        )

        # Core components - lazy initialization for faster startup
        self.config = Config()
        self.theme_manager = None  # Lazy init
        self.file_manager = None   # Lazy init
        self.panel_manager = None  # Lazy init
        self.media_viewer = None   # Lazy init
        self.ai_assistant = None   # Lazy init

        # Initialize navigation performance systems
        self.navigation_throttle = NavigationThrottle()
        self.fast_nav_manager = FastNavigationManager()
        self.keyboard_debouncer = KeyboardDebouncer()

        # Initialize hotkey manager
        self.hotkey_manager = HotkeyManager()
        self.logger = Logger()

        # Performance optimizations
        self._component_cache = {}
        self._startup_complete = False
        self._display_cache = {}
        self._last_display_hash = None

        # Initialize performance systems
        self.performance_optimizer = None  # Lazy init
        self.startup_optimizer = None      # Lazy init
        self.animation_optimizer = None    # Lazy init

        # Application state
        self.running = True
        self.current_path = {
            "left": self.config.get_startup_path(),
            "right": self.config.get_startup_path().parent
        }
        self.active_panel = self.config.config.startup_panel
        self.key_handler = KeyHandler()
        self.last_update = time.time()
        self.preview_enabled = self.config.get_ui().preview_pane
        self.ai_mode = False  # Track if we're in AI interaction mode

        # Initialize from session if enabled
        if self.config.config.remember_session:
            self._restore_session()

        # Setup layout
        self.layout = self.create_layout()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _get_theme_manager(self):
        """Lazy initialization of theme manager"""
        if self.theme_manager is None:
            self.theme_manager = ThemeManager(self.config)
            self._component_cache['theme_manager'] = self.theme_manager
        return self.theme_manager

    def _get_file_manager(self):
        """Lazy initialization of file manager"""
        if self.file_manager is None:
            self.file_manager = FileManager()
            self._component_cache['file_manager'] = self.file_manager
        return self.file_manager

    def _get_panel_manager(self):
        """Lazy initialization of panel manager"""
        if self.panel_manager is None:
            self.panel_manager = PanelManager(self._get_theme_manager())
            self._component_cache['panel_manager'] = self.panel_manager
        return self.panel_manager

    def _get_media_viewer(self):
        """Lazy initialization of media viewer"""
        if self.media_viewer is None:
            self.media_viewer = MediaViewer(self.console)
            self._component_cache['media_viewer'] = self.media_viewer
        return self.media_viewer

    def _get_ai_assistant(self):
        """Lazy initialization of AI assistant"""
        if self.ai_assistant is None:
            try:
                self.ai_assistant = AdvancedAIAssistant(self.config)
                self._component_cache['ai_assistant'] = self.ai_assistant
            except Exception as e:
                self.logger.warning(f"AI assistant initialization failed: {e}")
                # Create a dummy AI assistant for graceful degradation
                self.ai_assistant = None
        return self.ai_assistant

    def _get_performance_optimizer(self):
        """Lazy initialization of performance optimizer"""
        if self.performance_optimizer is None:
            perf_config = PerformanceConfig(
                max_concurrent_operations=self.config.get('performance.max_concurrent_operations', 10),
                chunk_size=self.config.get('performance.chunk_size', 100),
                memory_threshold_mb=self.config.get('performance.memory_threshold_mb', 500),
                lazy_loading_threshold=self.config.get('performance.lazy_loading_threshold', 1000),
                background_processing=self.config.get('performance.background_processing', True),
                use_threading=self.config.get('performance.use_threading', True),
                max_worker_threads=self.config.get('performance.max_worker_threads', 4)
            )
            self.performance_optimizer = PerformanceOptimizer(perf_config)
            self._component_cache['performance_optimizer'] = self.performance_optimizer
        return self.performance_optimizer

    def _get_animation_optimizer(self):
        """Lazy initialization of animation optimizer"""
        if self.animation_optimizer is None:
            # Determine animation quality based on terminal capabilities and config
            quality = AnimationQuality.MEDIUM
            if self.config.get('ui.high_performance_mode', False):
                quality = AnimationQuality.LOW
            elif self.config.get('ui.disable_animations', False):
                quality = AnimationQuality.DISABLED

            anim_config = AnimationConfig(
                quality=quality,
                max_fps=self.config.get('ui.max_fps', 30),
                enable_transitions=self.config.get('ui.enable_transitions', True),
                enable_cursor_animations=self.config.get('ui.enable_cursor_animations', True),
                enable_loading_animations=self.config.get('ui.enable_loading_animations', True),
                adaptive_quality=self.config.get('ui.adaptive_animation_quality', True)
            )
            self.animation_optimizer = AnimationOptimizer(anim_config)
            self._component_cache['animation_optimizer'] = self.animation_optimizer
        return self.animation_optimizer

    def _complete_startup(self):
        """Complete startup initialization after first use"""
        if not self._startup_complete:
            # Initialize all components that weren't lazy-loaded
            self._get_theme_manager()
            self._get_file_manager()
            self._get_panel_manager()
            self._get_media_viewer()

            # Initialize performance systems
            try:
                perf_optimizer = self._get_performance_optimizer()
                asyncio.create_task(perf_optimizer.initialize())
            except Exception as e:
                self.logger.warning(f"Performance optimizer initialization failed: {e}")

            try:
                self._get_animation_optimizer()
            except Exception as e:
                self.logger.warning(f"Animation optimizer initialization failed: {e}")

            self._startup_complete = True
            self.logger.info("Startup initialization complete")

    def _signal_handler(self, signum, frame):
        """Handle system signals gracefully"""
        self.quit()

    def _restore_session(self):
        """Restore session data"""
        try:
            left_path = self.config.get_session_data("left_path")
            right_path = self.config.get_session_data("right_path")
            active_panel = self.config.get_session_data("active_panel")

            if left_path and Path(left_path).exists():
                self.current_path["left"] = Path(left_path)
            if right_path and Path(right_path).exists():
                self.current_path["right"] = Path(right_path)
            if active_panel:
                self.active_panel = active_panel

        except Exception as e:
            self.logger.warning(f"Failed to restore session: {e}")

    def _save_session(self):
        """Save current session"""
        try:
            self.config.set_session_data("left_path", str(self.current_path["left"]))
            self.config.set_session_data("right_path", str(self.current_path["right"]))
            self.config.set_session_data("active_panel", self.active_panel)
        except Exception as e:
            self.logger.warning(f"Failed to save session: {e}")

    def create_layout(self):
        """Create the main layout structure"""
        layout = Layout(name="root")

        # Main layout structure
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1, minimum_size=15),
            Layout(name="footer", size=4)
        )

        # Split main area based on preview setting
        if self.preview_enabled:
            layout["main"].split_row(
                Layout(name="left_panel", ratio=1, minimum_size=30),
                Layout(name="right_panel", ratio=1, minimum_size=30),
                Layout(name="preview_panel", ratio=1, minimum_size=25)
            )
        else:
            layout["main"].split_row(
                Layout(name="left_panel", ratio=1),
                Layout(name="right_panel", ratio=1)
            )

        return layout

    def create_header(self) -> Panel:
        """Create beautiful header with gradients"""
        ui_config = self.config.get_ui()
        theme_manager = self._get_theme_manager()
        theme_style = theme_manager.get_style("header")

        # Create rainbow gradient title
        title_text = Text()
        title_text.append("🚀 ", style="bold bright_yellow")

        # LaxyFile with individual letter colors (cappuccino theme)
        letters = [
            ("L", "#8B4513"),  # Saddle brown
            ("a", "#A0522D"),  # Sienna
            ("x", "#D2691E"),  # Chocolate
            ("y", "#CD853F"),  # Peru
            ("F", "#DEB887"),  # Burlywood
            ("i", "#F4A460"),  # Sandy brown
            ("l", "#DAA520"),  # Goldenrod
            ("e", "#B8860B"),  # Dark goldenrod
        ]

        for letter, color in letters:
            title_text.append(letter, style=f"bold {color}")

        title_text.append(" ✨", style="bold bright_yellow")

        # Subtitle with current theme
        subtitle = Text()
        subtitle.append(" Modern Terminal File Manager ", style="dim white")
        theme_name = getattr(self.theme_manager.current_theme, 'name', str(self.theme_manager.current_theme))
        subtitle.append(f"• Theme: {theme_name.title()} ", style="dim cyan")
        subtitle.append(f"• Preview: {'On' if self.preview_enabled else 'Off'}", style="dim green" if self.preview_enabled else "dim red")

        # Combine title and subtitle
        header_content = Columns([
            Align.center(title_text),
            Align.right(subtitle)
        ])

        return Panel(
            header_content,
            style=theme_style,
            border_style=self.theme_manager.get_style("border", True),
            box=ROUNDED,
            padding=(0, 2)
        )

    def create_file_panel(self, panel_name: str, path: Path, is_active: bool) -> Panel:
        """Create beautiful file panel with modern styling"""
        try:
            files = self.file_manager.list_directory(path, self.panel_manager.show_hidden)
            current_selection = self.panel_manager.current_selection.get(panel_name, 0)
            selected_files = self.panel_manager.selected_files.get(panel_name, set())

            # Create table with modern styling
            table = Table(
                show_header=True,
                header_style="bold white on #34495E",
                border_style=self.theme_manager.get_style("border", is_active),
                box=ROUNDED,
                padding=(0, 1),
                expand=True,
                min_width=40
            )

            # Add columns
            table.add_column("", width=2, style="bold")  # Selection
            table.add_column("", width=3)  # Icon
            table.add_column("Name", style="white", no_wrap=False, min_width=20)
            table.add_column("Size", justify="right", width=8)
            table.add_column("Modified", width=12, style="dim")

            # Implement proper scrolling/pagination around current selection
            # Calculate actual displayable height based on terminal size
            terminal_height = self.console.size.height
            # Reserve space for: header panel (3), footer (2), table header (1), borders (2)
            # Be more aggressive with space usage to show more files
            reserved_space = 8  # Reduced from 11 to show more files
            available_height = max(10, terminal_height - reserved_space)  # Minimum 10 files visible
            max_files = min(available_height, self.config.get_ui().max_files_display)

            # Ensure selection is within bounds of all files
            if current_selection >= len(files):
                current_selection = len(files) - 1
                self.panel_manager.current_selection[panel_name] = current_selection
            elif current_selection < 0:
                current_selection = 0
                self.panel_manager.current_selection[panel_name] = current_selection

            # Calculate the visible window around the current selection
            if len(files) <= max_files:
                # All files fit in the display
                display_files = files
                display_start = 0
            else:
                # Need scrolling - center the selection in the visible window
                visible_height = max_files
                half_height = visible_height // 2

                # Calculate start position to center selection
                display_start = max(0, current_selection - half_height)

                # Ensure we don't go past the end
                if display_start + visible_height > len(files):
                    display_start = len(files) - visible_height

                # Ensure we don't go negative
                display_start = max(0, display_start)

                # Extract the visible slice
                display_files = files[display_start:display_start + visible_height]

            # Adjust current selection index for the visible window
            visible_selection = current_selection - display_start

            for i, file_info in enumerate(display_files):
                # Determine file states using the visible selection index
                is_current = (i == visible_selection and is_active)
                is_selected = file_info.path in selected_files

                # Selection indicator
                if is_current and is_selected:
                    cursor = "▶●"
                    cursor_style = "bold bright_green"
                elif is_current:
                    cursor = "▶ "
                    cursor_style = "bold bright_magenta"
                elif is_selected:
                    cursor = " ●"
                    cursor_style = "bold bright_green"
                else:
                    cursor = "  "
                    cursor_style = "dim"

                # Get file icon and style
                icon = self.theme_manager.get_file_icon(
                    file_info.file_type,
                    file_info.name,
                    file_info.is_dir,
                    file_info.is_symlink
                )

                icon_style = self.theme_manager.get_file_style(
                    file_info.file_type,
                    is_selected,
                    is_current
                )

                # File name with smart styling
                name_style = self.theme_manager.get_file_style(
                    file_info.file_type,
                    is_selected,
                    is_current
                )

                # Size formatting
                if file_info.is_dir:
                    size_text = Text("<DIR>", style="bold dim cyan")
                else:
                    size_text = Text.from_markup(
                        self.theme_manager.format_file_size(file_info.size)
                    )

                # Date formatting
                try:
                    mod_date = datetime.datetime.fromtimestamp(file_info.modified)
                    date_str = mod_date.strftime("%m/%d %H:%M")
                except:
                    date_str = "??/??"

                # Add row
                table.add_row(
                    Text(cursor, style=cursor_style),
                    Text(icon, style=icon_style),
                    Text(file_info.name, style=name_style),
                    size_text,
                    Text(date_str, style="dim cyan")
                )

            # Create panel title with path and stats
            path_str = str(path)
            if len(path_str) > 40:
                path_str = "..." + path_str[-37:]

            dir_count = sum(1 for f in files if f.is_dir and f.name != "..")
            file_count = len(files) - dir_count - (1 if any(f.name == ".." for f in files) else 0)
            selected_count = len(selected_files)

            title = Text()
            title.append("📁 ", style="bold cyan")
            title.append(path_str, style="bold white")

            # Add scrolling indicators if needed
            scroll_info = ""
            if len(files) > max_files:
                current_pos = current_selection + 1
                total_files = len(files)
                if display_start > 0:
                    scroll_info += "↑"
                if display_start + len(display_files) < len(files):
                    scroll_info += "↓"
                if scroll_info:
                    scroll_info = f" {scroll_info} [{current_pos}/{total_files}]"

            stats = f" ({dir_count}📂 {file_count}📄"
            if selected_count > 0:
                stats += f" {selected_count}✓"
            stats += ")"
            title.append(stats, style="dim cyan")

            # Add scroll indicators
            if scroll_info:
                title.append(scroll_info, style="dim yellow")

            return Panel(
                table,
                title=title,
                title_align="left",
                border_style=self.theme_manager.get_style("border", is_active),
                style=self.theme_manager.get_style("background") if not is_active else "",
                box=ROUNDED,
                padding=(1, 1)
            )

        except Exception as e:
            self.logger.error(f"Error creating panel: {e}")
            return Panel(
                Text(f"Error: {e}", style="bold red"),
                title="❌ Error",
                border_style="red",
                box=ROUNDED
            )

    def create_preview_panel(self) -> Panel:
        """Create preview panel for current file"""
        try:
            files = self.file_manager.list_directory(
                self.current_path[self.active_panel],
                self.panel_manager.show_hidden
            )
            current_file = self.panel_manager.get_current_file(self.active_panel, files)

            # Debug logging
            self.logger.debug(f"Preview: Active panel={self.active_panel}, Files={len(files)}, Current={current_file.name if current_file else None}")

            if not current_file or current_file.name == "..":
                return Panel(
                    Align.center(Text("No preview available", style="dim")),
                    title="👁️ Preview",
                    border_style="dim",
                    box=ROUNDED
                )

            # Use media viewer for preview with even larger dimensions for better quality
            self.logger.debug(f"Creating preview for: {current_file.path}")
            return self.media_viewer.create_preview_panel(current_file.path, 60, 40)

        except Exception as e:
            self.logger.error(f"Preview panel creation error: {e}")
            return Panel(
                Align.center(Text(f"Preview error: {e}", style="red")),
                title="❌ Preview Error",
                border_style="red",
                box=ROUNDED
            )

    def create_footer(self) -> Panel:
        """Create modern footer with status and shortcuts"""
        try:
            # Status information
            left_files = self.file_manager.list_directory(
                self.current_path["left"],
                self.panel_manager.show_hidden
            )
            right_files = self.file_manager.list_directory(
                self.current_path["right"],
                self.panel_manager.show_hidden
            )

            left_selected = len(self.panel_manager.selected_files.get("left", set()))
            right_selected = len(self.panel_manager.selected_files.get("right", set()))

            # Create status line
            status = Text()

            # Active panel indicator
            status.append("●" if self.active_panel == "left" else "○",
                         style="bold bright_magenta" if self.active_panel == "left" else "dim")
            status.append(f" L:{len(left_files)}", style="cyan")
            if left_selected > 0:
                status.append(f"({left_selected}✓)", style="green")

            status.append(" │ ", style="dim")

            status.append("●" if self.active_panel == "right" else "○",
                         style="bold bright_magenta" if self.active_panel == "right" else "dim")
            status.append(f" R:{len(right_files)}", style="cyan")
            if right_selected > 0:
                status.append(f"({right_selected}✓)", style="green")

            # Current file info
            files = left_files if self.active_panel == "left" else right_files
            if files:
                current_file = self.panel_manager.get_current_file(self.active_panel, files)
                if current_file:
                    status.append(" │ ", style="dim")
                    icon = self.theme_manager.get_file_icon(
                        current_file.file_type,
                        current_file.name,
                        current_file.is_dir
                    )
                    status.append(f"{icon} ", style="bold")
                    status.append(current_file.name[:25], style="white")

            # Keyboard shortcuts
            shortcuts = Text()
            hotkeys = [
                ("↕", "Nav"), ("Tab", "Switch"), ("Space", "Select"), ("Enter", "Open"),
                ("c", "Copy"), ("m", "Move"), ("d", "Del"), ("v", "View"),
                ("t", "Theme"), ("p", "Preview"), ("?", "Help"), ("q", "Quit")
            ]

            for i, (key, action) in enumerate(hotkeys):
                if i > 0:
                    shortcuts.append(" ", style="dim")
                shortcuts.append(key, style="bold yellow")
                shortcuts.append(":", style="dim")
                shortcuts.append(action, style="cyan")

            # Layout footer content
            footer_content = Columns([
                status,
                shortcuts
            ], align="left")

            return Panel(
                footer_content,
                style=self.theme_manager.get_style("footer"),
                border_style=self.theme_manager.get_style("border", True),
                box=ROUNDED,
                padding=(0, 1)
            )

        except Exception as e:
            return Panel(
                Text("Status: Ready ✨", style="cyan"),
                style=self.theme_manager.get_style("footer"),
                border_style="cyan",
                box=ROUNDED
            )

    def update_display(self):
        """Update display with improved stability and reduced flicker"""
        current_time = time.time()
        # Increased minimum interval to prevent excessive updates
        if current_time - self.last_update < 1.0 / 30:  # Max 30 FPS for stability
            return

        try:
            # Update header
            self.layout["header"].update(self.create_header())

            # Update panels
            left_panel = self.create_file_panel("left", self.current_path["left"], self.active_panel == "left")
            right_panel = self.create_file_panel("right", self.current_path["right"], self.active_panel == "right")

            self.layout["left_panel"].update(left_panel)
            self.layout["right_panel"].update(right_panel)

            # Update preview if enabled
            if self.preview_enabled:
                preview_panel = self.create_preview_panel()
                self.layout["preview_panel"].update(preview_panel)

            # Update footer
            self.layout["footer"].update(self.create_footer())

            self.last_update = current_time

        except Exception as e:
            self.logger.error(f"Display update error: {e}")

    def update_display_immediately(self):
        """Force immediate display update for ultra-fast navigation"""
        try:
            # Bypass all throttling for instant response
            self.layout["header"].update(self.create_header())

            # Update panels instantly
            left_panel = self.create_file_panel("left", self.current_path["left"], self.active_panel == "left")
            right_panel = self.create_file_panel("right", self.current_path["right"], self.active_panel == "right")

            self.layout["left_panel"].update(left_panel)
            self.layout["right_panel"].update(right_panel)

            # Update preview if enabled
            if self.preview_enabled:
                preview_panel = self.create_preview_panel()
                self.layout["preview_panel"].update(preview_panel)

            # Update footer instantly
            self.layout["footer"].update(self.create_footer())

            # Track the last update time without forced refresh
            self.last_update = time.time()

        except Exception as e:
            self.logger.error(f"Immediate display update error: {e}")

    async def handle_key(self, key: str):
        """Handle keyboard input with ultra-fast navigation and WASD support"""
        try:
            hotkeys = self.config.get_hotkeys()

            # Ultra-fast navigation - process instantly without caching delays
            # WASD Navigation (as requested)
            if key in ['s', 'S', 'j', 'J', 'DOWN']:
                # Down navigation - instant processing
                files = self.file_manager.list_directory(
                    self.current_path[self.active_panel],
                    self.panel_manager.show_hidden
                )
                self.panel_manager.navigate_down(self.active_panel, len(files))
                # Force immediate display update for ultra-fast response


            elif key in ['w', 'W', 'k', 'K', 'UP']:
                # Up navigation - instant processing
                self.panel_manager.navigate_up(self.active_panel)


            elif key in ['a', 'A', 'h', 'H', 'LEFT']:
                # Left navigation - go to parent directory
                self.navigate_to_parent()


            elif key in ['d', 'D', 'l', 'L', 'RIGHT', 'ENTER']:
                # Right navigation - enter directory or open file
                self.handle_enter()


            elif key == 'TAB':
                self.switch_panel()


            elif key == ' ':  # Space
                self.handle_selection()

            elif key in ['g']:
                self.panel_manager.navigate_to_top(self.active_panel)


            elif key in ['G']:
                files = self.file_manager.list_directory(self.current_path[self.active_panel], self.panel_manager.show_hidden)
                self.panel_manager.navigate_to_bottom(self.active_panel, len(files))


            elif key == 'PAGE_UP':
                # Page up navigation - jump by 10 items
                self.panel_manager.navigate_page_up(self.active_panel, 10)


            elif key == 'PAGE_DOWN':
                # Page down navigation - jump by 10 items
                files = self.file_manager.list_directory(self.current_path[self.active_panel], self.panel_manager.show_hidden)
                self.panel_manager.navigate_page_down(self.active_panel, len(files), 10)

            # File operations - reassigned since WASD are now navigation
            elif key in ['c', 'C']:
                self.handle_copy()
            elif key in ['m', 'M']:
                self.handle_move()
            elif key in ['x', 'X']:  # Changed from 'd' to 'x' for delete since 'd' is now right
                self.handle_delete()
            elif key in ['r', 'R']:
                self.handle_rename()
            elif key in ['n', 'N']:
                self.handle_new_dir()
            elif key in ['v', 'V']:
                self.handle_view()
            elif key in ['e', 'E']:
                self.handle_edit()
            elif key in ['z', 'Z']:  # New key for select all since 'a' is now left
                files = self.file_manager.list_directory(self.current_path[self.active_panel], self.panel_manager.show_hidden)
                self.panel_manager.select_all(self.active_panel, files)

            # Quick navigation
            elif key == '~':
                self.current_path[self.active_panel] = Path.home()
                self.panel_manager.reset_panel(self.active_panel)

            elif key == '/':
                self.current_path[self.active_panel] = Path('/')
                self.panel_manager.reset_panel(self.active_panel)

            elif key == '.':
                self.panel_manager.toggle_hidden_files()

            # Theme switching
            elif key in ['t', 'T']:
                self.cycle_theme()
            elif key == 'F1':
                self.set_theme("cappuccino")
            elif key == 'F2':
                self.set_theme("neon")
            elif key == 'F3':
                self.set_theme("ocean")
            elif key == 'F4':
                self.set_theme("sunset")
            elif key == 'F5':
                self.set_theme("forest")

            # UI toggles
            elif key in ['p', 'P']:
                self.toggle_preview()

            # AI features
            elif key in ['i', 'I']:
                await self.show_ai_assistant()
            elif key == 'F9':
                await self.quick_ai_analysis()

            # Help and quit
            elif key == '?':
                self.show_help()
            elif key in ['q', 'Q'] or key == 'CTRL_C':
                self.quit()

        except Exception as e:
            self.logger.error(f"Key handling error: {e}")

    async def show_ai_assistant(self):
        """Show AI assistant menu and handle queries"""
        try:
            if not self.ai_assistant.is_configured():
                self.show_message("❌ AI not configured. Set OPENROUTER_API_KEY environment variable.", "red")
                return

            # AI Assistant Menu
            menu_text = """
🤖 LaxyFile AI Assistant - Choose an option:

1. 💬 Chat with AI about current files
2. 🔍 Complete system analysis
3. 📁 Smart file organization
4. 🔒 Security audit
5. ⚡ Performance optimization
6. 🎬 Video analysis (selected files)
7. 🔄 Find duplicates
8. 📸 Media organization
9. 💾 Backup strategy
0. ❌ Cancel

Enter your choice (0-9):"""

            choice = self.get_user_input(menu_text)

            if choice == '0' or not choice:
                return

            # Show loading message
            self.console.print("🤖 AI is analyzing... Please wait.", style="cyan")

            current_path = self.current_path[self.active_panel]
            selected_files = self.panel_manager.get_selected_files(self.active_panel)

            response = ""

            if choice == '1':
                user_query = self.get_user_input("💬 Ask AI anything about your files:")
                if user_query:
                    response = await self.ai_assistant.query(user_query, current_path, selected_files, include_content=True)

            elif choice == '2':
                response = await self.ai_assistant.analyze_complete_system(current_path)

            elif choice == '3':
                response = await self.ai_assistant.smart_file_organization(current_path, selected_files)

            elif choice == '4':
                response = await self.ai_assistant.security_audit(current_path)

            elif choice == '5':
                response = await self.ai_assistant.performance_optimization(current_path)

            elif choice == '6':
                if selected_files:
                    video_files = [f for f in selected_files if f.suffix.lower() in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']]
                    if video_files:
                        response = await self.ai_assistant.create_video_analysis(video_files)
                    else:
                        response = "❌ No video files selected. Please select video files first."
                else:
                    response = "❌ No files selected. Please select video files first."

            elif choice == '7':
                response = await self.ai_assistant.duplicate_finder(current_path)

            elif choice == '8':
                response = await self.ai_assistant.media_organization(current_path)

            elif choice == '9':
                response = await self.ai_assistant.backup_strategy(current_path)

            # Display AI response
            if response:
                ai_panel = Panel(
                    Text(response, style="white"),
                    title="🤖 AI Assistant Response",
                    border_style="cyan",
                    box=ROUNDED,
                    padding=(1, 2)
                )
                self.console.print(ai_panel)
                self.console.input("[dim cyan]Press Enter to continue...[/dim cyan]")

        except Exception as e:
            self.show_message(f"❌ AI Assistant error: {e}", "red")

    async def quick_ai_analysis(self):
        """Quick AI analysis of current directory"""
        try:
            if not self.ai_assistant.is_configured():
                self.show_message("❌ AI not configured. Set OPENROUTER_API_KEY environment variable.", "red")
                return

            self.console.print("🔍 AI is performing quick analysis...", style="cyan")

            current_path = self.current_path[self.active_panel]
            selected_files = self.panel_manager.get_selected_files(self.active_panel)

            query = "Provide a quick analysis of this directory with file organization suggestions and any immediate recommendations."
            response = await self.ai_assistant.query(query, current_path, selected_files)

            # Create a compact display
            lines = response.split('\n')
            summary = '\n'.join(lines[:10])  # First 10 lines
            if len(lines) > 10:
                summary += f"\n... ({len(lines) - 10} more lines)"

            quick_panel = Panel(
                Text(summary, style="white"),
                title="🔍 Quick AI Analysis",
                border_style="yellow",
                box=ROUNDED,
                padding=(1, 1)
            )
            self.console.print(quick_panel)
            time.sleep(3)  # Show for 3 seconds

        except Exception as e:
            self.show_message(f"❌ Quick analysis failed: {e}", "red")

    def navigate_to_parent(self):
        """Navigate to parent directory"""
        current_path = self.current_path[self.active_panel]
        if current_path.parent != current_path:
            self.current_path[self.active_panel] = current_path.parent
            self.panel_manager.reset_panel(self.active_panel)

    def switch_panel(self):
        """Switch active panel"""
        self.active_panel = "right" if self.active_panel == "left" else "left"

    def handle_enter(self):
        """Handle Enter key - open file/directory"""
        try:
            files = self.file_manager.list_directory(
                self.current_path[self.active_panel],
                self.panel_manager.show_hidden
            )
            current_file = self.panel_manager.get_current_file(self.active_panel, files)

            if current_file:
                if current_file.name == "..":
                    self.navigate_to_parent()
                elif current_file.is_dir:
                    self.current_path[self.active_panel] = current_file.path
                    self.panel_manager.reset_panel(self.active_panel)
                else:
                    # Open file with default application
                    try:
                        subprocess.Popen(['xdg-open', str(current_file.path)],
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
                    except:
                        pass

        except Exception as e:
            self.logger.error(f"Enter handling error: {e}")

    def handle_selection(self):
        """Handle space key for file selection"""
        try:
            files = self.file_manager.list_directory(
                self.current_path[self.active_panel],
                self.panel_manager.show_hidden
            )
            current_file = self.panel_manager.get_current_file(self.active_panel, files)

            if current_file and current_file.name != "..":
                self.panel_manager.toggle_selection(self.active_panel, current_file.path)
        except Exception as e:
            self.logger.error(f"Selection handling error: {e}")

    def cycle_theme(self):
        """Cycle through available themes"""
        themes = self.theme_manager.get_available_themes()
        current_theme = getattr(self.theme_manager.current_theme, 'name', str(self.theme_manager.current_theme))

        try:
            current_index = themes.index(current_theme)
            next_index = (current_index + 1) % len(themes)
            self.set_theme(themes[next_index])
        except ValueError:
            self.set_theme(themes[0])

    def set_theme(self, theme_name: str):
        """Set specific theme"""
        self.theme_manager.set_theme(theme_name)
        self.show_message(f"Theme changed to: {theme_name.title()}", "green")

    def toggle_preview(self):
        """Toggle preview panel"""
        self.preview_enabled = not self.preview_enabled
        self.config.toggle_setting("ui.preview_pane")

        # Recreate layout
        self.layout = self.create_layout()

        status = "enabled" if self.preview_enabled else "disabled"
        self.show_message(f"Preview panel {status}", "green")

    def show_message(self, message: str, style: str = "green"):
        """Show temporary message to user"""
        self.console.print(f"[{style}]{message}[/{style}]")
        time.sleep(1)

    def get_user_input(self, prompt: str) -> str:
        """Get user input safely without echo issues"""
        try:
            # Temporarily show cursor for input
            self.console.print("\033[?25h", end="")
            result = self.console.input(f"[bold cyan]{prompt}[/bold cyan] ")
            # Hide cursor again
            self.console.print("\033[?25l", end="")
            return result
        except (KeyboardInterrupt, EOFError):
            # Hide cursor on exit
            self.console.print("\033[?25l", end="")
            return ""

    def confirm_action(self, message: str) -> bool:
        """Get user confirmation"""
        try:
            response = self.console.input(f"[bold yellow]{message} (y/N):[/bold yellow] ")
            return response.lower() in ['y', 'yes']
        except (KeyboardInterrupt, EOFError):
            return False

    def handle_copy(self):
        """Handle copy operation"""
        try:
            selected = self.panel_manager.get_selected_files(self.active_panel)
            if not selected:
                files = self.file_manager.list_directory(
                    self.current_path[self.active_panel],
                    self.panel_manager.show_hidden
                )
                current_file = self.panel_manager.get_current_file(self.active_panel, files)
                if current_file and current_file.name != "..":
                    selected = [current_file.path]

            if selected:
                target_panel = "right" if self.active_panel == "left" else "left"
                success = self.file_manager.copy_items(selected, self.current_path[target_panel])
                if success:
                    self.panel_manager.clear_selection(self.active_panel)
                    self.show_message(f"✨ Copied {len(selected)} items successfully!")
                else:
                    self.show_message("❌ Copy operation failed", "red")

        except Exception as e:
            self.show_message(f"❌ Copy error: {e}", "red")

    def handle_move(self):
        """Handle move operation"""
        try:
            selected = self.panel_manager.get_selected_files(self.active_panel)
            if not selected:
                files = self.file_manager.list_directory(
                    self.current_path[self.active_panel],
                    self.panel_manager.show_hidden
                )
                current_file = self.panel_manager.get_current_file(self.active_panel, files)
                if current_file and current_file.name != "..":
                    selected = [current_file.path]

            if selected:
                target_panel = "right" if self.active_panel == "left" else "left"
                success = self.file_manager.move_items(selected, self.current_path[target_panel])
                if success:
                    self.panel_manager.clear_selection(self.active_panel)
                    self.show_message(f"✨ Moved {len(selected)} items successfully!")
                else:
                    self.show_message("❌ Move operation failed", "red")

        except Exception as e:
            self.show_message(f"❌ Move error: {e}", "red")

    def handle_delete(self):
        """Handle delete operation"""
        try:
            selected = self.panel_manager.get_selected_files(self.active_panel)
            if not selected:
                files = self.file_manager.list_directory(
                    self.current_path[self.active_panel],
                    self.panel_manager.show_hidden
                )
                current_file = self.panel_manager.get_current_file(self.active_panel, files)
                if current_file and current_file.name != "..":
                    selected = [current_file.path]

            if selected:
                if self.confirm_action(f"🗑️ Delete {len(selected)} item(s)?"):
                    success = self.file_manager.delete_items(selected, self.config.config.use_trash)
                    if success:
                        self.panel_manager.clear_selection(self.active_panel)
                        self.show_message(f"🗑️ Deleted {len(selected)} items successfully!")
                    else:
                        self.show_message("❌ Delete operation failed", "red")

        except Exception as e:
            self.show_message(f"❌ Delete error: {e}", "red")

    def handle_rename(self):
        """Handle rename operation"""
        try:
            files = self.file_manager.list_directory(
                self.current_path[self.active_panel],
                self.panel_manager.show_hidden
            )
            current_file = self.panel_manager.get_current_file(self.active_panel, files)

            if current_file and current_file.name != "..":
                new_name = self.get_user_input(f"✏️ Rename '{current_file.name}' to:")
                if new_name and new_name != current_file.name:
                    if self.file_manager.rename_item(current_file.path, new_name):
                        self.show_message(f"✨ Renamed to '{new_name}' successfully!")
                    else:
                        self.show_message("❌ Rename operation failed", "red")

        except Exception as e:
            self.show_message(f"❌ Rename error: {e}", "red")

    def handle_new_dir(self):
        """Handle new directory creation"""
        try:
            name = self.get_user_input("📁 New directory name:")
            if name:
                if self.file_manager.create_directory(self.current_path[self.active_panel], name):
                    self.show_message(f"📁 Created directory '{name}' successfully!")
                else:
                    self.show_message("❌ Failed to create directory", "red")

        except Exception as e:
            self.show_message(f"❌ Directory creation error: {e}", "red")

    def handle_view(self):
        """Handle file viewing"""
        try:
            files = self.file_manager.list_directory(
                self.current_path[self.active_panel],
                self.panel_manager.show_hidden
            )
            current_file = self.panel_manager.get_current_file(self.active_panel, files)

            if current_file and current_file.is_file:
                # Use media viewer for full-screen display
                panel = self.media_viewer.display_file(current_file.path, 100, 40)
                self.console.print(panel)
                self.console.input("[dim cyan]Press Enter to continue...[/dim cyan]")

        except Exception as e:
            self.show_message(f"❌ View error: {e}", "red")

    def handle_edit(self):
        """Handle file editing"""
        try:
            files = self.file_manager.list_directory(
                self.current_path[self.active_panel],
                self.panel_manager.show_hidden
            )
            current_file = self.panel_manager.get_current_file(self.active_panel, files)

            if current_file and current_file.is_file:
                editor = self.config.get_editor()
                subprocess.call([editor, str(current_file.path)])

        except Exception as e:
            self.logger.error(f"Edit error: {e}")

    def show_help(self):
        """Show comprehensive help including AI features"""
        help_content = f"""
🚀 LaxyFile - Modern Terminal File Manager

📁 Navigation:
  j/k or ↑↓       Move up/down in file list
  h/l or ←→       Go to parent directory / enter directory
  g/G             Jump to top/bottom of list
  Tab             Switch between left and right panels
  Enter           Open file or enter directory

✨ File Operations:
  Space           Select/deselect current file
  a               Select all files in current panel
  c               Copy selected files to other panel
  m               Move selected files to other panel
  d               Delete selected files
  r               Rename current file
  n               Create new directory
  v               View file with media viewer
  e               Edit file with default editor

🎨 Themes & UI:
  t               Cycle through themes
  F1-F5           Set specific theme (Cappuccino, Neon, Ocean, Sunset, Forest)
  p               Toggle preview panel
  .               Toggle hidden files visibility

🤖 AI Assistant (Powered by Kimi AI):
  i               Open AI Assistant menu
  F9              Quick AI analysis of current directory

🔧 Quick Navigation:
  ~               Go to home directory
  /               Go to root directory

❓ Help & Exit:
  ?               Show this help screen
  q               Quit LaxyFile

💡 Current Theme: {getattr(self.theme_manager.current_theme, 'name', str(self.theme_manager.current_theme)).title()}
💡 Preview: {'Enabled' if self.preview_enabled else 'Disabled'}
💡 AI Status: {'🟢 Ready' if self.ai_assistant.is_configured() else '🔴 Not configured'}

🤖 AI Features:
  • Complete system analysis with device monitoring
  • Intelligent file organization suggestions
  • Security audits and vulnerability detection
  • Performance optimization recommendations
  • Video analysis and media organization
  • Duplicate file detection and cleanup
  • Smart backup strategy recommendations
  • Real-time content analysis and insights

Set OPENROUTER_API_KEY environment variable to enable AI features.
        """

        help_panel = Panel(
            Text(help_content, style="cyan"),
            title="📚 LaxyFile Help & AI Features",
            border_style="bold magenta",
            box=ROUNDED,
            padding=(1, 2)
        )

        self.console.print(help_panel)
        self.console.input("[dim cyan]Press Enter to return to file manager...[/dim cyan]")

    def run(self):
        """Main application loop with async AI support"""
        try:
            # Clear any existing terminal output and disable echo
            self._setup_clean_terminal()
            # Run the async main loop
            asyncio.run(self._async_run())
        except KeyboardInterrupt:
            self.quit()
        except Exception as e:
            self.console.print(f"[bold red]❌ Application error: {e}[/bold red]")
            self.quit()
        finally:
            # Restore terminal state
            self._restore_terminal()

    def _setup_clean_terminal(self):
        """Setup clean terminal environment"""
        try:
            # Clear screen and move cursor to top
            self.console.clear()
            # Disable cursor blinking to prevent flicker
            self.console.print("\033[?25l", end="")  # Hide cursor
        except:
            pass

    def _restore_terminal(self):
        """Restore terminal to normal state"""
        try:
            # Show cursor
            self.console.print("\033[?25h", end="")  # Show cursor
            # Clear screen one final time
            self.console.clear()
        except:
            pass

    async def _async_run(self):
        """Ultra-fast async main application loop optimized for navigation with stable display"""
        try:
            # Initial display setup - populate panels before starting main loop
            self.update_display_immediately()



            with Live(
                self.layout,
                console=self.console,
                screen=True,
                refresh_per_second=60,  # Reduced from 120 to prevent window jumping
                auto_refresh=False
            ) as live:

                while self.running:
                    # Handle input first for maximum responsiveness
                    key = self.key_handler.get_key_input()
                    if key:
                        # Process the key without showing it on screen
                        await self.handle_key(key)

                        # Update display content
                        self.update_display()

                        # Single refresh after key processing to prevent flicker
                        live.refresh()

                        # Slightly longer delay to prevent excessive refreshing
                        await asyncio.sleep(0.016)  # ~60 FPS to match refresh rate
                    else:
                        # No input - minimal delay without refresh to prevent jumping
                        await asyncio.sleep(0.016)

        except KeyboardInterrupt:
            self.quit()
        except Exception as e:
            self.console.print(f"[bold red]❌ Application error: {e}[/bold red]")
            self.quit()

    def quit(self):
        """Quit application gracefully"""
        self.running = False
        self._save_session()
        # Clean exit without extra display
        try:
            # Clear screen and show cursor
            self.console.print("\033[2J\033[H\033[?25h", end="")
            self.console.print("[bold green]✨ Thanks for using LaxyFile! 👋[/bold green]")
        except:
            print("✨ Thanks for using LaxyFile! 👋")

def main():
    """Main entry point"""
    try:
        app = LaxyFileApp()
        app.run()
    except KeyboardInterrupt:
        print("\n✨ Goodbye! 👋")
        sys.exit(0)
    except Exception as e:
        Console().print(f"[bold red]❌ Fatal error: {e}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()