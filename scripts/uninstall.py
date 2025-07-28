#!/usr/bin/env python3
"""
LaxyFile Uninstaller

This script removes LaxyFile installation and cleans up associated files.
"""

import os
import sys
import shutil
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any


class LaxyFileUninstaller:
    """LaxyFile uninstaller"""

    def __init__(self, manifest_path: Path, verbose: bool = False):
        self.manifest_path = Path(manifest_path)
        self.verbose = verbose
        self.manifest = self._load_manifest()

        if not self.manifest:
            raise Exception(f"Could not load installation manifest: {manifest_path}")

        print("LaxyFile Uninstaller")
        print(f"Installation directory: {self.manifest['install_dir']}")
        print()

    def _log(self, message: str, level: str = 'INFO'):
        """Log message"""
        if self.verbose or level in ['ERROR', 'WARNING']:
            print(f"[{level}] {message}")

    def _load_manifest(self) -> Dict[str, Any]:
        """Load installation manifest"""
        try:
            if not self.manifest_path.exists():
                return None

            with open(self.manifest_path, 'r') as f:
                return json.load(f)

        except Exception as e:
            print(f"Error loading manifest: {e}")
            return None

    def remove_installed_files(self) -> bool:
        """Remove installed files"""
        self._log("Removing installed files...")

        success = True
        removed_count = 0

        for file_path_str in self.manifest.get('installed_files', []):
            try:
                file_path = Path(file_path_str)
                if file_path.exists():
                    if file_path.is_file() or file_path.is_symlink():
                        file_path.unlink()
                        removed_count += 1
                        self._log(f"Removed file: {file_path}")
                    elif file_path.is_dir():
                        shutil.rmtree(file_path)
                        removed_count += 1
                        self._log(f"Removed directory: {file_path}")

            except Exception as e:
                self._log(f"Failed to remove {file_path_str}: {e}", 'ERROR')
                success = False

        self._log(f"Removed {removed_count} files/directories")
        return success

    def remove_directories(self) -> bool:
        """Remove created directories"""
        self._log("Removing installation directories...")

        success = True
        removed_count = 0

        # Sort directories by depth (deepest first)
        directories = sorted(
            self.manifest.get('created_directories', []),
            key=lambda x: len(Path(x).parts),
            reverse=True
        )

        for dir_path_str in directories:
            try:
                dir_path = Path(dir_path_str)
                if dir_path.exists() and dir_path.is_dir():
                    # Only remove if empty or if it's the main install directory
                    if (not any(dir_path.iterdir()) or
                        str(dir_path) == self.manifest['install_dir']):
                        shutil.rmtree(dir_path)
                        removed_count += 1
                        self._log(f"Removed directory: {dir_path}")
                    else:
                        self._log(f"Directory not empty, skipping: {dir_path}", 'WARNING')

            except Exception as e:
                self._log(f"Failed to remove directory {dir_path_str}: {e}", 'ERROR')
                success = False

        self._log(f"Removed {removed_count} directories")
        return success

    def remove_desktop_integration(self) -> bool:
        """Remove desktop integration"""
        if not self.manifest.get('desktop_integration', False):
            self._log("No desktop integration to remove")
            return True

        self._log("Removing desktop integration...")

        try:
            platform_system = self.manifest.get('platform', 'linux')

            if platform_system == 'linux':
                return self._remove_linux_desktop_integration()
            elif platform_system == 'darwin':
                return self._remove_macos_desktop_integration()
            elif platform_system == 'windows':
                return self._remove_windows_desktop_integration()

            return True

        except Exception as e:
            self._log(f"Failed to remove desktop integration: {e}", 'ERROR')
            return False

    def _remove_linux_desktop_integration(self) -> bool:
        """Remove Linux desktop integration"""
        success = True

        # Remove desktop entry
        desktop_file = Path.home() / '.local' / 'share' / 'applications' / 'laxyfile.desktop'
        if desktop_file.exists():
            try:
                desktop_file.unlink()
                self._log(f"Removed desktop entry: {desktop_file}")
            except Exception as e:
                self._log(f"Failed to remove desktop entry: {e}", 'ERROR')
                success = False

        # Remove MIME associations
        mime_file = Path.home() / '.local' / 'share' / 'mime' / 'packages' / 'com.laxyfile.LaxyFile.xml'
        if mime_file.exists():
            try:
                mime_file.unlink()
                self._log(f"Removed MIME associations: {mime_file}")
            except Exception as e:
                self._log(f"Failed to remove MIME associations: {e}", 'ERROR')
                success = False

        # Remove icons
        icon_sizes = ['16x16', '32x32', '48x48', '64x64', '128x128', '256x256']
        for size in icon_sizes:
            icon_file = Path.home() / '.local' / 'share' / 'icons' / 'hicolor' / size / 'apps' / 'com.laxyfile.LaxyFile.png'
            if icon_file.exists():
                try:
                    icon_file.unlink()
                    self._log(f"Removed icon: {icon_file}")
                except Exception as e:
                    self._log(f"Failed to remove icon: {e}", 'WARNING')

        # Update desktop database
        try:
            import subprocess
            if shutil.which('update-desktop-database'):
                subprocess.run([
                    'update-desktop-database',
                    str(Path.home() / '.local' / 'share' / 'applications')
                ], check=False)

            if shutil.which('update-mime-database'):
                subprocess.run([
                    'update-mime-database',
                    str(Path.home() / '.local' / 'share' / 'mime')
                ], check=False)

        except Exception as e:
            self._log(f"Failed to update desktop database: {e}", 'WARNING')

        return success

    def _remove_macos_desktop_integration(self) -> bool:
        """Remove macOS desktop integration"""
        app_bundle = Path.home() / 'Applications' / 'LaxyFile.app'
        if app_bundle.exists():
            try:
                shutil.rmtree(app_bundle)
                self._log(f"Removed app bundle: {app_bundle}")
                return True
            except Exception as e:
                self._log(f"Failed to remove app bundle: {e}", 'ERROR')
                return False

        return True

    def _remove_windows_desktop_integration(self) -> bool:
        """Remove Windows desktop integration"""
        success = True

        # Remove Start Menu shortcut
        start_menu_file = Path.home() / 'AppData' / 'Roaming' / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / 'LaxyFile.bat'
        if start_menu_file.exists():
            try:
                start_menu_file.unlink()
                self._log(f"Removed Start Menu shortcut: {start_menu_file}")
            except Exception as e:
                self._log(f"Failed to remove Start Menu shortcut: {e}", 'ERROR')
                success = False

        return success

    def remove_python_package(self) -> bool:
        """Remove Python package installation"""
        self._log("Removing Python package...")

        try:
            import subprocess

            # Try to uninstall using pip
            result = subprocess.run([
                sys.executable, '-m', 'pip', 'uninstall', 'laxyfile', '-y'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                self._log("Removed Python package")
                return True
            else:
                self._log("Python package not found or already removed", 'WARNING')
                return True

        except Exception as e:
            self._log(f"Failed to remove Python package: {e}", 'WARNING')
            return True  # Don't fail uninstallation for this

    def remove_user_data(self, remove_config: bool = False) -> bool:
        """Remove user data and configuration"""
        if not remove_config:
            self._log("Keeping user configuration (use --remove-config to remove)")
            return True

        self._log("Removing user data and configuration...")

        success = True

        # Platform-specific config directories
        platform_system = self.manifest.get('platform', 'linux')

        if platform_system == 'windows':
            config_dirs = [
                Path.home() / 'AppData' / 'Roaming' / 'LaxyFile',
                Path.home() / 'AppData' / 'Local' / 'LaxyFile'
            ]
        elif platform_system == 'darwin':
            config_dirs = [
                Path.home() / 'Library' / 'Application Support' / 'LaxyFile',
                Path.home() / 'Library' / 'Preferences' / 'com.laxyfile.LaxyFile.plist'
            ]
        else:  # Linux
            config_dirs = [
                Path.home() / '.config' / 'laxyfile',
                Path.home() / '.local' / 'share' / 'laxyfile',
                Path.home() / '.cache' / 'laxyfile'
            ]

        for config_dir in config_dirs:
            if config_dir.exists():
                try:
                    if config_dir.is_file():
                        config_dir.unlink()
                    else:
                        shutil.rmtree(config_dir)
                    self._log(f"Removed user data: {config_dir}")
                except Exception as e:
                    self._log(f"Failed to remove user data {config_dir}: {e}", 'ERROR')
                    success = False

        return success

    def uninstall(self, remove_config: bool = False) -> bool:
        """Run complete uninstallation"""
        try:
            self._log("Starting LaxyFile uninstallation...")

            success = True

            # Remove Python package
            if not self.remove_python_package():
                success = False

            # Remove desktop integration
            if not self.remove_desktop_integration():
                success = False

            # Remove installed files
            if not self.remove_installed_files():
                success = False

            # Remove directories
            if not self.remove_directories():
                success = False

            # Remove user data (optional)
            if not self.remove_user_data(remove_config):
                success = False

            # Remove manifest file last
            try:
                if self.manifest_path.exists():
                    self.manifest_path.unlink()
                    self._log(f"Removed manifest: {self.manifest_path}")
            except Exception as e:
                self._log(f"Failed to remove manifest: {e}", 'WARNING')

            if success:
                self._log("Uninstallation completed successfully!")
            else:
                self._log("Uninstallation completed with some errors", 'WARNING')

            return success

        except Exception as e:
            self._log(f"Uninstallation failed: {e}", 'ERROR')
            return False


def find_installation_manifest() -> Path:
    """Find installation manifest automatically"""
    # Common installation locations
    search_paths = []

    if sys.platform == 'win32':
        search_paths = [
            Path(os.environ.get('PROGRAMFILES', 'C:\\\\Program Files')) / 'LaxyFile' / 'install_manifest.json',
            Path.home() / 'AppData' / 'Local' / 'LaxyFile' / 'install_manifest.json'
        ]
    elif sys.platform == 'darwin':
        search_paths = [
            Path('/Applications/LaxyFile/install_manifest.json'),
            Path.home() / 'Applications' / 'LaxyFile' / 'install_manifest.json'
        ]
    else:  # Linux
        search_paths = [
            Path('/opt/laxyfile/install_manifest.json'),
            Path.home() / '.local' / 'share' / 'laxyfile' / 'install_manifest.json',
            Path('/usr/local/share/laxyfile/install_manifest.json')
        ]

    for path in search_paths:
        if path.exists():
            return path

    return None


def main():
    """Main uninstaller entry point"""
    parser = argparse.ArgumentParser(description='LaxyFile Uninstaller')

    parser.add_argument(
        'manifest',
        nargs='?',
        help='Path to installation manifest (auto-detected if not provided)'
    )

    parser.add_argument(
        '--remove-config',
        action='store_true',
        help='Remove user configuration and data'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Find manifest file
    if args.manifest:
        manifest_path = Path(args.manifest)
    else:
        manifest_path = find_installation_manifest()
        if not manifest_path:
            print("ERROR: Could not find installation manifest.")
            print("Please provide the path to install_manifest.json")
            sys.exit(1)

    if not manifest_path.exists():
        print(f"ERROR: Manifest file not found: {manifest_path}")
        sys.exit(1)

    try:
        uninstaller = LaxyFileUninstaller(manifest_path, args.verbose)

        # Confirm uninstallation
        install_dir = uninstaller.manifest['install_dir']
        print(f"This will remove LaxyFile from: {install_dir}")

        if args.remove_config:
            print("User configuration and data will also be removed.")

        response = input("Continue? [y/N]: ").strip().lower()
        if response not in ['y', 'yes']:
            print("Uninstallation cancelled.")
            sys.exit(0)

        success = uninstaller.uninstall(args.remove_config)
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()