"""
Platform-Specific Operations

This module provides platform-specific file operations and integrations
for Windows, macOS, and Linux systems.
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from ..core.exceptions import PlatformError
from ..utils.logger import Logger


class PlatformType(Enum):
    """Supported platform types"""
    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


@dataclass
class PlatformInfo:
    """Platform information"""
    platform_type: PlatformType
    system: str
    release: str
    version: str
    machine: str
    processor: str
    python_version: str

    # Platform-specific info
    desktop_environment: Optional[str] = None
    shell: Optional[str] = None
    package_manager: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'platform_type': self.platform_type.value,
            'system': self.system,
            'release': self.release,
            'version': self.version,
            'machine': self.machine,
            'processor': self.processor,
            'python_version': self.python_version,
            'desktop_environment': self.desktop_environment,
            'shell': self.shell,
            'package_manager': self.package_manager
        }


class PlatformInterface(ABC):
    """Abstract interface for platform-specific operations"""

    def __init__(self):
        self.logger = Logger()

    @abstractmethod
    def get_platform_info(self) -> PlatformInfo:
        """Get platform information"""
        pass

    @abstractmethod
    def get_trash_directory(self) -> Path:
        """Get platform-specific trash directory"""
        pass

    @abstractmethod
    async def move_to_trash(self, file_path: Path) -> bool:
        """Move file to trash/recycle bin"""
        pass

    @abstractmethod
    async def empty_trash(self) -> bool:
        """Empty trash/recycle bin"""
        pass

    @abstractmethod
    def get_file_associations(self, file_path: Path) -> List[str]:
        """Get applications associated with file type"""
        pass

    @abstractmethod
    async def open_with_default_app(self, file_path: Path) -> bool:
        """Open file with default application"""
        pass

    @abstractmethod
    async def show_in_file_manager(self, file_path: Path) -> bool:
        """Show file in system file manager"""
        pass

    @abstractmethod
    def get_system_directories(self) -> Dict[str, Path]:
        """Get system directories (home, documents, downloads, etc.)"""
        pass

    @abstractmethod
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize path for platform"""
        pass


