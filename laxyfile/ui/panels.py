"""
Panel Management for LaxyFile
"""

from pathlib import Path
from typing import Dict, Set, Optional, List
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align

from ..core.file_manager import FileManager, FileInfo
from ..core.file_manager_service import FileManagerService
from ..core.error_handling_mixin import ErrorHandlingMixin
from ..ui.theme import ThemeManager

class PanelManager(ErrorHandlingMixin):
    """Manages file browser panels with robust error handling"""

    def __init__(self, theme_manager: ThemeManager):
        super().__init__()
        self.theme_manager = theme_manager
        self.file_manager_service = FileManagerService.get_instance()
        self.current_selection: Dict[str, int] = {"left": 0, "right": 0}
        self.selected_files: Dict[str, Set[Path]] = {"left": set(), "right": set()}
        self.show_hidden = False
        self.current_paths: Dict[str, Path] = {}

        # Ensure file manager is initialized
        if not self.file_manager_service.ensure_initialized():
            self.logger.warning("File manager service not available during PanelManager initialization")

    def render_panel(self, path: Path, panel_name: str, is_active: bool = False) -> Panel:
        """Render a file browser panel with robust error handling"""
        try:
            # Use safe file operation to get directory listing
            files = self.safe_file_operation(
                operation=lambda: self.file_manager_service.list_directory(path, self.show_hidden),
                fallback_value=[],
                cache_key=f"list_dir_{path}_{self.show_hidden}",
                max_retries=2
            )

            # Handle empty directory or error case
            if not files:
                # Check if this is an error case or truly empty directory
                if not self.file_manager_service.is_healthy():
                    error_content = Align.center(
                        Text("File manager unavailable - Loading...", style="yellow")
                    )
                    border_style = "yellow"
                    title = "⚠️ Loading..."
                else:
                    error_content = Align.center(
                        Text("Empty directory", style="dim cyan")
                    )
                    border_style = "bright_blue" if is_active else self.theme_manager.get_style("border")
                    title = f"📁 {path.name or str(path)}"

                return Panel(
                    error_content,
                    title=title,
                    border_style=border_style
                )

            # Create file table
            table = Table(show_header=True, header_style="bold")
            table.add_column("", width=2)  # Selection indicator
            table.add_column("📎", width=3)  # Icon
            table.add_column("Name", style="white", no_wrap=False, min_width=20)
            table.add_column("Size", justify="right", width=10)
            table.add_column("Modified", width=16)

            current_selection = self.current_selection.get(panel_name, 0)

            # Ensure selection is within bounds
            if current_selection >= len(files):
                current_selection = len(files) - 1
                self.current_selection[panel_name] = current_selection
            elif current_selection < 0:
                current_selection = 0
                self.current_selection[panel_name] = current_selection

            for i, file_info in enumerate(files):
                # Handle different file info formats (dict vs FileInfo object)
                if isinstance(file_info, dict):
                    # Fallback format from error handling
                    name = file_info.get('name', 'Unknown')
                    is_dir = file_info.get('is_dir', False)
                    size = file_info.get('size', 0)
                    modified = file_info.get('modified', 0)
                    file_path = file_info.get('path', path / name)
                    file_type = file_info.get('file_type', 'unknown')
                else:
                    # Normal FileInfo object
                    name = file_info.name
                    is_dir = file_info.is_dir
                    size = file_info.size
                    modified = file_info.modified
                    file_path = file_info.path
                    file_type = getattr(file_info, 'file_type', 'unknown')

                # Selection indicator
                if i == current_selection and is_active:
                    selector = "▶"
                    name_style = "bold white on blue"
                elif i == current_selection:
                    selector = "►"
                    name_style = "bold white"
                elif file_path in self.selected_files.get(panel_name, set()):
                    selector = "●"
                    name_style = "bold yellow"
                else:
                    selector = " "
                    name_style = self.theme_manager.get_file_style(file_type, False, False) if hasattr(self.theme_manager, 'get_file_style') else "white"

                # Icon
                if hasattr(self.theme_manager, 'get_file_icon'):
                    icon = self.theme_manager.get_file_icon(file_type, name, is_dir, False)
                else:
                    icon = "📁" if is_dir else "📄"

                # Name with style
                name_text = Text(name, style=name_style)

                # Size
                if is_dir:
                    size_text = Text("<DIR>", style="dim cyan")
                else:
                    # Format size
                    if hasattr(file_info, 'get_size_formatted') and not isinstance(file_info, dict):
                        size_text = Text(file_info.get_size_formatted(), style="dim")
                    else:
                        # Manual size formatting
                        if size < 1024:
                            size_str = f"{size}B"
                        elif size < 1024 * 1024:
                            size_str = f"{size/1024:.1f}K"
                        elif size < 1024 * 1024 * 1024:
                            size_str = f"{size/(1024*1024):.1f}M"
                        else:
                            size_str = f"{size/(1024*1024*1024):.1f}G"
                        size_text = Text(size_str, style="dim")

                # Modified time
                if hasattr(file_info, 'get_modified_formatted') and not isinstance(file_info, dict):
                    modified_text = Text(file_info.get_modified_formatted(), style="dim")
                else:
                    # Manual time formatting
                    try:
                        import time as time_module
                        if isinstance(modified, (int, float)):
                            modified_str = time_module.strftime("%m/%d %H:%M", time_module.localtime(modified))
                        else:
                            modified_str = str(modified)[:16] if modified else "??/??"
                    except:
                        modified_str = "??/??"
                    modified_text = Text(modified_str, style="dim")

                table.add_row(
                    selector,
                    icon,
                    name_text,
                    size_text,
                    modified_text
                )

            # Panel title with path and file count
            selected_count = len(self.selected_files.get(panel_name, set()))
            if selected_count > 0:
                title = f"📁 {path.name or str(path)} ({len(files)} items, {selected_count} selected)"
            else:
                title = f"📁 {path.name or str(path)} ({len(files)} items)"

            # Different border style for active panel
            border_style = "bright_blue" if is_active else self.theme_manager.get_style("border")

            return Panel(
                table,
                title=title,
                border_style=border_style,
                padding=(0, 1)
            )

        except Exception as e:
            self.handle_file_manager_error(e, "render_panel")
            error_content = Align.center(
                Text(f"Panel Error: {str(e)}", style="red")
            )
            return Panel(
                error_content,
                title=f"❌ Error",
                border_style="red"
            )

    def navigate_up(self, panel_name: str):
        """Move selection up"""
        current = self.current_selection.get(panel_name, 0)
        self.current_selection[panel_name] = max(0, current - 1)

    def navigate_down(self, panel_name: str, max_items: int):
        """Move selection down"""
        if max_items <= 0:
            return
        current = self.current_selection.get(panel_name, 0)
        self.current_selection[panel_name] = min(max_items - 1, current + 1)

    def navigate_to_top(self, panel_name: str):
        """Move selection to top"""
        self.current_selection[panel_name] = 0

    def navigate_to_bottom(self, panel_name: str, max_items: int):
        """Move selection to bottom"""
        if max_items > 0:
            self.current_selection[panel_name] = max_items - 1

    def navigate_page_up(self, panel_name: str, page_size: int = 10):
        """Move selection up by page"""
        current = self.current_selection.get(panel_name, 0)
        self.current_selection[panel_name] = max(0, current - page_size)

    def navigate_page_down(self, panel_name: str, max_items: int, page_size: int = 10):
        """Move selection down by page"""
        if max_items <= 0:
            return
        current = self.current_selection.get(panel_name, 0)
        self.current_selection[panel_name] = min(max_items - 1, current + page_size)

    def get_current_file(self, panel_name: str, files: List[FileInfo]) -> Optional[FileInfo]:
        """Get the currently selected file"""
        if not files:
            return None

        current_selection = self.current_selection.get(panel_name, 0)
        if 0 <= current_selection < len(files):
            return files[current_selection]
        return None

    def toggle_selection(self, panel_name: str, file_path: Path):
        """Toggle selection of a file"""
        if panel_name not in self.selected_files:
            self.selected_files[panel_name] = set()

        if file_path in self.selected_files[panel_name]:
            self.selected_files[panel_name].remove(file_path)
        else:
            self.selected_files[panel_name].add(file_path)

    def get_selected_files(self, panel_name: str = None) -> List[Path]:
        """Get list of selected files"""
        if panel_name:
            return list(self.selected_files.get(panel_name, set()))
        else:
            # Return all selected files from both panels
            all_selected = []
            for panel_files in self.selected_files.values():
                all_selected.extend(list(panel_files))
            return all_selected

    def select_all(self, panel_name: str, files: List[FileInfo]):
        """Select all files in panel"""
        if panel_name not in self.selected_files:
            self.selected_files[panel_name] = set()

        # Select all files except ".."
        for file_info in files:
            if file_info.name != "..":
                self.selected_files[panel_name].add(file_info.path)

    def clear_selection(self, panel_name: str):
        """Clear all selections in panel"""
        if panel_name in self.selected_files:
            self.selected_files[panel_name].clear()

    def invert_selection(self, panel_name: str, files: List[FileInfo]):
        """Invert selection in panel"""
        if panel_name not in self.selected_files:
            self.selected_files[panel_name] = set()

        current_selected = self.selected_files[panel_name].copy()
        self.selected_files[panel_name].clear()

        for file_info in files:
            if file_info.name != ".." and file_info.path not in current_selected:
                self.selected_files[panel_name].add(file_info.path)

    def toggle_hidden_files(self):
        """Toggle showing hidden files"""
        self.show_hidden = not self.show_hidden

    def get_selection_count(self, panel_name: str) -> int:
        """Get number of selected files in panel"""
        return len(self.selected_files.get(panel_name, set()))

    def is_file_selected(self, panel_name: str, file_path: Path) -> bool:
        """Check if file is selected"""
        return file_path in self.selected_files.get(panel_name, set())

    def reset_panel(self, panel_name: str):
        """Reset panel state"""
        self.current_selection[panel_name] = 0
        if panel_name in self.selected_files:
            self.selected_files[panel_name].clear()
