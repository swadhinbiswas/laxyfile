"""
Advanced Icon System for LaxyFile - Inspired by Superfile's comprehensive icon support
Supports both Unicode emojis and Nerd Fonts for better visual experience
"""

from typing import Dict, Optional, Tuple
from pathlib import Path
import os

class IconStyle:
    """Icon style definition"""
    def __init__(self, icon: str, color: str = "white"):
        self.icon = icon
        self.color = color

class IconManager:
    """Advanced icon management system inspired by Superfile"""

    def __init__(self, use_nerd_fonts: bool = True, directory_icon_color: str = "#FFB86C"):
        self.use_nerd_fonts = use_nerd_fonts
        self.directory_icon_color = directory_icon_color
        self._init_icons()

    def _init_icons(self):
        """Initialize icon mappings"""
        # System icons
        if self.use_nerd_fonts:
            self.system_icons = {
                # Navigation
                "cursor": "\uf054",  #
                "directory": "\uf07b",  #
                "home": "\uf015",  #
                "up": "\uf062",  #
                "download": "\uf019",  #
                "documents": "\uf0f6",  #
                "pictures": "\uf03e",  #
                "videos": "\uf03d",  #
                "music": "\uf001",  #
                "search": "\uf002",  #
                "sort_asc": "\uf0de",  #
                "sort_desc": "\uf0dd",  #
                "terminal": "\uf120",  #
                "pinned": "\uf08d",  #

                # File operations
                "copy": "\uf0c5",  #
                "cut": "\uf0c4",  #
                "paste": "\uf0ea",  #
                "delete": "\uf1f8",  #
                "rename": "\uf246",  #
                "new_file": "\uf15b",  #
                "new_folder": "\uf07b",  #
                "compress": "\uf410",  #
                "extract": "\uf411",  #

                # Status
                "success": "\uf00c",  #
                "error": "\uf00d",  #
                "warning": "\uf071",  #
                "info": "\uf05a",  #
                "loading": "\uf110",  #
            }
        else:
            # ASCII fallbacks
            self.system_icons = {
                "cursor": ">",
                "directory": "D",
                "home": "H",
                "up": "^",
                "download": "v",
                "documents": "D",
                "pictures": "P",
                "videos": "V",
                "music": "M",
                "search": "?",
                "sort_asc": "^",
                "sort_desc": "v",
                "terminal": "T",
                "pinned": "*",
                "copy": "C",
                "cut": "X",
                "paste": "P",
                "delete": "D",
                "rename": "R",
                "new_file": "F",
                "new_folder": "D",
                "compress": "Z",
                "extract": "E",
                "success": "+",
                "error": "!",
                "warning": "!",
                "info": "i",
                "loading": ".",
            }

        # File type icons (comprehensive like Superfile)
        if self.use_nerd_fonts:
            self.file_icons = {
                # Programming languages
                "py": IconStyle("\ue606", "#3776AB"),  #
                "js": IconStyle("\ue781", "#F7DF1E"),  #
                "ts": IconStyle("\ue628", "#3178C6"),  #
                "jsx": IconStyle("\ue7ba", "#61DAFB"),  #
                "tsx": IconStyle("\ue7ba", "#61DAFB"),  #
                "html": IconStyle("\uf13b", "#E34F26"),  #
                "css": IconStyle("\uf13c", "#1572B6"),  #
                "scss": IconStyle("\ue603", "#CF649A"),  #
                "sass": IconStyle("\ue603", "#CF649A"),  #
                "vue": IconStyle("\ue6a0", "#4FC08D"),  #
                "java": IconStyle("\ue738", "#ED8B00"),  #
                "c": IconStyle("\ue649", "#A8B9CC"),  #
                "cpp": IconStyle("\ue646", "#00599C"),  #
                "h": IconStyle("\uf0fd", "#A8B9CC"),  #
                "rs": IconStyle("\ue7a8", "#CE422B"),  #
                "go": IconStyle("\ue627", "#00ADD8"),  #
                "php": IconStyle("\ue608", "#777BB4"),  #
                "rb": IconStyle("\ue21e", "#CC342D"),  #
                "swift": IconStyle("\ue755", "#FA7343"),  #
                "kt": IconStyle("\ue634", "#7F52FF"),  #
                "scala": IconStyle("\ue737", "#DC322F"),  #
                "dart": IconStyle("\ue64c", "#0175C2"),  #
                "r": IconStyle("\ue68a", "#276DC3"),  #

                # Web and data
                "json": IconStyle("\ue60b", "#FD7F28"),  #
                "xml": IconStyle("\ue796", "#E37933"),  #
                "yaml": IconStyle("\ue601", "#CB171E"),  #
                "yml": IconStyle("\ue601", "#CB171E"),  #
                "toml": IconStyle("\uf669", "#9C4221"),  #
                "sql": IconStyle("\uf1c0", "#336791"),  #
                "md": IconStyle("\uf48a", "#083FA1"),  #
                "csv": IconStyle("\uf1c3", "#0F9D58"),  #

                # Images
                "png": IconStyle("\uf1c5", "#0F9D58"),  #
                "jpg": IconStyle("\uf1c5", "#0F9D58"),  #
                "jpeg": IconStyle("\uf1c5", "#0F9D58"),  #
                "gif": IconStyle("\uf1c5", "#FF6D01"),  #
                "svg": IconStyle("\uf1c5", "#FFB13B"),  #
                "bmp": IconStyle("\uf1c5", "#4285F4"),  #
                "webp": IconStyle("\uf1c5", "#4285F4"),  #
                "ico": IconStyle("\uf1c5", "#4285F4"),  #
                "tiff": IconStyle("\uf1c5", "#4285F4"),  #
                "psd": IconStyle("\ue7b8", "#31A8FF"),  #

                # Videos
                "mp4": IconStyle("\uf03d", "#FD79A8"),  #
                "avi": IconStyle("\uf03d", "#FD79A8"),  #
                "mkv": IconStyle("\uf03d", "#FD79A8"),  #
                "mov": IconStyle("\uf03d", "#FD79A8"),  #
                "wmv": IconStyle("\uf03d", "#FD79A8"),  #
                "flv": IconStyle("\uf03d", "#FD79A8"),  #
                "webm": IconStyle("\uf03d", "#FD79A8"),  #

                # Audio
                "mp3": IconStyle("\uf001", "#FF6B6B"),  #
                "wav": IconStyle("\uf001", "#FF6B6B"),  #
                "flac": IconStyle("\uf001", "#FF6B6B"),  #
                "aac": IconStyle("\uf001", "#FF6B6B"),  #
                "ogg": IconStyle("\uf001", "#FF6B6B"),  #
                "m4a": IconStyle("\uf001", "#FF6B6B"),  #

                # Archives
                "zip": IconStyle("\uf410", "#FDCB6E"),  #
                "rar": IconStyle("\uf410", "#FDCB6E"),  #
                "7z": IconStyle("\uf410", "#FDCB6E"),  #
                "tar": IconStyle("\uf410", "#FDCB6E"),  #
                "gz": IconStyle("\uf410", "#FDCB6E"),  #
                "bz2": IconStyle("\uf410", "#FDCB6E"),  #
                "xz": IconStyle("\uf410", "#FDCB6E"),  #

                # Documents
                "pdf": IconStyle("\uf1c1", "#FF6B6B"),  #
                "doc": IconStyle("\uf1c2", "#185ABD"),  #
                "docx": IconStyle("\uf1c2", "#185ABD"),  #
                "xls": IconStyle("\uf1c3", "#107C41"),  #
                "xlsx": IconStyle("\uf1c3", "#107C41"),  #
                "ppt": IconStyle("\uf1c4", "#C43E1C"),  #
                "pptx": IconStyle("\uf1c4", "#C43E1C"),  #
                "txt": IconStyle("\uf15c", "#DCDCAA"),  #

                # Executables
                "exe": IconStyle("\uf17a", "#FF6B6B"),  #
                "msi": IconStyle("\uf17a", "#FF6B6B"),  #
                "deb": IconStyle("\ue77d", "#D70A53"),  #
                "rpm": IconStyle("\uf17c", "#FCA326"),  #
                "app": IconStyle("\uf179", "#A2AAAD"),  #

                # Shell scripts
                "sh": IconStyle("\uf489", "#89E051"),  #
                "bash": IconStyle("\uf489", "#89E051"),  #
                "zsh": IconStyle("\uf489", "#89E051"),  #
                "fish": IconStyle("\uf489", "#89E051"),  #
                "bat": IconStyle("\ue629", "#C1F12E"),  #
                "cmd": IconStyle("\ue629", "#C1F12E"),  #
                "ps1": IconStyle("\uf489", "#012456"),  #

                # Configuration
                "conf": IconStyle("\ue615", "#FFFFCC"),  #
                "config": IconStyle("\ue615", "#FFFFCC"),  #
                "ini": IconStyle("\uf17a", "#FFFFCC"),  #
                "cfg": IconStyle("\ue615", "#FFFFCC"),  #
                "env": IconStyle("\uf462", "#ECD53F"),  #
                "gitignore": IconStyle("\ue702", "#F1502F"),  #
                "dockerfile": IconStyle("\uf308", "#0db7ed"),  #
                "makefile": IconStyle("\uf489", "#427819"),  #

                # Default
                "file": IconStyle("\uf15b", "#FFFFFF"),  #
            }
        else:
            # Unicode emoji fallbacks (more universal support)
            self.file_icons = {
                "py": IconStyle("🐍", "#3776AB"),
                "js": IconStyle("📜", "#F7DF1E"),
                "ts": IconStyle("📘", "#3178C6"),
                "jsx": IconStyle("⚛️", "#61DAFB"),
                "tsx": IconStyle("⚛️", "#61DAFB"),
                "html": IconStyle("🌐", "#E34F26"),
                "css": IconStyle("🎨", "#1572B6"),
                "scss": IconStyle("🎨", "#CF649A"),
                "sass": IconStyle("🎨", "#CF649A"),
                "vue": IconStyle("💚", "#4FC08D"),
                "java": IconStyle("☕", "#ED8B00"),
                "c": IconStyle("⚡", "#A8B9CC"),
                "cpp": IconStyle("⚡", "#00599C"),
                "h": IconStyle("📋", "#A8B9CC"),
                "rs": IconStyle("🦀", "#CE422B"),
                "go": IconStyle("🐹", "#00ADD8"),
                "php": IconStyle("🐘", "#777BB4"),
                "rb": IconStyle("💎", "#CC342D"),
                "swift": IconStyle("🍎", "#FA7343"),
                "kt": IconStyle("🎯", "#7F52FF"),
                "scala": IconStyle("🔺", "#DC322F"),
                "dart": IconStyle("🎯", "#0175C2"),
                "r": IconStyle("📊", "#276DC3"),
                "json": IconStyle("📋", "#FD7F28"),
                "xml": IconStyle("📄", "#E37933"),
                "yaml": IconStyle("📄", "#CB171E"),
                "yml": IconStyle("📄", "#CB171E"),
                "toml": IconStyle("📄", "#9C4221"),
                "sql": IconStyle("🗃️", "#336791"),
                "md": IconStyle("📝", "#083FA1"),
                "csv": IconStyle("📊", "#0F9D58"),
                "png": IconStyle("🖼️", "#0F9D58"),
                "jpg": IconStyle("🖼️", "#0F9D58"),
                "jpeg": IconStyle("🖼️", "#0F9D58"),
                "gif": IconStyle("🎞️", "#FF6D01"),
                "svg": IconStyle("🎨", "#FFB13B"),
                "bmp": IconStyle("🖼️", "#4285F4"),
                "webp": IconStyle("🖼️", "#4285F4"),
                "ico": IconStyle("🔲", "#4285F4"),
                "tiff": IconStyle("🖼️", "#4285F4"),
                "psd": IconStyle("🎨", "#31A8FF"),
                "mp4": IconStyle("🎬", "#FD79A8"),
                "avi": IconStyle("🎬", "#FD79A8"),
                "mkv": IconStyle("🎬", "#FD79A8"),
                "mov": IconStyle("🎬", "#FD79A8"),
                "wmv": IconStyle("🎬", "#FD79A8"),
                "flv": IconStyle("🎬", "#FD79A8"),
                "webm": IconStyle("🎬", "#FD79A8"),
                "mp3": IconStyle("🎵", "#FF6B6B"),
                "wav": IconStyle("🎵", "#FF6B6B"),
                "flac": IconStyle("🎵", "#FF6B6B"),
                "aac": IconStyle("🎵", "#FF6B6B"),
                "ogg": IconStyle("🎵", "#FF6B6B"),
                "m4a": IconStyle("🎵", "#FF6B6B"),
                "zip": IconStyle("📦", "#FDCB6E"),
                "rar": IconStyle("📦", "#FDCB6E"),
                "7z": IconStyle("📦", "#FDCB6E"),
                "tar": IconStyle("📦", "#FDCB6E"),
                "gz": IconStyle("📦", "#FDCB6E"),
                "bz2": IconStyle("📦", "#FDCB6E"),
                "xz": IconStyle("📦", "#FDCB6E"),
                "pdf": IconStyle("📕", "#FF6B6B"),
                "doc": IconStyle("📘", "#185ABD"),
                "docx": IconStyle("📘", "#185ABD"),
                "xls": IconStyle("📗", "#107C41"),
                "xlsx": IconStyle("📗", "#107C41"),
                "ppt": IconStyle("📙", "#C43E1C"),
                "pptx": IconStyle("📙", "#C43E1C"),
                "txt": IconStyle("📄", "#DCDCAA"),
                "exe": IconStyle("⚙️", "#FF6B6B"),
                "msi": IconStyle("⚙️", "#FF6B6B"),
                "deb": IconStyle("📦", "#D70A53"),
                "rpm": IconStyle("📦", "#FCA326"),
                "app": IconStyle("📱", "#A2AAAD"),
                "sh": IconStyle("🐚", "#89E051"),
                "bash": IconStyle("🐚", "#89E051"),
                "zsh": IconStyle("🐚", "#89E051"),
                "fish": IconStyle("🐚", "#89E051"),
                "bat": IconStyle("⚙️", "#C1F12E"),
                "cmd": IconStyle("⚙️", "#C1F12E"),
                "ps1": IconStyle("💙", "#012456"),
                "conf": IconStyle("⚙️", "#FFFFCC"),
                "config": IconStyle("⚙️", "#FFFFCC"),
                "ini": IconStyle("⚙️", "#FFFFCC"),
                "cfg": IconStyle("⚙️", "#FFFFCC"),
                "env": IconStyle("🔧", "#ECD53F"),
                "gitignore": IconStyle("🙈", "#F1502F"),
                "dockerfile": IconStyle("🐳", "#0db7ed"),
                "makefile": IconStyle("🔨", "#427819"),
                "file": IconStyle("📄", "#FFFFFF"),
            }

        # Folder icons (like Superfile's special folder recognition)
        if self.use_nerd_fonts:
            self.folder_icons = {
                ".git": IconStyle("\ue5fb", "#F1502F"),  #
                ".github": IconStyle("\ue5fd", "#000000"),  #
                ".vscode": IconStyle("\ue70c", "#007ACC"),  #
                ".vim": IconStyle("\ue62b", "#019833"),  #
                "node_modules": IconStyle("\ue5fa", "#CB3837"),  #
                "__pycache__": IconStyle("\ue606", "#FFD43B"),  #
                ".npm": IconStyle("\ue5fa", "#CB3837"),  #
                ".docker": IconStyle("\ue7b0", "#0db7ed"),  #
                "config": IconStyle("\ue5fc", "#FFB86C"),  #
                "src": IconStyle("\ue5fc", "#FFB86C"),  #
                "test": IconStyle("\ue5fc", "#FF6B6B"),  #
                "tests": IconStyle("\ue5fc", "#FF6B6B"),  #
                "docs": IconStyle("\uf02d", "#74C0FC"),  #
                "assets": IconStyle("\uf07c", "#FFB86C"),  #
                "images": IconStyle("\uf07c", "#FF79C6"),  #
                "pictures": IconStyle("\uf07c", "#FF79C6"),  #
                "downloads": IconStyle("\uf07c", "#50FA7B"),  #
                "documents": IconStyle("\uf07c", "#8BE9FD"),  #
                "desktop": IconStyle("\uf07c", "#F1FA8C"),  #
                "music": IconStyle("\uf07c", "#FF6B6B"),  #
                "videos": IconStyle("\uf07c", "#BD93F9"),  #
                "bin": IconStyle("\uf413", "#50FA7B"),  #
                "lib": IconStyle("\uf413", "#FFB86C"),  #
                "tmp": IconStyle("\uf413", "#6272A4"),  #
                "var": IconStyle("\uf413", "#8BE9FD"),  #
                "etc": IconStyle("\uf413", "#F1FA8C"),  #
                "home": IconStyle("\uf015", "#50FA7B"),  #
                "folder": IconStyle("\uf07b", self.directory_icon_color),  #
            }
        else:
            self.folder_icons = {
                ".git": IconStyle("📦", "#F1502F"),
                ".github": IconStyle("📦", "#000000"),
                ".vscode": IconStyle("💻", "#007ACC"),
                ".vim": IconStyle("📝", "#019833"),
                "node_modules": IconStyle("📦", "#CB3837"),
                "__pycache__": IconStyle("🗄️", "#FFD43B"),
                ".npm": IconStyle("📦", "#CB3837"),
                ".docker": IconStyle("🐳", "#0db7ed"),
                "config": IconStyle("⚙️", "#FFB86C"),
                "src": IconStyle("📁", "#FFB86C"),
                "test": IconStyle("🧪", "#FF6B6B"),
                "tests": IconStyle("🧪", "#FF6B6B"),
                "docs": IconStyle("📖", "#74C0FC"),
                "assets": IconStyle("🎨", "#FFB86C"),
                "images": IconStyle("🖼️", "#FF79C6"),
                "pictures": IconStyle("🖼️", "#FF79C6"),
                "downloads": IconStyle("📥", "#50FA7B"),
                "documents": IconStyle("📚", "#8BE9FD"),
                "desktop": IconStyle("🖥️", "#F1FA8C"),
                "music": IconStyle("🎵", "#FF6B6B"),
                "videos": IconStyle("🎬", "#BD93F9"),
                "bin": IconStyle("⚙️", "#50FA7B"),
                "lib": IconStyle("📚", "#FFB86C"),
                "tmp": IconStyle("🗂️", "#6272A4"),
                "var": IconStyle("📁", "#8BE9FD"),
                "etc": IconStyle("⚙️", "#F1FA8C"),
                "home": IconStyle("🏠", "#50FA7B"),
                "folder": IconStyle("📂", self.directory_icon_color),
            }

        # File name aliases (like Superfile's special file recognition)
        self.file_aliases = {
            # Python files
            "requirements.txt": "py",
            "setup.py": "py",
            "main.py": "py",
            "app.py": "py",
            "__init__.py": "py",

            # JavaScript/Node files
            "package.json": "json",
            "package-lock.json": "json",
            "yarn.lock": "yml",
            "webpack.config.js": "js",
            "gulpfile.js": "js",
            "gruntfile.js": "js",
            "rollup.config.js": "js",
            "vite.config.js": "js",
            "next.config.js": "js",

            # Docker
            "dockerfile": "dockerfile",
            "docker-compose.yml": "yml",
            "docker-compose.yaml": "yml",

            # Git
            ".gitignore": "gitignore",
            ".gitconfig": "config",
            ".gitmodules": "config",

            # README files
            "readme": "md",
            "readme.md": "md",
            "readme.txt": "md",
            "changelog": "md",
            "license": "md",
            "contributing": "md",

            # Makefiles
            "makefile": "makefile",
            "cmake": "makefile",
            "cmakelists.txt": "makefile",

            # Configuration files
            ".editorconfig": "config",
            ".eslintrc": "json",
            ".prettierrc": "json",
            ".babelrc": "json",
            "tsconfig.json": "json",
            "tslint.json": "json",
            "composer.json": "json",
            "gemfile": "rb",
            "rakefile": "rb",
            "cargo.toml": "toml",
            "go.mod": "go",
            "go.sum": "go",
            "pyproject.toml": "toml",
        }

    def get_system_icon(self, icon_name: str) -> str:
        """Get system/UI icon"""
        return self.system_icons.get(icon_name, "?")

    def get_file_icon(self, file_path: Path, is_dir: bool = False, is_symlink: bool = False) -> IconStyle:
        """Get icon for file/directory with comprehensive type detection"""
        if is_symlink:
            if self.use_nerd_fonts:
                return IconStyle("\uf0c1", "#00CED1")  #
            else:
                return IconStyle("🔗", "#00CED1")

        file_name = file_path.name.lower()

        if is_dir:
            # Check for special directories
            for folder_name, icon in self.folder_icons.items():
                if folder_name in file_name:
                    return icon

            # Check for hidden directories
            if file_name.startswith('.'):
                if self.use_nerd_fonts:
                    return IconStyle("\uf023", "#75715E")  #
                else:
                    return IconStyle("📁", "#75715E")

            # Default folder icon
            return self.folder_icons.get("folder", IconStyle("📂", self.directory_icon_color))

        # Check for specific file names first (higher priority)
        if file_name in self.file_aliases:
            alias = self.file_aliases[file_name]
            if alias in self.file_icons:
                return self.file_icons[alias]

        # Check by extension
        if '.' in file_name:
            ext = file_name.split('.')[-1].lower()
            if ext in self.file_icons:
                return self.file_icons[ext]

            # Check aliases for extensions
            if ext in self.file_aliases:
                alias = self.file_aliases[ext]
                if alias in self.file_icons:
                    return self.file_icons[alias]

        # Check for executable files
        if os.access(file_path, os.X_OK) and not is_dir:
            if self.use_nerd_fonts:
                return IconStyle("\uf013", "#50FA7B")  #
            else:
                return IconStyle("⚙️", "#50FA7B")

        # Default file icon
        return self.file_icons.get("file", IconStyle("📄", "#FFFFFF"))

    def get_file_type_category(self, file_path: Path) -> str:
        """Get file type category for theming"""
        if file_path.is_dir():
            return "directory"

        if file_path.is_symlink():
            return "symlink"

        file_name = file_path.name.lower()

        # Programming files
        prog_extensions = {
            'py', 'js', 'ts', 'jsx', 'tsx', 'java', 'c', 'cpp', 'h', 'hpp',
            'rs', 'go', 'php', 'rb', 'swift', 'kt', 'scala', 'dart', 'r',
            'html', 'css', 'scss', 'sass', 'vue', 'sql', 'sh', 'bash', 'zsh'
        }

        # Image files
        image_extensions = {
            'png', 'jpg', 'jpeg', 'gif', 'svg', 'bmp', 'webp', 'ico', 'tiff', 'psd'
        }

        # Video files
        video_extensions = {
            'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', 'webm', 'm4v', '3gp'
        }

        # Audio files
        audio_extensions = {
            'mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a', 'wma', 'opus'
        }

        # Archive files
        archive_extensions = {
            'zip', 'rar', '7z', 'tar', 'gz', 'bz2', 'xz', 'deb', 'rpm', 'dmg', 'iso'
        }

        # Document files
        document_extensions = {
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 'md',
            'odt', 'ods', 'odp', 'rtf', 'tex'
        }

        # Executable files
        executable_extensions = {
            'exe', 'msi', 'app', 'deb', 'rpm', 'appimage', 'flatpak', 'snap'
        }

        if '.' in file_name:
            ext = file_name.split('.')[-1].lower()

            if ext in prog_extensions:
                return "code"
            elif ext in image_extensions:
                return "image"
            elif ext in video_extensions:
                return "video"
            elif ext in audio_extensions:
                return "audio"
            elif ext in archive_extensions:
                return "archive"
            elif ext in document_extensions:
                return "document"
            elif ext in executable_extensions:
                return "executable"

        # Check if file is executable
        try:
            if os.access(file_path, os.X_OK) and not file_path.is_dir():
                return "executable"
        except (OSError, PermissionError):
            pass

        return "file"

    def set_nerd_fonts(self, enable: bool):
        """Toggle nerd fonts support"""
        if enable != self.use_nerd_fonts:
            self.use_nerd_fonts = enable
            self._init_icons()

    def set_directory_color(self, color: str):
        """Set directory icon color"""
        self.directory_icon_color = color
        if "folder" in self.folder_icons:
            self.folder_icons["folder"].color = color