class WindowsPlatform(PlatformInterface):
    """Windows-specific platform operations"""

    def __init__(self):
        super().__init__()
        self._check_windows_dependencies()

    def _check_windows_dependencies(self):
        """Check for Windows-specific dependencies"""
        try:
            import winreg
            import win32api
            import win32con
            import win32file
            self.winreg = winreg
            self.win32api = win32api
            self.win32con = win32con
            self.win32file = win32file
        except ImportError as e:
            self.logger.warning(f"Windows-specific modules not available: {e}")
            self.winreg = None
            self.win32api = None

    def get_platform_info(self) -> PlatformInfo:
        """Get Windows platform information"""
        return PlatformInfo(
            platform_type=PlatformType.WINDOWS,
            system=platform.system(),
            release=platform.release(),
            version=platform.version(),
            machine=platform.machine(),
            processor=platform.processor(),
            python_version=sys.version,
            shell=os.environ.get('COMSPEC', 'cmd.exe'),
            package_manager=self._detect_package_manager()
        )

    def _detect_package_manager(self) -> Optional[str]:
        """Detect Windows package manager"""
        managers = ['winget', 'choco', 'scoop']

        for manager in managers:
            if shutil.which(manager):
                return manager

        return None

    def get_trash_directory(self) -> Path:
        """Get Windows Recycle Bin directory"""
        # Windows Recycle Bin is virtual, return a temp directory for staging
        return Path(os.environ.get('TEMP', 'C:\\\\Temp')) / 'LaxyFile_Trash'

    async def move_to_trash(self, file_path: Path) -> bool:
        """Move file to Windows Recycle Bin"""
        try:
            if not file_path.exists():
                return False

            # Use Windows Shell API to move to recycle bin
            if self.win32api:
                try:
                    import win32file
                    import win32con

                    # Use SHFileOperation to move to recycle bin
                    result = win32file.SHFileOperation((
                        0,  # hwnd
                        win32con.FO_DELETE,  # operation
                        str(file_path),  # source
                        None,  # destination
                        win32con.FOF_ALLOWUNDO | win32con.FOF_NOCONFIRMATION,  # flags
                        None,  # progress title
                        None   # progress text
                    ))

                    return result[0] == 0  # 0 means success

                except Exception as e:
                    self.logger.error(f"Error using Windows Shell API: {e}")

            # Fallback: move to staging directory
            trash_dir = self.get_trash_directory()
            trash_dir.mkdir(parents=True, exist_ok=True)

            trash_path = trash_dir / file_path.name
            counter = 1
            while trash_path.exists():
                name_parts = file_path.stem, counter, file_path.suffix
                trash_path = trash_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                counter += 1

            shutil.move(str(file_path), str(trash_path))
            return True

        except Exception as e:
            self.logger.error(f"Error moving file to trash: {e}")
            return False

    async def empty_trash(self) -> bool:
        """Empty Windows Recycle Bin"""
        try:
            if self.win32api:
                try:
                    import win32file
                    import win32con

                    # Empty recycle bin for all drives
                    result = win32file.SHEmptyRecycleBin(
                        0,  # hwnd
                        None,  # root path (None = all drives)
                        win32con.SHERB_NOCONFIRMATN | win32con.SHERB_NOPROGRESSUI
                    )

                    return result == 0

                except Exception as e:
                    self.logger.error(f"Error emptying recycle bin: {e}")

            # Fallback: empty staging directory
            trash_dir = self.get_trash_directory()
            if trash_dir.exists():
                shutil.rmtree(trash_dir)
                return True

            return True

        except Exception as e:
            self.logger.error(f"Error emptying trash: {e}")
            return False

    def get_file_associations(self, file_path: Path) -> List[str]:
        """Get Windows file associations"""
        associations = []

        try:
            if self.winreg:
                extension = file_path.suffix.lower()

                # Get file type from extension
                try:
                    with self.winreg.OpenKey(self.winreg.HKEY_CLASSES_ROOT, extension) as key:
                        file_type, _ = self.winreg.QueryValueEx(key, "")
                except FileNotFoundError:
                    return associations

                # Get command for file type
                try:
                    command_path = f"{file_type}\\\\shell\\\\open\\\\command"
                    with self.winreg.OpenKey(self.winreg.HKEY_CLASSES_ROOT, command_path) as key:
                        command, _ = self.winreg.QueryValueEx(key, "")
                        associations.append(command)
                except FileNotFoundError:
                    pass

        except Exception as e:
            self.logger.error(f"Error getting file associations: {e}")

        return associations

    async def open_with_default_app(self, file_path: Path) -> bool:
        """Open file with default Windows application"""
        try:
            if self.win32api:
                try:
                    self.win32api.ShellExecute(0, "open", str(file_path), None, None, 1)
                    return True
                except Exception as e:
                    self.logger.error(f"Error using ShellExecute: {e}")

            # Fallback to os.startfile
            os.startfile(str(file_path))
            return True

        except Exception as e:
            self.logger.error(f"Error opening file with default app: {e}")
            return False

    async def show_in_file_manager(self, file_path: Path) -> bool:
        """Show file in Windows Explorer"""
        try:
            if file_path.is_file():
                # Select file in Explorer
                subprocess.run(['explorer', '/select,', str(file_path)], check=True)
            else:
                # Open directory in Explorer
                subprocess.run(['explorer', str(file_path)], check=True)

            return True

        except Exception as e:
            self.logger.error(f"Error showing file in Explorer: {e}")
            return False

    def get_system_directories(self) -> Dict[str, Path]:
        """Get Windows system directories"""
        directories = {}

        try:
            # Standard Windows directories
            directories['home'] = Path.home()
            directories['desktop'] = Path.home() / 'Desktop'
            directories['documents'] = Path.home() / 'Documents'
            directories['downloads'] = Path.home() / 'Downloads'
            directories['music'] = Path.home() / 'Music'
            directories['pictures'] = Path.home() / 'Pictures'
            directories['videos'] = Path.home() / 'Videos'

            # System directories
            directories['program_files'] = Path(os.environ.get('PROGRAMFILES', 'C:\\\\Program Files'))
            directories['program_files_x86'] = Path(os.environ.get('PROGRAMFILES(X86)', 'C:\\\\Program Files (x86)'))
            directories['windows'] = Path(os.environ.get('WINDIR', 'C:\\\\Windows'))
            directories['system32'] = Path(os.environ.get('WINDIR', 'C:\\\\Windows')) / 'System32'
            directories['temp'] = Path(os.environ.get('TEMP', 'C:\\\\Temp'))

        except Exception as e:
            self.logger.error(f"Error getting system directories: {e}")

        return directories

    def normalize_pathed_files=[pa Union[str, Path]) -> Path:
        """Normalize Windows path"""
        path = Path(path)

        # Convert forward slashes to backslashes
        path_str = str(path).replace('/', '\\\\')

        # Resolve path
        try:
            return Path(path_str).resolve()
        except Exception:
            return Path(path_str)


