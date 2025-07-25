"""
Desktop Integration

This module provides desktop environment integration for LaxyFile,
including file associations, desktop entries, and system integration.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from configparser import ConfigParser

from .platform_ops import PlatformManager, PlatformType
from ..core.config import Config
from ..utils.logger import Logger


@dataclass
class DesktopEntry:
    """Desktop entry information"""
    name: str
    exec_command: str
    icon: Optional[str] = None
    comment: Optional[str] = None
    categories: List[str] = None
    mime_types: List[str] = None
    terminal: bool = True

    def __post_init__(self):
        if self.categories is None:
            self.categories = ["System", "FileManager", "Utility"]
        if self.mime_types is None:
            self.mime_types = ["inode/directory"]


class DesktopIntegration:
    """Desktop environment integration manager"""

    def __init__(self, config: Config):
        self.config = config
        self.logger = Logger()
        self.platform_manager = PlatformManager()

        # Desktop integration settings
        self.app_name = "LaxyFile"
        self.app_id = "com.laxyfile.LaxyFile"
        self.executable_name = "laxyfile"

    async def install_desktop_integration(self) -> bool:
        """Install desktop integration for current platform"""
        try:
            platform_type = self.platform_manager.get_platform_type()

            if platform_type == PlatformType.LINUX:
                return await self._install_linux_integration()
            elif platform_type == PlatformType.MACOS:
                return await self._install_macos_integration()
            elif platform_type == PlatformType.WINDOWS:
                return await self._install_windows_integration()
            else:
                self.logger.warning(f"Desktop integration not supported for platform: {platform_type}")
                return False

        except Exception as e:
            self.logger.error(f"Error installing desktop integration: {e}")
            return False

    async def uninstall_desktop_integration(self) -> bool:
        """Uninstall desktop integration"""
        try:
            platform_type = self.platform_manager.get_platform_type()

            if platform_type == PlatformType.LINUX:
                return await self._uninstall_linux_integration()
            elif platform_type == PlatformType.MACOS:
                return await self._uninstall_macos_integration()
            elif platform_type == PlatformType.WINDOWS:
                return await self._uninstall_windows_integration()
            else:
                return False

        except Exception as e:
            self.logger.error(f"Error uninstalling desktop integration: {e}")
            return False

    # Linux Integration
    async def _install_linux_integration(self) -> bool:
        """Install Linux desktop integration"""
        success = True

        # Install desktop entry
        if not await self._install_linux_desktop_entry():
            success = False

        # Install MIME type associations
        if not await self._install_linux_mime_types():
            success = False

        # Install application icon
        if not await self._install_linux_icon():
            success = False

        # Update desktop database
        await self._update_linux_desktop_database()

        return success

    async def _install_linux_desktop_entry(self) -> bool:
        """Install Linux desktop entry"""
        try:
            # Get desktop entry directory
            desktop_dir = Path.home() / '.local' / 'share' / 'applications'
            desktop_dir.mkdir(parents=True, exist_ok=True)

            # Create desktop entry
            desktop_entry = DesktopEntry(
                name=self.app_name,
                exec_command=f"{self.executable_name} %F",
                icon=self.app_id,
                comment="Advanced terminal file manager with AI capabilities",
                categories=["System", "FileManager", "Utility"],
                mime_types=["inode/directory"],
                terminal=True
            )

            # Write desktop file
            desktop_file = desktop_dir / f"{self.app_id}.desktop"
            desktop_content = self._create_desktop_file_content(desktop_entry)
            desktop_file.write_text(desktop_content)

            # Make executable
            desktop_file.chmod(0o755)

            self.logger.info(f"Installed desktop entry: {desktop_file}")
            return True

        except Exception as e:
            self.logger.error(f"Error installing Linux desktop entry: {e}")
            return False

    def _create_desktop_file_content(self, entry: DesktopEntry) -> str:
        """Create desktop file content"""
        content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name={entry.name}
Exec={entry.exec_command}
Terminal={str(entry.terminal).lower()}
Categories={';'.join(entry.categories)};
"""

        if entry.icon:
            content += f"Icon={entry.icon}\\n"

        if entry.comment:
            content += f"Comment={entry.comment}\\n"

        if entry.mime_types:
            content += f"MimeType={';'.join(entry.mime_types)};\\n"

        return content

    async def _install_linux_mime_types(self) -> bool:
        """Install Linux MIME type associations"""
        try:
            # Create MIME type associations
            mime_dir = Path.home() / '.local' / 'share' / 'mime' / 'packages'
            mime_dir.mkdir(parents=True, exist_ok=True)

            # Create MIME package file
            mime_file = mime_dir / f"{self.app_id}.xml"
            mime_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
    <mime-type type="application/x-laxyfile-project">
        <comment>LaxyFile Project</comment>
        <glob pattern="*.laxyproj"/>
    </mime-type>
