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
from ..ui.theme import ThemeManager

class PanelManager:
    """Manages file browser panels"""

    def __init__(self, theme_manager: ThemeManager):
        self.theme_manager = theme_manager
        self.file_manager = FileManager()
        self.current_selection: Dict[str, int] = {"left": 0, "right": 0}
        self.selected_files: Dict[str, Set[Path]] = {"left": set(), "right": set()}
        self.show_hidden = False
        self.current_paths: Dict[str, Path] = {}

    def render_panel(self, path: Path, panel_name: str, is_active: bool = False) -> Panel:
        """Render a file browser panel"""
        try:
            files = self.file_manager.list_directory(path, self.show_hidden)

            if not files:
                empty_content = Align.center(
                    Text("Empty directory", style=self.theme_manager.get_style("info"))
                )
                border_style = "bright_blue" if is_active else self.theme_manager.get_style("border")
                return Panel(
                    empty_content,
                    title=f"📁 {path.name or str(path)}",
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
                # Selection indicator
                if i == current_selection and is_active:
                    selector = "▶"
                    name_style = "bold white on blue"
                elif i == current_selection:
                    selector = "►"
                    name_style = "bold white"
                elif file_info.path in self.selected_files.get(panel_name, set()):
                    selector = "●"
                    name_style = "bold yellow"
                else:
                    selector = " "
                    name_style = self.theme_manager.get_file_style(file_info.file_type)

                # Icon
                icon = self.theme_manager.get_file_icon(
                    file_info.file_type,
                    file_info.is_dir
                )

                # Name with style
                name_text = Text(file_info.name, style=name_style)

                # Size
                if file_info.is_dir:
                    size_text = Text("<DIR>", style="dim cyan")
                else:
                    size_text = Text(file_info.get_size_formatted(), style="dim")

                # Modified time
                modified_text = Text(
                    file_info.get_modified_formatted(),
                    style="dim"
                )

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
            error_content = Align.center(
                Text(f"Error: {str(e)}", style=self.theme_manager.get_style("error"))
            )
            return Panel(
                error_content,
                title=f"❌ Error",
                border_style=self.theme_manager.get_style("error")
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