class MacOSPlatform(PlatformInterface):
    """macOS-specific platform operations"""

    def get_platform_info(self) -> PlatformInfo:
        """Get macOS platform information"""
        return PlatformInfo(
            platform_type=PlatformType.MACOS,
            system=platform.system(),
            release=platform.release(),
            version=platform.version(),
            machine=platform.machine(),
            processor=platform.processor(),
            python_version=sys.version,
            shell=os.environ.get('SHELL', '/bin/bash'),
            package_manager=self._detect_package_manager()
        )

    def _detect_package_manager(self) -> Optional[str]:
        """Detect macOS package manager"""
        managers = ['brew', 'port', 'fink']

        for manager in managers:
            if shutil.which(manager):
                return manager

        return None

    def get_trash_directory(self) -> Path:
        """Get macOS Trash directory"""
        return Path.home() / '.Trash'

    async def move_to_trash(self, file_path: Path) -> bool:
        """Move file to macOS Trash"""
        try:
            if not file_path.exists():
                return False

            # Use osascript to move to trash (preserves Trash functionality)
            script = f'''
            tell application "Finder"
                move POSIX file "{file_path}" to trash
            end tell
            '''

            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return True

            # Fallback: move to .Trash directory
            trash_dir = self.get_trash_directory()
            trash_path = trash_dir / file_path.name

            counter = 1
            while trash_path.exists():
                name_parts = file_path.stem, counter, file_path.suffix
                trash_path = trash_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                counter += 1

            shutil.move(str(file_path), str(trash_path))
            return True

        except Exception as e:
            self.logger.error(f"Error moving file to trash: {e}")
            return False

    async def empty_trash(self) -> bool:
        """Empty macOS Trash"""
        try:
            # Use osascript to empty trash
            script = '''
            tell application "Finder"
                empty trash
            end tell
            '''

            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True
            )

            return result.returncode == 0

        except Exception as e:
            self.logger.error(f"Error emptying trash: {e}")
            return False

    def get_file_associations(self, file_path: Path) -> List[str]:
        """Get macOS file associations"""
        associations = []

        try:
            # Use Launch Services to get default application
            result = subprocess.run([
                'duti', '-x', file_path.suffix
            ], capture_output=True, text=True)

            if result.returncode == 0:
                associations.append(result.stdout.strip())

        except Exception as e:
            self.logger.error(f"Error getting file associations: {e}")

        return associations

    async def open_with_default_app(self, file_path: Path) -> bool:
        """Open file with default macOS application"""
        try:
            subprocess.run(['open', str(file_path)], check=True)
            return True

        except Exception as e:
            self.logger.error(f"Error opening file with default app: {e}")
            return False

    async def show_in_file_manager(self, file_path: Path) -> bool:
        """Show file in macOS Finder"""
        try:
            if file_path.is_file():
                # Select file in Finder
                subprocess.run(['open', '-R', str(file_path)], check=True)
            else:
                # Open directory in Finder
                subprocess.run(['open', str(file_path)], check=True)

            return True

        except Exception as e:
            self.logger.error(f"Error showing file in Finder: {e}")
            return False

    def get_system_directories(self) -> Dict[str, Path]:
        """Get macOS system directories"""
        directories = {}

        try:
            # Standard macOS directories
            directories['home'] = Path.home()
            directories['desktop'] = Path.home() / 'Desktop'
            directories['documents'] = Path.home() / 'Documents'
            directories['downloads'] = Path.home() / 'Downloads'
            directories['music'] = Path.home() / 'Music'
            directories['pictures'] = Path.home() / 'Pictures'
            directories['movies'] = Path.home() / 'Movies'
            directories['public'] = Path.home() / 'Public'

            # System directories
            directories['applications'] = Path('/Applications')
            directories['library'] = Path('/Library')
            directories['system'] = Path('/System')
            directories['usr'] = Path('/usr')
            directories['tmp'] = Path('/tmp')

            # User library
            directories['user_library'] = Path.home() / 'Library'
            directories['application_support'] = Path.home() / 'Library' / 'Application Support'

        except Exception as e:
            self.logger.error(f"Error getting system directories: {e}")

        return directories

    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize macOS path"""
        path = Path(path)

        # Expand user directory
        if str(path).startswith('~'):
            path = path.expanduser()

        # Resolve path
        try:
            return path.resolve()
        except Exception:
            return path


class LinuxPlatform(PlatformInterface):
    """Linux-specific platform operations"""

    def __init__(self):
        super().__init__()
        self.desktop_environment = self._detect_desktop_environment()

    def _detect_desktop_environment(self) -> Optional[str]:
        """Detect Linux desktop environment"""
        # Check environment variables
        desktop_vars = [
            'XDG_CURRENT_DESKTOP',
            'DESKTOP_SESSION',
            'GDMSESSION'
        ]

        for var in desktop_vars:
            value = os.environ.get(var)
            if value:
                return value.lower()

        # Check for specific desktop processes
        desktop_processes = {
            'gnome-shell': 'gnome',
            'kwin': 'kde',
            'xfwm4': 'xfce',
            'openbox': 'openbox',
            'i3': 'i3',
            'awesome': 'awesome'
        }

        try:
            result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
            processes = result.stdout

            for process, desktop in desktop_processes.items():
                if process in processes:
                    return desktop

        except Exception:
            pass

        return None

    def get_platform_info(self) -> PlatformInfo:
        """Get Linux platform information"""
        return PlatformInfo(
            platform_type=PlatformType.LINUX,
            system=platform.system(),
            release=platform.release(),
            version=platform.version(),
            machine=platform.machine(),
            processor=platform.processor(),
            python_version=sys.version,
            desktop_environment=self.desktop_environment,
            shell=os.environ.get('SHELL', '/bin/bash'),
            package_manager=self._detect_package_manager()
        )

    def _detect_package_manager(self) -> Optional[str]:
        """Detect Linux package manager"""
        managers = [
            'apt', 'yum', 'dnf', 'pacman', 'zypper',
            'emerge', 'apk', 'snap', 'flatpak'
        ]

        for manager in managers:
            if shutil.which(manager):
                return manager

        return None

    def get_trash_directory(self) -> Path:
        """Get Linux trash directory"""
        # Follow XDG Base Directory Specification
        xdg_data_home = os.environ.get('XDG_DATA_HOME')
        if xdg_data_home:
            return Path(xdg_data_home) / 'Trash'
        else:
            return Path.home() / '.local' / 'share' / 'Trash'

    async def move_to_trash(self, file_path: Path) -> bool:
        """Move file to Linux trash"""
        try:
            if not file_path.exists():
                return False

            # Try using gio (GNOME/GTK)
            if shutil.which('gio'):
                result = subprocess.run(
                    ['gio', 'trash', str(file_path)],
                    capture_output=True
                )
                if result.returncode == 0:
                    return True

            # Try using trash-cli
            if shutil.which('trash'):
                result = subprocess.run(
                    ['trash', str(file_path)],
                    capture_output=True
                )
                if result.returncode == 0:
                    return True

            # Fallback: manual trash implementation
            trash_dir = self.get_trash_directory()
            files_dir = trash_dir / 'files'
            info_dir = trash_dir / 'info'

            files_dir.mkdir(parents=True, exist_ok=True)
            info_dir.mkdir(parents=True, exist_ok=True)

            # Generate unique name
            trash_name = file_path.name
            counter = 1
            while (files_dir / trash_name).exists():
                name_parts = file_path.stem, counter, file_path.suffix
                trash_name = f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                counter += 1

            # Move file
            trash_file_path = files_dir / trash_name
            shutil.move(str(file_path), str(trash_file_path))

            # Create info file
            info_content = f"""[Trash Info]
