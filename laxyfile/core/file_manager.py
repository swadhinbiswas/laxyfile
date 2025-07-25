"""
Core File Manager - Handles all file operations
"""

import os
import shutil
import stat
import time
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

try:
    from send2trash import send2trash
    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False

from ..utils.logger import Logger

class FileInfo:
    """File information container"""

    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.is_dir = path.is_dir()
        self.is_file = path.is_file()
        self.is_symlink = path.is_symlink()

        try:
            stat_info = path.stat()
            self.size = stat_info.st_size
            self.modified = stat_info.st_mtime
            self.created = stat_info.st_ctime
            self.permissions = stat.filemode(stat_info.st_mode)
            self.owner = stat_info.st_uid
            self.group = stat_info.st_gid
        except (OSError, PermissionError):
            self.size = 0
            self.modified = 0
            self.created = 0
            self.permissions = "----------"
            self.owner = 0
            self.group = 0

        # Get file type
        if self.is_dir:
            self.file_type = "directory"
            self.mime_type = "inode/directory"
        elif self.is_file:
            try:
                if HAS_MAGIC:
                    self.mime_type = magic.from_file(str(path), mime=True)
                else:
                    # Fallback: determine mime type from extension
                    self.mime_type = self._get_mime_from_extension()
                self.file_type = self._get_file_type()
            except:
                self.mime_type = "application/octet-stream"
                self.file_type = "unknown"
        else:
            self.mime_type = "unknown"
            self.file_type = "special"

    def _get_mime_from_extension(self) -> str:
        """Fallback method to get MIME type from file extension"""
        ext = self.path.suffix.lower()

        mime_map = {
            '.txt': 'text/plain',
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.xml': 'application/xml',
            '.pdf': 'application/pdf',
            '.zip': 'application/zip',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.mp3': 'audio/mpeg',
            '.mp4': 'video/mp4',
            '.py': 'text/x-python',
        }

        return mime_map.get(ext, 'application/octet-stream')

    def _get_file_type(self) -> str:
        """Determine file type from extension and mime type"""
        ext = self.path.suffix.lower()

        # Images
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico']:
            return "image"
        # Videos
        elif ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']:
            return "video"
        # Audio
        elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a']:
            return "audio"
        # Documents
        elif ext in ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt']:
            return "document"
        # Archives
        elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz']:
            return "archive"
        # Code
        elif ext in ['.py', '.js', '.html', '.css', '.cpp', '.c', '.java', '.rs', '.go']:
            return "code"
        # Configuration
        elif ext in ['.json', '.yaml', '.yml', '.xml', '.ini', '.conf', '.cfg']:
            return "config"
        else:
            return "file"

    def get_size_formatted(self) -> str:
        """Get human-readable file size"""
        if self.is_dir:
            return "<DIR>"

        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def get_modified_formatted(self) -> str:
        """Get formatted modification time"""
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(self.modified))