</mime-info>
'''
            mime_file.write_text(mime_content)

            # Update MIME database
            if shutil.which('update-mime-database'):
                subprocess.run([
                    'update-mime-database',
                    str(Path.home() / '.local' / 'share' / 'mime')
                ], check=False)

            # Set default application for directories
            if shutil.which('xdg-mime'):
                subprocess.run([
                    'xdg-mime', 'default',
                    f"{self.app_id}.desktop",
                    'inode/directory'
                ], check=False)

            return True

        except Exception as e:
            self.logger.error(f"Error installing Linux MIME types: {e}")
            return False

    async def _install_linux_icon(self) -> bool:
        """Install Linux application icon"""
        try:
            # Icon directories for different sizes
            icon_sizes = ['16x16', '32x32', '48x48', '64x64', '128x128', '256x256']

            for size in icon_sizes:
                icon_dir = Path.home() / '.local' / 'share' / 'icons' / 'hicolor' / size / 'apps'
                icon_dir.mkdir(parents=True, exist_ok=True)

                # Create a simple icon (in real implementation, use actual icon files)
                icon_file = icon_dir / f"{self.app_id}.png"

                # For now, just create a placeholder
                # In real implementation, copy actual icon files
                if not icon_file.exists():
                    icon_file.touch()

            # Update icon cache
            if shutil.which('gtk-update-icon-cache'):
                subprocess.run([
                    'gtk-update-icon-cache',
                    str(Path.home() / '.local' / 'share' / 'icons' / 'hicolor')
                ], check=False)

            return True

        except Exception as e:
            self.logger.error(f"Error installing Linux icon: {e}")
            return False

    async def _update_linux_desktop_database(self):
        """Update Linux desktop database"""
        try:
            if shutil.which('update-desktop-database'):
                subprocess.run([
                    'update-desktop-database',
                    str(Path.home() / '.local' / 'share' / 'applications')
                ], check=False)

        except Exception as e:
            self.logger.error(f"Error updating desktop database: {e}")

    async def _uninstall_linux_integration(self) -> bool:
        """Uninstall Linux desktop integration"""
        try:
            success = True

            # Remove desktop entry
            desktop_file = Path.home() / '.local' / 'share' / 'applications' / f"{self.app_id}.desktop"
            if desktop_file.exists():
                desktop_file.unlink()

            # Remove MIME types
            mime_file = Path.home() / '.local' / 'share' / 'mime' / 'packages' / f"{self.app_id}.xml"
            if mime_file.exists():
                mime_file.unlink()

            # Remove icons
            icon_sizes = ['16x16', '32x32', '48x48', '64x64', '128x128', '256x256']
            for size in icon_sizes:
                icon_file = Path.home() / '.local' / 'share' / 'icons' / 'hicolor' / size / 'apps' / f"{self.app_id}.png"
                if icon_file.exists():
                    icon_file.unlink()

            # Update databases
            await self._update_linux_desktop_database()

            if shutil.which('update-mime-database'):
                subprocess.run([
                    'update-mime-database',
                    str(Path.home() / '.local' / 'share' / 'mime')
 check=False)

            return success

        except Exception as e:
            self.logger.error(f"Error uninstalling Linux integration: {e}")
            return False

    # macOS Integration
    async def _install_macos_integration(self) -> bool:
        """Install macOS desktop integration"""
        try:
            # Create application bundle structure
            app_bundle_dir = Path.home() / 'Applications' / f"{self.app_name}.app"
            contents_dir = app_bundle_dir / 'Contents'
            macos_dir = contents_dir / 'MacOS'
            resources_dir = contents_dir / 'Resources'

            # Create directories
            macos_dir.mkdir(parents=True, exist_ok=True)
            resources_dir.mkdir(parents=True, exist_ok=True)

            # Create Info.plist
            info_plist = contents_dir / 'Info.plist'
            plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>{self.executable_name}</string>
    <key>CFBundleIdentifier</key>
    <string>{self.app_id}</string>
    <key>CFBundleName</key>
    <string>{self.app_name}</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>LXYF</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.12</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>CFBundleDocumentTypes</key>
    <array>
        <dict>
            <key>CFBundleTypeRole</key>
            <string>Viewer</string>
            <key>LSHandlerRank</key>
            <string>Alternate</string>
            <key>LSItemContentTypes</key>
            <array>
                <string>public.folder</string>
            </array>
        </dict>
    </array>
</dict>
</plist>
'''
            info_plist.write_text(plist_content)

            # Create executable script
            executable_script = macos_dir / self.executable_name
            script_content = f'''#!/bin/bash
exec {shutil.which('python3') or 'python3'} -m laxyfile "$@"
'''
            executable_script.write_text(script_content)
            executable_script.chmod(0o755)

            self.logger.info(f"Installed macOS application bundle: {app_bundle_dir}")
            return True

        except Exception as e:
            self.logger.error(f"Error installing macOS integration: {e}")
            return False

    async def _uninstall_macos_integration(self) -> bool:
        """Uninstall macOS desktop integration"""
        try:
            app_bundle_dir = Path.home() / 'Applications' / f"{self.app_name}.app"
            if app_bundle_dir.exists():
                shutil.rmtree(app_bundle_dir)

            return True

        except Exception as e:
            self.logger.error(f"Error uninstalling macOS integration: {e}")
            return False

    # Windows Integration
    async def _install_windows_integration(self) -> bool:
        """Install Windows desktop integration"""
        try:
            success = True

            # Create Start Menu shortcut
            if not await self._create_windows_start_menu_shortcut():
                success = False

            # Register file associations
            if not await self._register_windows_file_associations():
                success = False

            # Add to Windows PATH (optional)
            if not await self._add_to_windows_path():
                success = False

            return success

        except Exception as e:
            self.logger.error(f"Error installing Windows integration: {e}")
            return False

    async def _create_windows_start_menu_shortcut(self) -> bool:
        """Create Windows Start Menu shortcut"""
        try:
            # This would require pywin32 or similar for proper implementation
            start_menu_dir = Path.home() / 'AppData' / 'Roaming' / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs'
            start_menu_dir.mkdir(parents=True, exist_ok=True)

            # Create batch file as shortcut
            shortcut_file = start_menu_dir / f"{self.app_name}.bat"
            batch_content = f'''@echo off
{sys.executable} -m laxyfile %*
'''
            shortcut_file.write_text(batch_content)

            return True

        except Exception as e:
            self.logger.error(f"Error creating Windows Start Menu shortcut: {e}")
            return False

    async def _register_windows_file_associations(self) -> bool:
        """Register Windows file associations"""
        try:
            # This would require registry manipulation
            # For now, just log the intent
            self.logger.info("Windows file associations would be registered here")
            return True

        except Exception as e:
            self.logger.error(f"Error registering Windows file associations: {e}")
            return False

    async def _add_to_windows_path(self) -> bool:
        """Add LaxyFile to Windows PATH"""
        try:
            # This would require registry manipulation
            # For now, just log the intent
            self.logger.info("LaxyFile would be added to Windows PATH here")
            return True

        except Exception as e:
            self.logger.error(f"Error adding to Windows PATH: {e}")
            return False

    async def _uninstall_windows_integration(self) -> bool:
        """Uninstall Windows desktop integration"""
        try:
            # Remove Start Menu shortcut
            shortcut_file = Path.home() / 'AppData' / 'Roaming' / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / f"{self.app_name}.bat"
            if shortcut_file.exists():
                shortcut_file.unlink()

            return True

        except Exception as e:
            self.logger.error(f"Error uninstalling Windows integration: {e}")
            return False

    # Common methods
    def is_desktop_integration_installed(self) -> bool:
        """Check if desktop integration is installed"""
        platform_type = self.platform_manager.get_platform_type()

        if platform_type == PlatformType.LINUX:
            desktop_file = Path.home() / '.local' / 'share' / 'applications' / f"{self.app_id}.desktop"
            return desktop_file.exists()

        elif platform_type == PlatformType.MACOS:
            app_bundle = Path.home() / 'Applications' / f"{self.app_name}.app"
            return app_bundle.exists()

        elif platform_type == PlatformType.WINDOWS:
            shortcut_file = Path.home() / 'AppData' / 'Roaming' / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs' / f"{self.app_name}.bat"
            return shortcut_file.exists()

        return False

    def get_integration_status(self) -> Dict[str, Any]:
        """Get desktop integration status"""
        return {
            'platform': self.platform_manager.get_platform_type().value,
            'installed': self.is_desktop_integration_installed(),
            'app_name': self.app_name,
            'app_id': self.app_id,
            'executable_name': self.executable_name
        }


# CLI commands for desktop integration
async def install_desktop_integration(config: Config) -> bool:
    """Install desktop integration"""
    integration = DesktopIntegration(config)
    return await integration.install_desktop_integration()


async def uninstall_desktop_integration(config: Config) -> bool:
    """Uninstall desktop integration"""
    integration = DesktopIntegration(config)
    return await integration.uninstall_desktop_integration()


def check_desktop_integration_status(config: Config) -> Dict[str, Any]:
    """Check desktop integration status"""
    integration = DesktopIntegration(config)
    return integration.get_integration_status()