Path={file_path}
DeletionDate={datetime.now().strftime('%Y-%m-%dT%H:%M:%S')}
"""
            info_file_path = info_dir / f"{trash_name}.trashinfo"
            info_file_path.write_text(info_content)

            return True

        except Exception as e:
            self.logger.error(f"Error moving file to trash: {e}")
            return False

    async def empty_trash(self) -> bool:
        """Empty Linux trash"""
        try:
            # Try using gio
            if shutil.which('gio'):
                result = subprocess.run(['gio', 'trash', '--empty'], capture_output=True)
                if result.returncode == 0:
                    return True

            # Try using trash-cli
            if shutil.which('trash-empty'):
                result = subprocess.run(['trash-empty'], capture_output=True)
                if result.returncode == 0:
                    return True

            # Fallback: manual empty
            trash_dir = self.get_trash_directory()
            if trash_dir.exists():
                shutil.rmtree(trash_dir)
                return True

            return True

        except Exception as e:
            self.logger.error(f"Error emptying trash: {e}")
            return False

    def get_file_associations(self, file_path: Path) -> List[str]:
        """Get Linux file associations"""
        associations = []
            supports_acl=True,
         ry:
            # Use xdg-mime to get default application
            result = subprocess.run([
                'xdg-mime', 'query', 'default', self._get_mime_type(file_path)
            ], capture_output=True, text=True)

            if result.returncode == 0:
                desktop_file = result.stdout.strip()
                if desktop_file:
                    associations.append(desktop_file)

        except Exception as e:
            self.logger.error(f"Error getting file associations: {e}")

        return associations

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type of file"""
        try:
            result = subprocess.run([
                'file', '--mime-type', '-b', str(file_path)
            ], capture_output=True, text=True)

            if result.returncode == 0:
                return result.stdout.strip()

        except Exception:
            pass

        # Fallback to extension-based detection
        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'application/octet-stream'

    async def open_with_default_app(self, file_path: Path) -> bool:
        """Open file with default Linux application"""
        try:
            # Try xdg-open (most common)
            if shutil.which('xdg-open'):
                subprocess.run(['xdg-open', str(file_path)], check=True)
                return True

            # Try desktop-specific openers
            openers = ['gnome-open', 'kde-open', 'exo-open']
            for opener in openers:
                if shutil.which(opener):
                    subprocess.run([opener, str(file_path)], check=True)
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error opening file with default app: {e}")
            return False

    async def show_in_file_manager(self, file_path: Path) -> bool:
        """Show file in Linux file manager"""
        try:
            # Try desktop-specific file managers
            if self.desktop_environment == 'gnome':
                subprocess.run(['nautilus', '--select', str(file_path)], check=True)
            elif self.desktop_environment == 'kde':
                subprocess.run(['dolphin', '--select', str(file_path)], check=True)
            elif self.desktop_environment == 'xfce':
                subprocess.run(['thunar', str(file_path.parent)], check=True)
            else:
                # Generic approach
                if file_path.is_file():
                    subprocess.run(['xdg-open', str(file_path.parent)], check=True)
                else:
                    subprocess.run(['xdg-open', str(file_path)], check=True)

            return True

        except Exception as e:
            self.logger.error(f"Error showing file in file manager: {e}")
            return False

    def get_system_directories(self) -> Dict[str, Path]:
        """Get Linux system directories"""
        directories = {}

        try:
            # Standard user directories
            directories['home'] = Path.home()

            # XDG user directories
            xdg_dirs = {
                'desktop': 'XDG_DESKTOP_DIR',
                'documents': 'XDG_DOCUMENTS_DIR',
                'downloads': 'XDG_DOWNLOAD_DIR',
                'music': 'XDG_MUSIC_DIR',
                'pictures': 'XDG_PICTURES_DIR',
                'videos': 'XDG_VIDEOS_DIR',
                'templates': 'XDG_TEMPLATES_DIR',
                'public': 'XDG_PUBLICSHARE_DIR'
            }

            # Try to get XDG directories from user-dirs.dirs
            user_dirs_file = Path.home() / '.config' / 'user-dirs.dirs'
            if user_dirs_file.exists():
                content = user_dirs_file.read_text()
                for line in content.splitlines():
                    if '=' in line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').replace('$HOME', str(Path.home()))

                        for dir_name, env_var in xdg_dirs.items():
                            if key == env_var:
                                directories[dir_name] = Path(value)

            # Fallback to standard directories
            fallback_dirs = {
                'desktop': Path.home() / 'Desktop',
                'documents': Path.home() / 'Documents',
                'downloads': Path.home() / 'Downloads',
                'music': Path.home() / 'Music',
                'pictures': Path.home() / 'Pictures',
                'videos': Path.home() / 'Videos'
            }

            for name, path in fallback_dirs.items():
                if name not in directories:
                    directories[name] = path

            # System directories
            directories['root'] = Path('/')
            directories['usr'] = Path('/usr')
            directories['etc'] = Path('/etc')
            directories['var'] = Path('/var')
            directories['tmp'] = Path('/tmp')
            directories['opt'] = Path('/opt')

        except Exception as e:
            self.logger.error(f"Error getting system directories: {e}")

        return directories

    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize Linux path"""
        path = Path(path)

        # Expand user directory
        if str(path).startswith('~'):
            path = path.expanduser()

        # Resolve path
        try:
            return path.resolve()
        except Exception:
            return path


class PlatformManager:
    """Manager for platform-specific operations"""

    def __init__(self):
        self.logger = Logger()
        self.platform_interface = self._create_platform_interface()

    def _create_platform_interface(self) -> PlatformInterface:
        """Create appropriate platform interface"""
        system = platform.system().lower()

        if system == 'windows':
            return WindowsPlatform()
        elif system == 'darwin':
            return MacOSPlatform()
        elif system == 'linux':
            return LinuxPlatform()
        else:
            self.logger.warning(f"Unsupported platform: {system}")
            # Return Linux as fallback for Unix-like systems
            return LinuxPlatform()

    def get_platform_type(self) -> PlatformType:
        """Get current platform type"""
        return self.platform_interface.get_platform_info().platform_type

    def get_platform_info(self) -> PlatformInfo:
        """Get platform information"""
        return self.platform_interface.get_platform_info()

    async def move_to_trash(self, file_path: Path) -> bool:
        """Move file to platform-specific trash"""
        return await self.platform_interface.move_to_trash(file_path)

    async def empty_trash(self) -> bool:
        """Empty platform-specific trash"""
        return await self.platform_interface.empty_trash()

    def get_file_associations(self, file_path: Path) -> List[str]:
        """Get file associations"""
        return self.platform_interface.get_file_associations(file_path)

    async def open_with_default_app(self, file_path: Path) -> bool:
        """Open file with default application"""
        return await self.platform_interface.open_with_default_app(file_path)

    async def show_in_file_manager(self, file_path: Path) -> bool:
        """Show file in system file manager"""
        return await self.platform_interface.show_in_file_manager(file_path)

    def get_system_directories(self) -> Dict[str, Path]:
        """Get system directories"""
        return self.platform_interface.get_system_directories()

    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize path for current platform"""
        return self.platform_interface.normalize_path(path)

    def is_windows(self) -> bool:
        """Check if running on Windows"""
        return self.get_platform_type() == PlatformType.WINDOWS

    def is_macos(self) -> bool:
        """Check if running on macOS"""
        return self.get_platform_type() == PlatformType.MACOS

    def is_linux(self) -> bool:
        """Check if running on Linux"""
        return self.get_platform_type() == PlatformType.LINUX