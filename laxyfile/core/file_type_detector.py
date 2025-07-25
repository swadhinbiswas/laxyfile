"""
Advanced File Type Detection and Icon System

This module provides comprehensive file type detection using multiple methods
including extension analysis, MIME type detection, and content analysis.
"""

import os
import mimetypes
import magic
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from .types import FileType
from ..utils.logger import Logger


class IconStyle(Enum):
    """Icon style enumeration"""
    UNICODE = "unicode"
    NERD_FONT = "nerd_font"
    ASCII = "ascii"


@dataclass
class FileTypeInfo:
    """Comprehensive file type information"""
    file_type: FileType
    category: str
    subcategory: str
    mime_type: Optional[str]
    description: str
    icon_unicode: str
    icon_nerd_font: str
    icon_ascii: str
    is_executable: bool = False
    is_binary: bool = False
    is_text: bool = False


class AdvancedFileTypeDetector:
    """Advanced file type detection with comprehensive icon support"""

    def __init__(self, use_magic: bool = True):
        self.logger = Logger()
        self.use_magic = use_magic

        # Initialize magic if available
        self.magic_mime = None
        self.magic_desc = None

        if use_magic:
            try:
                self.magic_mime = magic.Magic(mime=True)
                self.magic_desc = magic.Magic()
            except Exception as e:
                self.logger.warning(f"Magic library not available: {e}")
                self.use_magic = False

        # Initialize file type database
        self._init_file_type_database()

        # Initialize icon mappings
        self._init_icon_mappings()

    def _init_file_type_database(self):
        """Initialize comprehensive file type database"""
        self.file_types = {
            # Programming Languages
            '.py': FileTypeInfo(FileType.CODE, 'code', 'python', 'text/x-python', 'Python Script', '🐍', '', 'PY', is_text=True),
            '.js': FileTypeInfo(FileType.CODE, 'code', 'javascript', 'application/javascript', 'JavaScript', '📜', '', 'JS', is_text=True),
            '.ts': FileTypeInfo(FileType.CODE, 'code', 'typescript', 'application/typescript', 'TypeScript', '📘', '', 'TS', is_text=True),
            '.html': FileTypeInfo(FileType.CODE, 'code', 'html', 'text/html', 'HTML Document', '🌐', '', 'HTM', is_text=True),
            '.css': FileTypeInfo(FileType.CODE, 'code', 'css', 'text/css', 'CSS Stylesheet', '🎨', '', 'CSS', is_text=True),
            '.java': FileTypeInfo(FileType.CODE, 'code', 'java', 'text/x-java-source', 'Java Source', '☕', '', 'JAV', is_text=True),
            '.cpp': FileTypeInfo(FileType.CODE, 'code', 'cpp', 'text/x-c++src', 'C++ Source', '⚙️', '', 'CPP', is_text=True),
            '.c': FileTypeInfo(FileType.CODE, 'code', 'c', 'text/x-csrc', 'C Source', '⚙️', '', 'C', is_text=True),
            '.h': FileTypeInfo(FileType.CODE, 'code', 'header', 'text/x-chdr', 'C Header', '📋', '', 'H', is_text=True),
            '.php': FileTypeInfo(FileType.CODE, 'code', 'php', 'application/x-httpd-php', 'PHP Script', '🐘', '', 'PHP', is_text=True),
            '.rb': FileTypeInfo(FileType.CODE, 'code', 'ruby', 'application/x-ruby', 'Ruby Script', '💎', '', 'RB', is_text=True),
            '.go': FileTypeInfo(FileType.CODE, 'code', 'go', 'text/x-go', 'Go Source', '🐹', '', 'GO', is_text=True),
            '.rs': FileTypeInfo(FileType.CODE, 'code', 'rust', 'text/rust', 'Rust Source', '🦀', '', 'RS', is_text=True),
            '.swift': FileTypeInfo(FileType.CODE, 'code', 'swift', 'text/x-swift', 'Swift Source', '🐦', '', 'SW', is_text=True),
            '.kt': FileTypeInfo(FileType.CODE, 'code', 'kotlin', 'text/x-kotlin', 'Kotlin Source', '🎯', '', 'KT', is_text=True),
            '.scala': FileTypeInfo(FileType.CODE, 'code', 'scala', 'text/x-scala', 'Scala Source', '⚖️', '', 'SC', is_text=True),

            # Web Technologies
            '.jsx': FileTypeInfo(FileType.CODE, 'code', 'react', 'text/jsx', 'React JSX', '⚛️', '', 'JSX', is_text=True),
            '.tsx': FileTypeInfo(FileType.CODE, 'code', 'react', 'text/tsx', 'React TSX', '⚛️', '', 'TSX', is_text=True),
            '.vue': FileTypeInfo(FileType.CODE, 'code', 'vue', 'text/x-vue', 'Vue Component', '💚', '', 'VUE', is_text=True),
            '.scss': FileTypeInfo(FileType.CODE, 'code', 'sass', 'text/x-scss', 'SASS Stylesheet', '🎨', '', 'SCSS', is_text=True),
            '.sass': FileTypeInfo(FileType.CODE, 'code', 'sass', 'text/x-sass', 'SASS Stylesheet', '🎨', '', 'SASS', is_text=True),
            '.less': FileTypeInfo(FileType.CODE, 'code', 'less', 'text/x-less', 'LESS Stylesheet', '🎨', '', 'LESS', is_text=True),

            # Configuration Files
            '.json': FileTypeInfo(FileType.CODE, 'config', 'json', 'application/json', 'JSON Data', '📋', '', 'JSON', is_text=True),
            '.xml': FileTypeInfo(FileType.CODE, 'config', 'xml', 'application/xml', 'XML Document', '📄', '', 'XML', is_text=True),
            '.yaml': FileTypeInfo(FileType.CODE, 'config', 'yaml', 'application/x-yaml', 'YAML Config', '📝', '', 'YAML', is_text=True),
            '.yml': FileTypeInfo(FileType.CODE, 'config', 'yaml', 'application/x-yaml', 'YAML Config', '📝', '', 'YML', is_text=True),
            '.toml': FileTypeInfo(FileType.CODE, 'config', 'toml', 'application/toml', 'TOML Config', '📝', '', 'TOML', is_text=True),
            '.ini': FileTypeInfo(FileType.CODE, 'config', 'ini', 'text/plain', 'INI Config', '⚙️', '', 'INI', is_text=True),
            '.conf': FileTypeInfo(FileType.CODE, 'config', 'config', 'text/plain', 'Configuration', '⚙️', '', 'CONF', is_text=True),
            '.cfg': FileTypeInfo(FileType.CODE, 'config', 'config', 'text/plain', 'Configuration', '⚙️', '', 'CFG', is_text=True),

            # Documents
            '.md': FileTypeInfo(FileType.DOCUMENT, 'document', 'markdown', 'text/markdown', 'Markdown Document', '📖', '', 'MD', is_text=True),
            '.txt': FileTypeInfo(FileType.DOCUMENT, 'document', 'text', 'text/plain', 'Text Document', '📄', '', 'TXT', is_text=True),
            '.pdf': FileTypeInfo(FileType.DOCUMENT, 'document', 'pdf', 'application/pdf', 'PDF Document', '📕', '', 'PDF', is_binary=True),
            '.doc': FileTypeInfo(FileType.DOCUMENT, 'document', 'word', 'application/msword', 'Word Document', '📘', '', 'DOC', is_binary=True),
            '.docx': FileTypeInfo(FileType.DOCUMENT, 'document', 'word', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word Document', '📘', '', 'DOCX', is_binary=True),
            '.odt': FileTypeInfo(FileType.DOCUMENT, 'document', 'writer', 'application/vnd.oasis.opendocument.text', 'OpenDocument Text', '📝', '', 'ODT', is_binary=True),
            '.rtf': FileTypeInfo(FileType.DOCUMENT, 'document', 'rtf', 'application/rtf', 'Rich Text Format', '📝', '', 'RTF', is_text=True),

            # Spreadsheets
            '.xls': FileTypeInfo(FileType.DOCUMENT, 'document', 'excel', 'application/vnd.ms-excel', 'Excel Spreadsheet', '📊', '', 'XLS', is_binary=True),
            '.xlsx': FileTypeInfo(FileType.DOCUMENT, 'document', 'excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Excel Spreadsheet', '📊', '', 'XLSX', is_binary=True),
            '.ods': FileTypeInfo(FileType.DOCUMENT, 'document', 'calc', 'application/vnd.oasis.opendocument.spreadsheet', 'OpenDocument Spreadsheet', '📊', '', 'ODS', is_binary=True),
            '.csv': FileTypeInfo(FileType.DOCUMENT, 'document', 'csv', 'text/csv', 'CSV Data', '📊', '', 'CSV', is_text=True),

            # Presentations
            '.ppt': FileTypeInfo(FileType.DOCUMENT, 'document', 'powerpoint', 'application/vnd.ms-powerpoint', 'PowerPoint Presentation', '📽️', '', 'PPT', is_binary=True),
            '.pptx': FileTypeInfo(FileType.DOCUMENT, 'document', 'powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation', 'PowerPoint Presentation', '📽️', '', 'PPTX', is_binary=True),
            '.odp': FileTypeInfo(FileType.DOCUMENT, 'document', 'impress', 'application/vnd.oasis.opendocument.presentation', 'OpenDocument Presentation', '📽️', '', 'ODP', is_binary=True),

            # Images
            '.jpg': FileTypeInfo(FileType.IMAGE, 'media', 'image', 'image/jpeg', 'JPEG Image', '🖼️', '', 'JPG', is_binary=True),
            '.jpeg': FileTypeInfo(FileType.IMAGE, 'media', 'image', 'image/jpeg', 'JPEG Image', '🖼️', '', 'JPEG', is_binary=True),
            '.png': FileTypeInfo(FileType.IMAGE, 'media', 'image', 'image/png', 'PNG Image', '🖼️', '', 'PNG', is_binary=True),
            '.gif': FileTypeInfo(FileType.IMAGE, 'media', 'image', 'image/gif', 'GIF Image', '🖼️', '', 'GIF', is_binary=True),
            '.bmp': FileTypeInfo(FileType.IMAGE, 'media', 'image', 'image/bmp', 'Bitmap Image', '🖼️', '', 'BMP', is_binary=True),
            '.webp': FileTypeInfo(FileType.IMAGE, 'media', 'image', 'image/webp', 'WebP Image', '🖼️', '', 'WEBP', is_binary=True),
            '.svg': FileTypeInfo(FileType.IMAGE, 'media', 'vector', 'image/svg+xml', 'SVG Vector', '🎨', '', 'SVG', is_text=True),
            '.tiff': FileTypeInfo(FileType.IMAGE, 'media', 'image', 'image/tiff', 'TIFF Image', '🖼️', '', 'TIFF', is_binary=True),
            '.ico': FileTypeInfo(FileType.IMAGE, 'media', 'icon', 'image/x-icon', 'Icon File', '🖼️', '', 'ICO', is_binary=True),

            # Videos
            '.mp4': FileTypeInfo(FileType.VIDEO, 'media', 'video', 'video/mp4', 'MP4 Video', '🎬', '', 'MP4', is_binary=True),
            '.avi': FileTypeInfo(FileType.VIDEO, 'media', 'video', 'video/x-msvideo', 'AVI Video', '🎬', '', 'AVI', is_binary=True),
            '.mkv': FileTypeInfo(FileType.VIDEO, 'media', 'video', 'video/x-matroska', 'Matroska Video', '🎬', '', 'MKV', is_binary=True),
            '.mov': FileTypeInfo(FileType.VIDEO, 'media', 'video', 'video/quicktime', 'QuickTime Video', '🎬', '', 'MOV', is_binary=True),
            '.wmv': FileTypeInfo(FileType.VIDEO, 'media', 'video', 'video/x-ms-wmv', 'Windows Media Video', '🎬', '', 'WMV', is_binary=True),
            '.flv': FileTypeInfo(FileType.VIDEO, 'media', 'video', 'video/x-flv', 'Flash Video', '🎬', '', 'FLV', is_binary=True),
            '.webm': FileTypeInfo(FileType.VIDEO, 'media', 'video', 'video/webm', 'WebM Video', '🎬', '', 'WEBM', is_binary=True),
            '.m4v': FileTypeInfo(FileType.VIDEO, 'media', 'video', 'video/x-m4v', 'M4V Video', '🎬', '', 'M4V', is_binary=True),

            # Audio
            '.mp3': FileTypeInfo(FileType.AUDIO, 'media', 'audio', 'audio/mpeg', 'MP3 Audio', '🎵', '', 'MP3', is_binary=True),
            '.wav': FileTypeInfo(FileType.AUDIO, 'media', 'audio', 'audio/wav', 'WAV Audio', '🎵', '', 'WAV', is_binary=True),
            '.flac': FileTypeInfo(FileType.AUDIO, 'media', 'audio', 'audio/flac', 'FLAC Audio', '🎵', '', 'FLAC', is_binary=True),
            '.aac': FileTypeInfo(FileType.AUDIO, 'media', 'audio', 'audio/aac', 'AAC Audio', '🎵', '', 'AAC', is_binary=True),
            '.ogg': FileTypeInfo(FileType.AUDIO, 'media', 'audio', 'audio/ogg', 'OGG Audio', '🎵', '', 'OGG', is_binary=True),
            '.wma': FileTypeInfo(FileType.AUDIO, 'media', 'audio', 'audio/x-ms-wma', 'Windows Media Audio', '🎵', '', 'WMA', is_binary=True),
            '.m4a': FileTypeInfo(FileType.AUDIO, 'media', 'audio', 'audio/mp4', 'M4A Audio', '🎵', '', 'M4A', is_binary=True),

            # Archives
            '.zip': FileTypeInfo(FileType.ARCHIVE, 'archive', 'zip', 'application/zip', 'ZIP Archive', '📦', '', 'ZIP', is_binary=True),
            '.tar': FileTypeInfo(FileType.ARCHIVE, 'archive', 'tar', 'application/x-tar', 'TAR Archive', '📦', '', 'TAR', is_binary=True),
            '.gz': FileTypeInfo(FileType.ARCHIVE, 'archive', 'gzip', 'application/gzip', 'GZIP Archive', '📦', '', 'GZ', is_binary=True),
            '.bz2': FileTypeInfo(FileType.ARCHIVE, 'archive', 'bzip2', 'application/x-bzip2', 'BZIP2 Archive', '📦', '', 'BZ2', is_binary=True),
            '.xz': FileTypeInfo(FileType.ARCHIVE, 'archive', 'xz', 'application/x-xz', 'XZ Archive', '📦', '', 'XZ', is_binary=True),
            '.7z': FileTypeInfo(FileType.ARCHIVE, 'archive', '7zip', 'application/x-7z-compressed', '7-Zip Archive', '📦', '', '7Z', is_binary=True),
            '.rar': FileTypeInfo(FileType.ARCHIVE, 'archive', 'rar', 'application/vnd.rar', 'RAR Archive', '📦', '', 'RAR', is_binary=True),

            # Executables
            '.exe': FileTypeInfo(FileType.EXECUTABLE, 'executable', 'windows', 'application/x-msdownload', 'Windows Executable', '⚙️', '', 'EXE', is_binary=True, is_executable=True),
            '.msi': FileTypeInfo(FileType.EXECUTABLE, 'executable', 'installer', 'application/x-msi', 'Windows Installer', '⚙️', '', 'MSI', is_binary=True, is_executable=True),
            '.deb': FileTypeInfo(FileType.EXECUTABLE, 'executable', 'package', 'application/vnd.debian.binary-package', 'Debian Package', '📦', '', 'DEB', is_binary=True, is_executable=True),
            '.rpm': FileTypeInfo(FileType.EXECUTABLE, 'executable', 'package', 'application/x-rpm', 'RPM Package', '📦', '', 'RPM', is_binary=True, is_executable=True),
            '.dmg': FileTypeInfo(FileType.EXECUTABLE, 'executable', 'disk_image', 'application/x-apple-diskimage', 'macOS Disk Image', '💿', '', 'DMG', is_binary=True, is_executable=True),
            '.app': FileTypeInfo(FileType.EXECUTABLE, 'executable', 'macos', 'application/x-apple-bundle', 'macOS Application', '📱', '', 'APP', is_binary=True, is_executable=True),

            # Scripts
            '.sh': FileTypeInfo(FileType.CODE, 'script', 'shell', 'application/x-shellscript', 'Shell Script', '📜', '', 'SH', is_text=True, is_executable=True),
            '.bash': FileTypeInfo(FileType.CODE, 'script', 'bash', 'application/x-shellscript', 'Bash Script', '📜', '', 'BASH', is_text=True, is_executable=True),
            '.zsh': FileTypeInfo(FileType.CODE, 'script', 'zsh', 'application/x-shellscript', 'Zsh Script', '📜', '', 'ZSH', is_text=True, is_executable=True),
            '.fish': FileTypeInfo(FileType.CODE, 'script', 'fish', 'application/x-shellscript', 'Fish Script', '🐟', '', 'FISH', is_text=True, is_executable=True),
            '.bat': FileTypeInfo(FileType.CODE, 'script', 'batch', 'application/x-bat', 'Batch Script', '📜', '', 'BAT', is_text=True, is_executable=True),
            '.cmd': FileTypeInfo(FileType.CODE, 'script', 'batch', 'application/x-bat', 'Command Script', '📜', '', 'CMD', is_text=True, is_executable=True),
            '.ps1': FileTypeInfo(FileType.CODE, 'script', 'powershell', 'application/x-powershell', 'PowerShell Script', '💙', '', 'PS1', is_text=True, is_executable=True),
        }

        # Special file patterns
        self.special_files = {
            'Dockerfile': FileTypeInfo(FileType.CODE, 'config', 'docker', 'text/plain', 'Docker Configuration', '🐳', '', 'DOCK', is_text=True),
            'Makefile': FileTypeInfo(FileType.CODE, 'build', 'make', 'text/x-makefile', 'Makefile', '🔨', '', 'MAKE', is_text=True),
            'CMakeLists.txt': FileTypeInfo(FileType.CODE, 'build', 'cmake', 'text/plain', 'CMake Configuration', '🔨', '', 'CMAKE', is_text=True),
            'package.json': FileTypeInfo(FileType.CODE, 'config', 'npm', 'application/json', 'NPM Package', '📦', '', 'NPM', is_text=True),
            'requirements.txt': FileTypeInfo(FileType.CODE, 'config', 'pip', 'text/plain', 'Python Requirements', '🐍', '', 'REQ', is_text=True),
            'Cargo.toml': FileTypeInfo(FileType.CODE, 'config', 'cargo', 'application/toml', 'Rust Cargo', '🦀', '', 'CARGO', is_text=True),
            'go.mod': FileTypeInfo(FileType.CODE, 'config', 'go_mod', 'text/plain', 'Go Module', '🐹', '', 'GOMOD', is_text=True),
            '.gitignore': FileTypeInfo(FileType.CODE, 'config', 'git', 'text/plain', 'Git Ignore', '📝', '', 'GIT', is_text=True),
            '.gitattributes': FileTypeInfo(FileType.CODE, 'config', 'git', 'text/plain', 'Git Attributes', '📝', '', 'GIT', is_text=True),
            'README.md': FileTypeInfo(FileType.DOCUMENT, 'document', 'readme', 'text/markdown', 'README Document', '📖', '', 'README', is_text=True),
            'LICENSE': FileTypeInfo(FileType.DOCUMENT, 'document', 'license', 'text/plain', 'License File', '📜', '', 'LIC', is_text=True),
        }

    def _init_icon_mappings(self):
        """Initialize icon mappings for different styles"""
        # Default fallback icons
        self.default_icons = {
            IconStyle.UNICODE: {
                FileType.DIRECTORY: '📁',
                FileType.FILE: '📄',
                FileType.IMAGE: '🖼️',
                FileType.VIDEO: '🎬',
                FileType.AUDIO: '🎵',
                FileType.ARCHIVE: '📦',
                FileType.CODE: '💻',
                FileType.DOCUMENT: '📝',
                FileType.EXECUTABLE: '⚙️',
                FileType.SYMLINK: '🔗',
                FileType.UNKNOWN: '❓'
            },
            IconStyle.NERD_FONT: {
                FileType.DIRECTORY: '',
                FileType.FILE: '',
                FileType.IMAGE: '',
                FileType.VIDEO: '',
                FileType.AUDIO: '',
                FileType.ARCHIVE: '',
                FileType.CODE: '',
                FileType.DOCUMENT: '',
                FileType.EXECUTABLE: '',
                FileType.SYMLINK: '',
                FileType.UNKNOWN: ''
            },
            IconStyle.ASCII: {
                FileType.DIRECTORY: '[DIR]',
                FileType.FILE: '[FILE]',
                FileType.IMAGE: '[IMG]',
                FileType.VIDEO: '[VID]',
                FileType.AUDIO: '[AUD]',
                FileType.ARCHIVE: '[ARC]',
                FileType.CODE: '[CODE]',
                FileType.DOCUMENT: '[DOC]',
                FileType.EXECUTABLE: '[EXE]',
                FileType.SYMLINK: '[LNK]',
                FileType.UNKNOWN: '[?]'
            }
        }

    def detect_file_type(self, path: Path) -> FileTypeInfo:
        """Detect file type using multiple methods"""
        try:
            # Handle directories
            if path.is_dir():
                return FileTypeInfo(
                    FileType.DIRECTORY, 'directory', 'folder', 'inode/directory',
                    'Directory', '📁', '', '[DIR]'
                )

            # Handle symlinks
            if path.is_symlink():
                return FileTypeInfo(
                    FileType.SYMLINK, 'symlink', 'link', 'inode/symlink',
                    'Symbolic Link', '🔗', '', '[LNK]'
                )

            # Check special files by name
            if path.name in self.special_files:
                return self.special_files[path.name]

            # Check by extension
            extension = path.suffix.lower()
            if extension in self.file_types:
                file_type_info = self.file_types[extension]

                # Check if file is executable
                if os.access(path, os.X_OK) and not file_type_info.is_executable:
                    # Create a copy with executable flag
                    return FileTypeInfo(
                        FileType.EXECUTABLE, file_type_info.category, file_type_info.subcategory,
                        file_type_info.mime_type, f"Executable {file_type_info.description}",
                        '⚙️', '', '[EXE]', is_executable=True,
                        is_binary=file_type_info.is_binary, is_text=file_type_info.is_text
                    )

                return file_type_info

            # Use magic library for unknown extensions
            if self.use_magic and self.magic_mime:
                try:
                    mime_type = self.magic_mime.from_file(str(path))
                    description = self.magic_desc.from_file(str(path))

                    # Determine file type from MIME type
                    file_type = self._mime_to_file_type(mime_type)
                    icon = self.default_icons[IconStyle.UNICODE].get(file_type, '❓')

                    return FileTypeInfo(
                        file_type, 'unknown', 'unknown', mime_type, description,
                        icon, '', f'[{file_type.value.upper()}]',
                        is_executable=os.access(path, os.X_OK),
                        is_binary='text' not in mime_type,
                        is_text='text' in mime_type
                    )

                except Exception as e:
                    self.logger.debug(f"Magic detection failed for {path}: {e}")

            # Fallback to basic MIME type detection
            mime_type, _ = mimetypes.guess_type(str(path))
            if mime_type:
                file_type = self._mime_to_file_type(mime_type)
                icon = self.default_icons[IconStyle.UNICODE].get(file_type, '❓')

                return FileTypeInfo(
                    file_type, 'unknown', 'unknown', mime_type, f'{file_type.value.title()} File',
                    icon, '', f'[{file_type.value.upper()}]',
                    is_executable=os.access(path, os.X_OK),
                    is_binary='text' not in mime_type,
                    is_text='text' in mime_type
                )

            # Final fallback
            return FileTypeInfo(
                FileType.UNKNOWN, 'unknown', 'unknown', None, 'Unknown File Type',
                '❓', '', '[?]',
                is_executable=os.access(path, os.X_OK)
            )

        except Exception as e:
            self.logger.error(f"Error detecting file type for {path}: {e}")
            return FileTypeInfo(
                FileType.UNKNOWN, 'unknown', 'unknown', None, 'Unknown File Type',
                '❓', '', '[?]'
            )

    def _mime_to_file_type(self, mime_type: str) -> FileType:
        """Convert MIME type to FileType enum"""
        if mime_type.startswith('image/'):
            return FileType.IMAGE
        elif mime_type.startswith('video/'):
            return FileType.VIDEO
        elif mime_type.startswith('audio/'):
            return FileType.AUDIO
        elif mime_type.startswith('text/'):
            return FileType.CODE if any(lang in mime_type for lang in ['python', 'javascript', 'html', 'css']) else FileType.DOCUMENT
        elif 'application/zip' in mime_type or 'compressed' in mime_type:
            return FileType.ARCHIVE
        elif 'application/pdf' in mime_type or 'document' in mime_type:
            return FileType.DOCUMENT
        elif 'executable' in mime_type or 'application/x-' in mime_type:
            return FileType.EXECUTABLE
        else:
            return FileType.FILE

    def get_icon(self, file_type_info: FileTypeInfo, style: IconStyle = IconStyle.UNICODE) -> str:
        """Get icon for file type in specified style"""
        if style == IconStyle.UNICODE:
            return file_type_info.icon_unicode
        elif style == IconStyle.NERD_FONT:
            return file_type_info.icon_nerd_font or file_type_info.icon_unicode
        elif style == IconStyle.ASCII:
            return file_type_info.icon_ascii
        else:
            return file_type_info.icon_unicode

    def get_supported_extensions(self) -> Set[str]:
        """Get set of all supported file extensions"""
        return set(self.file_types.keys())

    def get_file_types_by_category(self, category: str) -> List[FileTypeInfo]:
        """Get all file types in a specific category"""
        return [info for info in self.file_types.values() if info.category == category]

    def is_text_file(self, path: Path) -> bool:
        """Check if file is a text file"""
        file_type_info = self.detect_file_type(path)
        return file_type_info.is_text

    def is_binary_file(self, path: Path) -> bool:
        """Check if file is a binary file"""
        file_type_info = self.detect_file_type(path)
        return file_type_info.is_binary

    def is_executable_file(self, path: Path) -> bool:
        """Check if file is executable"""
        file_type_info = self.detect_file_type(path)
        return file_type_info.is_executable or os.access(path, os.X_OK)

    def get_file_category(self, path: Path) -> str:
        """Get file category"""
        file_type_info = self.detect_file_type(path)
        return file_type_info.category

    def get_file_description(self, path: Path) -> str:
        """Get human-readable file description"""
        file_type_info = self.detect_file_type(path)
        return file_type_info.description