class FileManager:
    """Main file manager class"""

    def __init__(self):
        self.logger = Logger()
        self.clipboard = []
        self.clipboard_operation = None  # 'copy' or 'cut'
        self.current_directory = Path.cwd()

    def list_directory(self, path: Path, show_hidden: bool = False) -> List[FileInfo]:
        """List files in directory"""
        try:
            files = []

            # Add parent directory entry if not root
            if path.parent != path:
                parent_info = FileInfo(path.parent)
                parent_info.name = ".."
                files.append(parent_info)

            for item in path.iterdir():
                if not show_hidden and item.name.startswith('.'):
                    continue

                try:
                    file_info = FileInfo(item)
                    files.append(file_info)
                except (PermissionError, OSError) as e:
                    self.logger.warning(f"Cannot access {item}: {e}")

            # Sort: directories first, then files, alphabetically
            files.sort(key=lambda x: (not x.is_dir, x.name.lower()))
            return files

        except (PermissionError, OSError) as e:
            self.logger.error(f"Cannot list directory {path}: {e}")
            return []

    def create_directory(self, path: Path, name: str) -> bool:
        """Create a new directory"""
        try:
            new_dir = path / name
            new_dir.mkdir(exist_ok=False)
            self.logger.info(f"Created directory: {new_dir}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create directory {name}: {e}")
            return False

    def create_file(self, path: Path, name: str) -> bool:
        """Create a new file"""
        try:
            new_file = path / name
            new_file.touch(exist_ok=False)
            self.logger.info(f"Created file: {new_file}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to create file {name}: {e}")
            return False

    def rename_item(self, old_path: Path, new_name: str) -> bool:
        """Rename a file or directory"""
        try:
            new_path = old_path.parent / new_name
            old_path.rename(new_path)
            self.logger.info(f"Renamed {old_path.name} to {new_name}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to rename {old_path.name}: {e}")
            return False

    def delete_items(self, items: List[Path], use_trash: bool = True) -> bool:
        """Delete files/directories"""
        try:
            for item in items:
                if use_trash and HAS_SEND2TRASH:
                    send2trash(str(item))
                    self.logger.info(f"Moved to trash: {item}")
                else:
                    if item.is_dir():
                        shutil.rmtree(item)
                    else:
                        item.unlink()
                    self.logger.info(f"Permanently deleted: {item}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete items: {e}")
            return False

    def copy_items(self, items: List[Path], destination: Path) -> bool:
        """Copy files/directories"""
        try:
            for item in items:
                dest_path = destination / item.name
                if item.is_dir():
                    shutil.copytree(item, dest_path)
                else:
                    shutil.copy2(item, dest_path)
                self.logger.info(f"Copied {item} to {dest_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to copy items: {e}")
            return False

    def move_items(self, items: List[Path], destination: Path) -> bool:
        """Move files/directories"""
        try:
            for item in items:
                dest_path = destination / item.name
                shutil.move(str(item), str(dest_path))
                self.logger.info(f"Moved {item} to {dest_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to move items: {e}")
            return False

    def copy_to_clipboard(self, items: List[Path]):
        """Copy items to clipboard"""
        self.clipboard = items.copy()
        self.clipboard_operation = 'copy'
        self.logger.info(f"Copied {len(items)} items to clipboard")

    def cut_to_clipboard(self, items: List[Path]):
        """Cut items to clipboard"""
        self.clipboard = items.copy()
        self.clipboard_operation = 'cut'
        self.logger.info(f"Cut {len(items)} items to clipboard")

    def paste_from_clipboard(self, destination: Path) -> bool:
        """Paste items from clipboard"""
        if not self.clipboard:
            return False

        try:
            if self.clipboard_operation == 'copy':
                return self.copy_items(self.clipboard, destination)
            elif self.clipboard_operation == 'cut':
                result = self.move_items(self.clipboard, destination)
                if result:
                    self.clipboard.clear()
                    self.clipboard_operation = None
                return result
        except Exception as e:
            self.logger.error(f"Failed to paste: {e}")
            return False

    def get_directory_size(self, path: Path) -> int:
        """Get total size of directory"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(path):
                for filename in filenames:
                    filepath = Path(dirpath) / filename
                    try:
                        total_size += filepath.stat().st_size
                    except (OSError, PermissionError):
                        continue
        except (OSError, PermissionError):
            pass
        return total_size

    def get_disk_usage(self, path: Path) -> Dict[str, int]:
        """Get disk usage information"""
        try:
            if HAS_PSUTIL:
                usage = psutil.disk_usage(str(path))
                return {
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': (usage.used / usage.total) * 100
                }
            else:
                # Fallback using shutil
                import shutil
                total, used, free = shutil.disk_usage(path)
                return {
                    'total': total,
                    'used': used,
                    'free': free,
                    'percent': (used / total) * 100 if total > 0 else 0
                }
        except Exception as e:
            self.logger.error(f"Failed to get disk usage: {e}")
            return {'total': 0, 'used': 0, 'free': 0, 'percent': 0}

    def search_files(self, path: Path, pattern: str, case_sensitive: bool = False) -> List[FileInfo]:
        """Search for files matching pattern"""
        results = []
        try:
            if not case_sensitive:
                pattern = pattern.lower()

            for item in path.rglob('*'):
                if item.is_file():
                    name = item.name if case_sensitive else item.name.lower()
                    if pattern in name:
                        results.append(FileInfo(item))

        except Exception as e:
            self.logger.error(f"Search failed: {e}")

        return results[:100]  # Limit results