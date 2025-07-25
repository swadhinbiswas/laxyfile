#!/usr/bin/env python3
"""
LaxyFile Cross-Platform Installer

This script provides a unified installation experience across different platforms,
handling dependencies, desktop integration, and configuration setup.
"""

import os
import sys
import platform
import subprocess
import shutil
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import tempfile
import urllib.request
import zipfile
import tarfile

# Add parent directory to path to import LaxyFile modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from laxyfile.operations.platform_ops import PlatformManager, PlatformType
    from laxyfile.operations.desktop_integration import DesktopIntegration
    from laxyfile.core.config import Config
    from laxyfile.utils.logger import Logger
except ImportError:
    # Fallback for standalone installer
    PlatformManager = None
    DesktopIntegration = None
    Config = None
    Logger = None


class LaxyFileInstaller:
    """Cross-platform LaxyFile installer"""

    def __init__(self, args):
        self.args = args
        self.platform_system = platform.system().lower()
        self.install_dir = Path(args.install_dir) if args.install_dir else self._get_default_install_dir()
        self.create_desktop_integration = args.desktop_integration
        self.install_dependencies = args.install_deps
        self.verbose = args.verbose

        # Installation state
        self.temp_dir = Path(tempfile.mkdtemp(prefix='laxyfile_install_'))
        self.installed_files = []
        self.created_directories = []

        print(f"LaxyFile Installer")
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Install directory: {self.install_dir}")
        print()

    def _get_default_install_dir(self) -> Path:
        """Get default installation directory for platform"""
        if self.platform_system == 'windows':
            return Path(os.environ.get('PROGRAMFILES', 'C:\\\\Program Files')) / 'LaxyFile'
        elif self.platform_system == 'darwin':
            return Path('/Applications/LaxyFile')
        else:  # Linux and other Unix-like
            return Path('/opt/laxyfile')

    def _log(self, message: str, level: str = 'INFO'):
        """Log message"""
        if self.verbose or'ERROR', 'WARNING']:
            print(f"[{level}] {message}")

    def _run_command(self, command: List[str], check: bool = True) -> subprocess.CompletedProcess:
        """Run command with logging"""
        self._log(f"Running: {' '.join(command)}")

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=check
            )

            if result.stdout and self.verbose:
                self._log(f"STDOUT: {result.stdout}")

            if result.stderr and self.verbose:
                self._log(f"STDERR: {result.stderr}")

            return result

        except subprocess.CalledProcessError as e:
            self._log(f"Command failed: {e}", 'ERROR')
            if e.stdout:
                self._log(f"STDOUT: {e.stdout}", 'ERROR')
            if e.stderr:
                self._log(f"STDERR: {e.stderr}", 'ERROR')
            raise

    def check_prerequisites(self) -> bool:
        """Check installation prerequisites"""
        self._log("Checking prerequisites...")

        # Check Python version
        if sys.version_info < (3, 8):
            self._log("Python 3.8 or higher is required", 'ERROR')
            return False

        self._log(f"Python version: {sys.version}")

        # Check pip
        try:
            self._run_command([sys.executable, '-m', 'pip', '--version'])
        except subprocess.CalledProcessError:
            self._log("pip is required but not found", 'ERROR')
            return False

        # Check platform-specific prerequisites
        if self.platform_system == 'linux':
            return self._check_linux_prerequisites()
        elif self.platform_system == 'darwin':
            return self._check_macos_prerequisites()
        elif self.platform_system == 'windows':
            return self._check_windows_prerequisites()

        return True

    def _check_linux_prerequisites(self) -> bool:
        """Check Linux-specific prerequisites"""
        # Check for required system packages
        required_packages = {
            'git': 'git',
            'curl': 'curl',
            'build-essential': 'gcc'  # Check for gcc as indicator
        }

        missing_packages = []
        for package, check_command in required_packages.items():
            if not shutil.which(check_command):
                missing_packages.append(package)

        if missing_packages:
            self._log(f"Missing system packages: {', '.join(missing_packages)}", 'WARNING')
            self._log("Please install them using your package manager", 'WARNING')

        return True  # Don't fail on missing packages, just warn

    def _check_macos_prerequisites(self) -> bool:
        """Check macOS-specific prerequisites"""
        # Check for Xcode command line tools
        try:
            self._run_command(['xcode-select', '--print-path'])
        except subprocess.CalledProcessError:
            self._log("Xcode command line tools not found", 'WARNING')
            self._log("Run: xcode-select --install", 'WARNING')

        return True

    def _check_windows_prerequisites(self) -> bool:
        """Check Windows-specific prerequisites"""
        # Check for Visual C++ Build Tools (for some Python packages)
        # This is optional, so just warn if not found
        return True

    def install_dependencies(self) -> bool:
        """Install Python dependencies"""
        if not self.install_dependencies:
            self._log("Skipping dependency installation")
            return True

        self._log("Installing Python dependencies...")

        try:
            # Install from requirements.txt if available
            requirements_file = Path(__file__).parent.parent / 'requirements.txt'
            if requirements_file.exists():
                self._run_command([
                    sys.executable, '-m', 'pip', 'install',
                    '-r', str(requirements_file)
                ])
            else:
                # Install core dependencies
                core_deps = [
                    'rich>=13.0.0',
                    'click>=8.0.0',
                    'pyyaml>=6.0',
                    'watchdog>=3.0.0',
                    'python-magic>=0.4.27',
                    'pillow>=9.0.0',
                    'pygments>=2.14.0'
                ]

                self._run_command([
                    sys.executable, '-m', 'pip', 'install'
                ] + core_deps)

            # Install optional dependencies based on platform
            self._install_platform_dependencies()

            return True

        except subprocess.CalledProcessError:
            self._log("Failed to install dependencies", 'ERROR')
            return False

    def _install_platform_dependencies(self):
        """Install platform-specific dependencies"""
        platform_deps = []

        if self.platform_system == 'windows':
            platform_deps.extend([
                'pywin32>=306',
                'colorama>=0.4.6'
            ])
        elif self.platform_system == 'linux':
            platform_deps.extend([
                'python-xlib>=0.33'
            ])

        if platform_deps:
            try:
                self._run_command([
                    sys.executable, '-m', 'pip', 'install'
                ] + platform_deps)
            except subprocess.CalledProcessError:
                self._log("Some platform-specific dependencies failed to install", 'WARNING')

    def install_laxyfile(self) -> bool:
        """Install LaxyFile application"""
        self._log("Installing LaxyFile...")

        try:
            # Create installation directory
            self.install_dir.mkdir(parents=True, exist_ok=True)
            self.created_directories.append(self.install_dir)

            # Copy LaxyFile source
            source_dir = Path(__file__).parent.parent
            laxyfile_source = source_dir / 'laxyfile'

            if laxyfile_source.exists():
                # Copy from local source
                self._copy_directory(laxyfile_source, self.install_dir / 'laxyfile')
            else:
                # Download from repository (if this is a standalone installer)
                if not self._download_laxyfile():
                    return False

            # Copy additional files
            additional_files = [
                'main.py',
                'run_laxyfile.py',
                'setup.py',
                'pyproject.toml',
                'README.md',
                'LICENSE'
            ]

            for file_name in additional_files:
                source_file = source_dir / file_name
                if source_file.exists():
                    dest_file = self.install_dir / file_name
                    shutil.copy2(source_file, dest_file)
                    self.installed_files.append(dest_file)

            # Create launcher script
            self._create_launcher_script()

            # Install as Python package (development mode)
            if (self.install_dir / 'setup.py').exists():
                self._run_command([
                    sys.executable, '-m', 'pip', 'install', '-e', str(self.install_dir)
                ])

            return True

        except Exception as e:
            self._log(f"Failed to install LaxyFile: {e}", 'ERROR')
            return False

    def _copy_directory(self, source: Path, destination: Path):
        """Copy directory recursively"""
        self._log(f"Copying {source} to {destination}")

        if destination.exists():
            shutil.rmtree(destination)

        shutil.copytree(source, destination)
        self.created_directories.append(destination)

    def _download_laxyfile(self) -> bool:
        """Download LaxyFile from repository"""
        self._log("Downloading LaxyFile from repository...")

        try:
            # Download from GitHub (example URL)
            download_url = "https://github.com/user/laxyfile/archive/main.zip"

            # Download to temp directory
            zip_file = self.temp_dir / 'laxyfile.zip'

            with urllib.request.urlopen(download_url) as response:
                with open(zip_file, 'wb') as f:
                    shutil.copyfileobj(response, f)

            # Extract
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)

            # Find extracted directory
            extracted_dirs = [d for d in self.temp_dir.iterdir() if d.is_dir()]
            if not extracted_dirs:
                raise Exception("No directory found in downloaded archive")

            source_dir = extracted_dirs[0]

            # Copy to installation directory
            self._copy_directory(source_dir / 'laxyfile', self.install_dir / 'laxyfile')

            return True

        except Exception as e:
            self._log(f"Failed to download LaxyFile: {e}", 'ERROR')
            return False

    def _create_launcher_script(self):
        """Create platform-specific launcher script"""
        if self.platform_system == 'windows':
            self._create_windows_launcher()
        else:
            self._create_unix_launcher()

    def _create_windows_launcher(self):
        """Create Windows batch launcher"""
        launcher_content = f'''@echo off
set LAXYFILE_HOME={self.install_dir}
cd /d "%LAXYFILE_HOME%"
{sys.executable} -m laxyfile %*
'''

        launcher_file = self.install_dir / 'laxyfile.bat'
        launcher_file.write_text(launcher_content)
        self.installed_files.append(launcher_file)

        # Add to PATH (optional)
        if self.args.add_to_path:
            self._add_to_windows_path()

    def _create_unix_launcher(self):
        """Create Unix shell launcher"""
        launcher_content = f'''#!/bin/bash
export LAXYFILE_HOME="{self.install_dir}"
cd "$LAXYFILE_HOME"
exec {sys.executable} -m laxyfile "$@"
'''

        launcher_file = self.install_dir / 'laxyfile'
        launcher_file.write_text(launcher_content)
        launcher_file.chmod(0o755)
        self.installed_files.append(launcher_file)

        # Create symlink in /usr/local/bin (if writable)
        if self.args.add_to_path:
            self._create_unix_symlink()

    def _add_to_windows_path(self):
        """Add LaxyFile to Windows PATH"""
        try:
            # This would require registry manipulation
            # For now, just inform the user
            self._log("To add LaxyFile to PATH, add this directory to your PATH environment variable:")
            self._log(str(self.install_dir))

        except Exception as e:
            self._log(f"Failed to add to PATH: {e}", 'WARNING')

    def _create_unix_symlink(self):
        """Create symlink in /usr/local/bin"""
        try:
            bin_dir = Path('/usr/local/bin')
            if bin_dir.exists() and os.access(bin_dir, os.W_OK):
                symlink_path = bin_dir / 'laxyfile'
                if symlink_path.exists():
                    symlink_path.unlink()

                symlink_path.symlink_to(self.install_dir / 'laxyfile')
                self.installed_files.append(symlink_path)
                self._log(f"Created symlink: {symlink_path}")
            else:
                self._log("Cannot create symlink in /usr/local/bin (no write permission)", 'WARNING')
                self._log("You may need to run with sudo or add to PATH manually", 'WARNING')

        except Exception as e:
            self._log(f"Failed to create symlink: {e}", 'WARNING')

    def install_desktop_integration(self) -> bool:
        """Install desktop integration"""
        if not self.create_desktop_integration:
            self._log("Skipping desktop integration")
            return True

        self._log("Installing desktop integration...")

        try:
            # Use LaxyFile's desktop integration if available
            if DesktopIntegration and Config:
                config = Config()
                integration = DesktopIntegration(config)
                return integration.install_desktop_integration()
            else:
                # Fallback implementation
                return self._install_basic_desktop_integration()

        except Exception as e:
            self._log(f"Failed to install desktop integration: {e}", 'ERROR')
            return False

    def _install_basic_desktop_integration(self) -> bool:
        """Basic desktop integration fallback"""
        if self.platform_system == 'linux':
            return self._install_linux_desktop_entry()
        elif self.platform_system == 'darwin':
            return self._install_macos_app_bundle()
        elif self.platform_system == 'windows':
            return self._install_windows_start_menu()

        return True

    def _install_linux_desktop_entry(self) -> bool:
        """Install Linux desktop entry"""
        try:
            desktop_dir = Path.home() / '.local' / 'share' / 'applications'
            desktop_dir.mkdir(parents=True, exist_ok=True)

            desktop_content = f'''[Desktop Entry]
Version=1.0
Type=Application
Name=LaxyFile
Exec={self.install_dir}/laxyfile %F
Terminal=true
Categories=System;FileManager;Utility;
Comment=Advanced terminal file manager with AI capabilities
'''

            desktop_file = desktop_dir / 'laxyfile.desktop'
            desktop_file.write_text(desktop_content)
            desktop_file.chmod(0o755)

            self.installed_files.append(desktop_file)
            return True

        except Exception as e:
            self._log(f"Failed to install Linux desktop entry: {e}", 'ERROR')
            return False

    def _install_macos_app_bundle(self) -> bool:
        """Install macOS app bundle"""
        # This would create a proper .app bundle
        self._log("macOS app bundle installation not implemented in basic installer")
        return True

    def _install_windows_start_menu(self) -> bool:
        """Install Windows Start Menu entry"""
        try:
            start_menu_dir = Path.home() / 'AppData' / 'Roaming' / 'Microsoft' / 'Windows' / 'Start Menu' / 'Programs'
            start_menu_dir.mkdir(parents=True, exist_ok=True)

            shortcut_content = f'''@echo off
cd /d "{self.install_dir}"
{sys.executable} -m laxyfile %*
'''

            shortcut_file = start_menu_dir / 'LaxyFile.bat'
            shortcut_file.write_text(shortcut_content)

            self.installed_files.append(shortcut_file)
            return True

        except Exception as e:
            self._log(f"Failed to install Windows Start Menu entry: {e}", 'ERROR')
            return False

    def create_uninstaller(self):
        """Create uninstaller script"""
        self._log("Creating uninstaller...")

        # Create installation manifest
        manifest = {
            'install_dir': str(self.install_dir),
            'installed_files': [str(f) for f in self.installed_files],
            'created_directories': [str(d) for d in self.created_directories],
            'platform': self.platform_system,
            'install_time': str(datetime.now()),
            'desktop_integration': self.create_desktop_integration
        }

        manifest_file = self.install_dir / 'install_manifest.json'
        manifest_file.write_text(json.dumps(manifest, indent=2))

        # Create uninstaller script
        if self.platform_system == 'windows':
            uninstaller_content = f'''@echo off
echo Uninstalling LaxyFile...
{sys.executable} "{Path(__file__).parent / 'uninstall.py'}" "{manifest_file}"
'''
            uninstaller_file = self.install_dir / 'uninstall.bat'
        else:
            uninstaller_content = f'''#!/bin/bash
echo "Uninstalling LaxyFile..."
{sys.executable} "{Path(__file__).parent / 'uninstall.py'}" "{manifest_file}"
'''
            uninstaller_file = self.install_dir / 'uninstall.sh'

        uninstaller_file.write_text(uninstaller_content)
        if not self.platform_system == 'windows':
            uninstaller_file.chmod(0o755)

    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            self._log(f"Failed to clean up temp files: {e}", 'WARNING')

    def install(self) -> bool:
        """Run complete installation"""
        try:
            self._log("Starting LaxyFile installation...")

            # Check prerequisites
            if not self.check_prerequisites():
                return False

            # Install dependencies
            if not self.install_dependencies():
                return False

            # Install LaxyFile
            if not self.install_laxyfile():
                return False

            # Install desktop integration
            if not self.install_desktop_integration():
                self._log("Desktop integration failed, but continuing...", 'WARNING')

            # Create uninstaller
            self.create_uninstaller()

            self._log("Installation completed successfully!")
            self._log(f"LaxyFile installed to: {self.install_dir}")

            if self.platform_system != 'windows':
                self._log(f"Run: {self.install_dir}/laxyfile")
            else:
                self._log(f"Run: {self.install_dir}\\\\laxyfile.bat")

            return True

        except Exception as e:
            self._log(f"Installation failed: {e}", 'ERROR')
            return False

        finally:
            self.cleanup_temp_files()


def main():
    """Main installer entry point"""
    parser = argparse.ArgumentParser(description='LaxyFile Cross-Platform Installer')

    parser.add_argument(
        '--install-dir',
        help='Installation directory (default: platform-specific)'
    )

    parser.add_argument(
        '--no-deps',
        dest='install_deps',
        action='store_false',
        help='Skip dependency installation'
    )

    parser.add_argument(
        '--no-desktop',
        dest='desktop_integration',
        action='store_false',
        help='Skip desktop integration'
    )

    parser.add_argument(
        '--add-to-path',
        action='store_true',
        help='Add LaxyFile to system PATH'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Check if running as root/administrator
    if os.geteuid() == 0 if hasattr(os, 'geteuid') else False:
        print("WARNING: Running as root. Consider installing to user directory.")
        print()

    installer = LaxyFileInstaller(args)
    success = installer.install()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()