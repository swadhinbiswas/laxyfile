"""
Modern Theme Management System with comprehensive color schemes inspired by Superfile
Supports multiple popular themes from the terminal community
"""

from typing import Dict, Any, Optional
from rich.style import Style
from ..core.config import Config

class ThemeManager:
    """Advanced theme management system inspired by Superfile's extensive theme support"""

    def __init__(self, config: Config):
        self.config = config
        self.current_theme = config.get_theme()
        self._setup_themes()

    def _setup_themes(self):
        """Setup comprehensive theme collection inspired by popular terminal themes"""
        self.themes = {
            # Default theme - Modern and clean
            "default": {
                "header": "bold white on #44475A",
                "footer": "white on #6272A4",
                "border_active": "#8BE9FD",
                "border_inactive": "#6272A4",
                "background": "#282A36",
                "file": "#F8F8F2",
                "directory": "bold #8BE9FD",
                "selected": "#282A36 on #50FA7B",
                "current": "#282A36 on #FFB86C",
                "current_selected": "#282A36 on #FF79C6",
                "error": "bold #FF5555",
                "success": "bold #50FA7B",
                "warning": "bold #F1FA8C",
                "info": "bold #8BE9FD",
                "image": "bold #FF79C6",
                "video": "bold #BD93F9",
                "audio": "bold #FF6B6B",
                "code": "bold #50FA7B",
                "archive": "bold #F1FA8C",
                "document": "bold #8BE9FD",
                "executable": "bold #FF5555",
                "symlink": "bold #6BE5FD",
                "cursor": "#FFB86C",
                "hint": "#6272A4",
                "cancel": "#FF5555",
                "confirm": "#50FA7B",
                "file_fg": "#F8F8F2",
                "file_bg": "#282A36",
                "sidebar_title": "bold #FF79C6",
                "sidebar_divider": "#44475A",
                "help_menu_hotkey": "#FF79C6",
                "help_menu_title": "bold #8BE9FD",
                "gradient": ["#FF79C6", "#BD93F9", "#8BE9FD"],
                "directory_icon": "#8BE9FD",
            },

            # Dracula theme - Popular dark theme
            "dracula": {
                "header": "bold #F8F8F2 on #44475A",
                "footer": "#F8F8F2 on #6272A4",
                "border_active": "#FF79C6",
                "border_inactive": "#44475A",
                "background": "#282A36",
                "file": "#F8F8F2",
                "directory": "bold #BD93F9",
                "selected": "#282A36 on #50FA7B",
                "current": "#282A36 on #FFB86C",
                "current_selected": "#282A36 on #FF79C6",
                "error": "bold #FF5555",
                "success": "bold #50FA7B",
                "warning": "bold #F1FA8C",
                "info": "bold #8BE9FD",
                "image": "bold #FF79C6",
                "video": "bold #BD93F9",
                "audio": "bold #FF6B6B",
                "code": "bold #50FA7B",
                "archive": "bold #F1FA8C",
                "document": "bold #8BE9FD",
                "executable": "bold #FF5555",
                "symlink": "bold #6BE5FD",
                "cursor": "#FF79C6",
                "hint": "#6272A4",
                "cancel": "#FF5555",
                "confirm": "#50FA7B",
                "file_fg": "#F8F8F2",
                "file_bg": "#282A36",
                "sidebar_title": "bold #FF79C6",
                "sidebar_divider": "#44475A",
                "help_menu_hotkey": "#FFB86C",
                "help_menu_title": "bold #BD93F9",
                "gradient": ["#FF79C6", "#BD93F9", "#8BE9FD", "#50FA7B"],
                "directory_icon": "#BD93F9",
            },

            # Catppuccin theme - Warm pastel colors
            "catppuccin": {
                "header": "bold #CDD6F4 on #45475A",
                "footer": "#CDD6F4 on #585B70",
                "border_active": "#F5C2E7",
                "border_inactive": "#585B70",
                "background": "#1E1E2E",
                "file": "#CDD6F4",
                "directory": "bold #89B4FA",
                "selected": "#1E1E2E on #A6E3A1",
                "current": "#1E1E2E on #F9E2AF",
                "current_selected": "#1E1E2E on #F5C2E7",
                "error": "bold #F38BA8",
                "success": "bold #A6E3A1",
                "warning": "bold #F9E2AF",
                "info": "bold #89B4FA",
                "image": "bold #F5C2E7",
                "video": "bold #CBA6F7",
                "audio": "bold #EBA0AC",
                "code": "bold #A6E3A1",
                "archive": "bold #F9E2AF",
                "document": "bold #89B4FA",
                "executable": "bold #F38BA8",
                "symlink": "bold #94E2D5",
                "cursor": "#F5C2E7",
                "hint": "#585B70",
                "cancel": "#F38BA8",
                "confirm": "#A6E3A1",
                "file_fg": "#CDD6F4",
                "file_bg": "#1E1E2E",
                "sidebar_title": "bold #F5C2E7",
                "sidebar_divider": "#45475A",
                "help_menu_hotkey": "#F9E2AF",
                "help_menu_title": "bold #CBA6F7",
                "gradient": ["#F5C2E7", "#CBA6F7", "#89B4FA"],
                "directory_icon": "#89B4FA",
            },

            # Gruvbox theme - Retro groove colors
            "gruvbox": {
                "header": "bold #FBF1C7 on #3C3836",
                "footer": "#FBF1C7 on #504945",
                "border_active": "#FABD2F",
                "border_inactive": "#665C54",
                "background": "#282828",
                "file": "#FBF1C7",
                "directory": "bold #83A598",
                "selected": "#282828 on #B8BB26",
                "current": "#282828 on #FABD2F",
                "current_selected": "#282828 on #FB4934",
                "error": "bold #FB4934",
                "success": "bold #B8BB26",
                "warning": "bold #FABD2F",
                "info": "bold #83A598",
                "image": "bold #D3869B",
                "video": "bold #8EC07C",
                "audio": "bold #FE8019",
                "code": "bold #B8BB26",
                "archive": "bold #FABD2F",
                "document": "bold #83A598",
                "executable": "bold #FB4934",
                "symlink": "bold #8EC07C",
                "cursor": "#FABD2F",
                "hint": "#665C54",
                "cancel": "#FB4934",
                "confirm": "#B8BB26",
                "file_fg": "#FBF1C7",
                "file_bg": "#282828",
                "sidebar_title": "bold #D3869B",
                "sidebar_divider": "#3C3836",
                "help_menu_hotkey": "#FABD2F",
                "help_menu_title": "bold #83A598",
                "gradient": ["#FB4934", "#FABD2F", "#B8BB26"],
                "directory_icon": "#83A598",
            },

            # Nord theme - Arctic, north-bluish color palette
            "nord": {
                "header": "bold #ECEFF4 on #434C5E",
                "footer": "#ECEFF4 on #5E81AC",
                "border_active": "#88C0D0",
                "border_inactive": "#4C566A",
                "background": "#2E3440",
                "file": "#ECEFF4",
                "directory": "bold #81A1C1",
                "selected": "#2E3440 on #A3BE8C",
                "current": "#2E3440 on #EBCB8B",
                "current_selected": "#2E3440 on #B48EAD",
                "error": "bold #BF616A",
                "success": "bold #A3BE8C",
                "warning": "bold #EBCB8B",
                "info": "bold #81A1C1",
                "image": "bold #B48EAD",
                "video": "bold #5E81AC",
                "audio": "bold #D08770",
                "code": "bold #A3BE8C",
                "archive": "bold #EBCB8B",
                "document": "bold #81A1C1",
                "executable": "bold #BF616A",
                "symlink": "bold #88C0D0",
                "cursor": "#88C0D0",
                "hint": "#4C566A",
                "cancel": "#BF616A",
                "confirm": "#A3BE8C",
                "file_fg": "#ECEFF4",
                "file_bg": "#2E3440",
                "sidebar_title": "bold #B48EAD",
                "sidebar_divider": "#434C5E",
                "help_menu_hotkey": "#EBCB8B",
                "help_menu_title": "bold #81A1C1",
                "gradient": ["#BF616A", "#D08770", "#EBCB8B"],
                "directory_icon": "#81A1C1",
            },

            # Monokai theme - Sublime Text inspired
            "monokai": {
                "header": "bold #F8F8F2 on #49483E",
                "footer": "#F8F8F2 on #75715E",
                "border_active": "#A6E22E",
                "border_inactive": "#75715E",
                "background": "#272822",
                "file": "#F8F8F2",
                "directory": "bold #66D9EF",
                "selected": "#272822 on #A6E22E",
                "current": "#272822 on #E6DB74",
                "current_selected": "#272822 on #F92672",
                "error": "bold #F92672",
                "success": "bold #A6E22E",
                "warning": "bold #E6DB74",
                "info": "bold #66D9EF",
                "image": "bold #AE81FF",
                "video": "bold #FD971F",
                "audio": "bold #F92672",
                "code": "bold #A6E22E",
                "archive": "bold #E6DB74",
                "document": "bold #66D9EF",
                "executable": "bold #F92672",
                "symlink": "bold #66D9EF",
                "cursor": "#A6E22E",
                "hint": "#75715E",
                "cancel": "#F92672",
                "confirm": "#A6E22E",
                "file_fg": "#F8F8F2",
                "file_bg": "#272822",
                "sidebar_title": "bold #AE81FF",
                "sidebar_divider": "#49483E",
                "help_menu_hotkey": "#E6DB74",
                "help_menu_title": "bold #66D9EF",
                "gradient": ["#F92672", "#FD971F", "#E6DB74"],
                "directory_icon": "#66D9EF",
            },
        }

    def get_style(self, element: str, panel_active: bool = True) -> str:
        """Get style for UI element"""
        # Handle ThemeConfig object or string
        if hasattr(self.current_theme, 'name'):
            theme_name = self.current_theme.name
        else:
            theme_name = str(self.current_theme)

        if theme_name not in self.themes:
            theme_name = "default"

        theme = self.themes[theme_name]

        # Handle border styles based on panel state
        if element == "border":
            return theme.get("border_active" if panel_active else "border_inactive", "#808080")

        return theme.get(element, "white")

    def get_file_style(self, file_type: str, is_selected: bool = False, is_current: bool = False) -> str:
        """Get style for file type with state indicators"""
        theme_name = self.current_theme.name if hasattr(self.current_theme, 'name') else self.current_theme
        if theme_name not in self.themes:
            theme_name = "default"

        theme = self.themes[theme_name]

        # Priority: current + selected > current > selected > normal
        if is_current and is_selected:
            return theme.get("current_selected", "white on blue")
        elif is_current:
            return theme.get("current", "white on blue")
        elif is_selected:
            return theme.get("selected", "white on green")

        # Return file type specific style
        file_type_map = {
            "directory": "directory",
            "image": "image",
            "video": "video",
            "audio": "audio",
            "code": "code",
            "archive": "archive",
            "document": "document",
            "executable": "executable",
            "symlink": "symlink"
        }

        style_key = file_type_map.get(file_type, "file")
        return theme.get(style_key, "white")

    def set_theme(self, theme_name: str):
        """Set current theme"""
        if theme_name in self.themes:
            if hasattr(self.current_theme, 'name'):
                self.current_theme.name = theme_name
            else:
                self.current_theme = theme_name
            self.config.update_theme(theme_name)

    def get_available_themes(self) -> list:
        """Get list of available themes"""
        return list(self.themes.keys())

    def get_file_icon(self, file_type: str, file_name: str = "", is_dir: bool = False, is_symlink: bool = False) -> str:
        """Get beautiful unicode icons for file types"""
        if is_symlink:
            return "🔗"

        if is_dir:
            # Special directory icons
            dir_icons = {
                "home": "🏠", "documents": "📚", "downloads": "📥", "desktop": "🖥️",
                "pictures": "🖼️", "music": "🎵", "videos": "🎬", "public": "🌐",
                ".git": "📦", "node_modules": "📦", "__pycache__": "🗄️",
                ".vscode": "💻", ".config": "⚙️", "bin": "⚙️", "src": "📁",
                "test": "🧪", "tests": "🧪", "docs": "📖", "assets": "🎨"
            }

            name_lower = file_name.lower()
            for key, icon in dir_icons.items():
                if key in name_lower:
                    return icon

            # Default directory icons
            if file_name.startswith('.'):
                return "📁"  # Hidden directory
            return "📂"  # Regular directory

        # File type icons
        file_icons = {
            # Programming languages
            "py": "🐍", "js": "🟨", "ts": "🔷", "jsx": "⚛️", "tsx": "⚛️",
            "java": "☕", "cpp": "⚡", "c": "⚡", "h": "⚡", "hpp": "⚡",
            "rs": "🦀", "go": "🐹", "php": "🐘", "rb": "💎", "swift": "🍎",
            "kt": "🎯", "scala": "🔺", "clj": "🔵", "hs": "λ", "elm": "🌳",
            "dart": "🎯", "r": "📊", "matlab": "📊", "jl": "🔴",

            # Web technologies
            "html": "🌐", "htm": "🌐", "css": "🎨", "scss": "🎨", "sass": "🎨",
            "less": "🎨", "vue": "💚", "svelte": "🧡", "angular": "🔴",

            # Data formats
            "json": "📋", "yaml": "📄", "yml": "📄", "xml": "📄", "csv": "📊",
            "tsv": "📊", "sql": "🗃️", "db": "🗃️", "sqlite": "🗃️",

            # Images
            "jpg": "🖼️", "jpeg": "🖼️", "png": "🖼️", "gif": "🎞️", "svg": "🎨",
            "bmp": "🖼️", "webp": "🖼️", "ico": "🔲", "tiff": "🖼️", "psd": "🎨",
            "ai": "🎨", "sketch": "🎨", "fig": "🎨", "xd": "🎨",

            # Videos
            "mp4": "🎬", "avi": "🎬", "mkv": "🎬", "mov": "🎬", "wmv": "🎬",
            "flv": "🎬", "webm": "🎬", "m4v": "🎬", "3gp": "📱",

            # Audio
            "mp3": "🎵", "wav": "🎵", "flac": "🎵", "aac": "🎵", "ogg": "🎵",
            "m4a": "🎵", "wma": "🎵", "opus": "🎵",

            # Documents
            "pdf": "📕", "doc": "📘", "docx": "📘", "xls": "📗", "xlsx": "📗",
            "ppt": "📙", "pptx": "📙", "odt": "📄", "ods": "📊", "odp": "📊",
            "rtf": "📄", "tex": "📜", "md": "📝", "txt": "📄",

            # Archives
            "zip": "📦", "rar": "📦", "7z": "📦", "tar": "📦", "gz": "📦",
            "bz2": "📦", "xz": "📦", "deb": "📦", "rpm": "📦", "dmg": "💿",
            "iso": "💿", "img": "💿",

            # Executables
            "exe": "⚙️", "msi": "⚙️", "app": "📱", "deb": "📦", "rpm": "📦",
            "appimage": "📱", "flatpak": "📱", "snap": "📱",

            # Shell scripts
            "sh": "🐚", "bash": "🐚", "zsh": "🐚", "fish": "🐚", "csh": "🐚",
            "bat": "⚙️", "cmd": "⚙️", "ps1": "💙",

            # Configuration
            "conf": "⚙️", "config": "⚙️", "ini": "⚙️", "cfg": "⚙️",
            "env": "🔧", "gitignore": "🙈", "gitconfig": "🔧", "editorconfig": "🔧",
            "dockerfile": "🐳", "docker-compose": "🐳", "makefile": "🔨",

            # Fonts
            "ttf": "🔤", "otf": "🔤", "woff": "🔤", "woff2": "🔤", "eot": "🔤",

            # Certificates
            "pem": "🔐", "key": "🔑", "crt": "🔐", "cer": "🔐", "p12": "🔐",

            # Logs
            "log": "📜", "logs": "📜",

            # Temporary files
            "tmp": "🗂️", "temp": "🗂️", "cache": "🗄️", "bak": "💾", "backup": "💾",
        }

        # Get extension
        if '.' in file_name:
            ext = file_name.split('.')[-1].lower()
            if ext in file_icons:
                return file_icons[ext]

        # Check for specific file names
        name_lower = file_name.lower()
        special_files = {
            "readme": "📖", "license": "📜", "changelog": "📋", "makefile": "🔨",
            "dockerfile": "🐳", "vagrantfile": "📦", "procfile": "⚙️",
            "gemfile": "💎", "package.json": "📦", "composer.json": "🎼",
            "requirements.txt": "📋", "setup.py": "🐍", "main.py": "🐍",
            "index.html": "🌐", "index.js": "🟨", "app.js": "🟨"
        }

        for pattern, icon in special_files.items():
            if pattern in name_lower:
                return icon

        # Default based on file type
        if file_type == "executable":
            return "⚙️"
        elif file_type == "code":
            return "💻"
        elif file_type == "image":
            return "🖼️"
        elif file_type == "video":
            return "🎬"
        elif file_type == "audio":
            return "🎵"
        elif file_type == "archive":
            return "📦"
        elif file_type == "document":
            return "📄"

        return "📄"  # Default file icon

    def get_size_color(self, size: int) -> str:
        """Get color for file size based on size"""
        theme_name = self.current_theme.name if hasattr(self.current_theme, 'name') else self.current_theme
        if theme_name not in self.themes:
            theme_name = "default"

        if size < 1024:  # < 1KB
            return "dim white"
        elif size < 1024 * 1024:  # < 1MB
            return "green"
        elif size < 1024 * 1024 * 10:  # < 10MB
            return "yellow"
        elif size < 1024 * 1024 * 100:  # < 100MB
            return "orange"
        else:  # >= 100MB
            return "red"

    def format_file_size(self, size: int) -> str:
        """Format file size with beautiful colors"""
        color = self.get_size_color(size)

        if size < 1024:
            return f"[{color}]{size} B[/{color}]"

        size_float = float(size)
        for unit in ['KB', 'MB', 'GB', 'TB']:
            size_float /= 1024.0
            if size_float < 1024.0:
                return f"[{color}]{size_float:.1f} {unit}[/{color}]"

        return f"[red]{size_float:.1f} PB[/red]"

    def get_permission_style(self, permissions: str) -> str:
        """Get style for file permissions"""
        if permissions.startswith('d'):
            return "bold blue"  # Directory
        elif 'x' in permissions[1:4]:  # Owner executable
            return "bold green"  # Executable
        elif permissions[1] == 'r' and permissions[2] == 'w':
            return "yellow"  # Read-write
        elif permissions[1] == 'r':
            return "white"  # Read-only
        else:
            return "dim red"  # No permissions
