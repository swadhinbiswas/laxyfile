#!/usr/bin/env python3
"""
macOS Application Bundle Builder for LaxyFile

This script creates a macOS .app bundle and optionally a DMG installer.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import plistlib
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class MacOSAppBuilder:
    """macOS application bundle builder"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.build_dir = self.project_root / 'build' / 'macos'
        self.dist_dir = self.project_root / 'dist' / 'macos'

        # App information
        self.app_name = "LaxyFile"
        self.app_version = "1.0.0"
        self.app_identifier = "com.laxyfile.LaxyFile"
        self.app_description = "Advanced terminal file manager with AI capabilities"
        self.app_author = "LaxyFile Team"
        self.app_copyright = "Copyright © 2024 LaxyFile Team"

        # Ensure build directories exist
        self.build_dir.mkdir(parents=True, exist_ok=True)
        self.dist_dir.mkdir(parents=True, exist_ok=True)

    def prepare_source(self):
        """Prepare source files for packaging"""
        print("Preparing source files...")

        # Copy LaxyFile source
        source_dir = self.project_root / 'laxyfile'
        target_dir = self.build_dir / 'laxyfile'

        if target_dir.exists():
            shutil.rmtree(target_dir)

        shutil.copytree(source_dir, target_dir)

        # Copy additional files
        additional_files = [
            'main.py',
            'run_laxyfile.py',
            'README.md',
            'LICENSE',
            'requirements.txt'
        ]

        for file_name in additional_files:
            source_file = self.project_root / file_name
            if source_file.exists():
                shutil.copy2(source_file, self.build_dir / file_name)

        print(f"Source prepared in: {self.build_dir}")

    def create_app_bundle(self):
        """Create macOS .app bundle"""
        print("Creating macOS app bundle...")

        app_bundle_dir = self.dist_dir / f"{self.app_name}.app"
        contents_dir = app_bundle_dir / 'Contents'
        macos_dir = contents_dir / 'MacOS'
        resources_dir = contents_dir / 'Resources'
        frameworks_dir = contents_dir / 'Frameworks'

        # Create directory structure
        for directory in [macos_dir, resources_dir, frameworks_dir]:
            directory.mkdir(parents=True, exist_ok=True)

        # Create Info.plist
        self._create_info_plist(contents_dir)

        # Copy application resources
        self._copy_app_resources(resources_dir)

        # Create executable script
        self._create_executable_script(macos_dir)

        # Copy Python dependencies (if needed)
        self._copy_python_dependencies(resources_dir)

        print(f"App bundle created: {app_bundle_dir}")
        return app_bundle_dir

    def _create_info_plist(self, contents_dir: Path):
        """Create Info.plist file"""
        info_plist = {
            'CFBundleDevelopmentRegion': 'en',
            'CFBundleExecutable': self.app_name.lower(),
            'CFBundleIdentifier': self.app_identifier,
            'CFBundleInfoDictionaryVersion': '6.0',
            'CFBundleName': self.app_name,
            'CFBundleDisplayName': self.app_name,
            'CFBundlePackageType': 'APPL',
            'CFBundleShortVersionString': self.app_version,
            'CFBundleVersion': self.app_version,
            'CFBundleSignature': 'LXYF',
            'LSMinimumSystemVersion': '10.12',
            'NSHighResolutionCapable': True,
            'NSSupportsAutomaticGraphicsSwitching': True,
            'LSApplicationCategoryType': 'public.app-category.utilities',
            'NSHumanReadableCopyright': self.app_copyright,

            # Document types
            'CFBundleDocumentTypes': [
                {
                    'CFBundleTypeRole': 'Viewer',
                    'CFBundleTypeName': 'Folder',
                    'LSHandlerRank': 'Alternate',
                    'LSItemContentTypes': ['public.folder']
                }
            ],

            # URL schemes (if needed)
            'CFBundleURLTypes': [
                {
                    'CFBundleURLName': self.app_identifier,
                    'CFBundleURLSchemes': ['laxyfile']
                }
            ]
        }

        # Add icon if available
        icon_file = self.project_root / 'assets' / 'icon.icns'
        if icon_file.exists():
            info_plist['CFBundleIconFile'] = 'icon.icns'

        plist_file = contents_dir / 'Info.plist'
        with open(plist_file, 'wb') as f:
            plistlib.dump(info_plist, f)

        print(f"Created Info.plist: {plist_file}")

    def _copy_app_resources(self, resources_dir: Path):
        """Copy application resources"""
        # Copy LaxyFile source
        shutil.copytree(self.build_dir / 'laxyfile', resources_dir / 'laxyfile')

        # Copy additional files
        for file_name in ['README.md', 'LICENSE']:
            source_file = self.build_dir / file_name
            if source_file.exists():
                shutil.copy2(source_file, resources_dir / file_name)

        # Copy icon if available
        icon_file = self.project_root / 'assets' / 'icon.icns'
        if icon_file.exists():
            shutil.copy2(icon_file, resources_dir / 'icon.icns')

        print(f"Copied resources to: {resources_dir}")

    def _create_executable_script(self, macos_dir: Path):
        """Create executable script"""
        executable_script = macos_dir / self.app_name.lower()

        script_content = f'''#!/bin/bash

# Get the directory containing this script
DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" && pwd )"
RESOURCES_DIR="$DIR/../Resources"

# Set up environment
export PYTHONPATH="$RESOURCES_DIR:$PYTHONPATH"
export LAXYFILE_BUNDLE=1

# Change to resources directory
cd "$RESOURCES_DIR"

# Run LaxyFile
exec {shutil.which('python3') or 'python3'} -m laxyfile "$@"
'''

        executable_script.write_text(script_content)
        executable_script.chmod(0o755)

        print(f"Created executable: {executable_script}")

    def _copy_python_dependencies(self, resources_dir: Path):
        """Copy Python dependencies (optional)"""
        # This would copy Python dependencies if creating a standalone bundle
        # For now, we assume Python is installed on the system

        # Create a requirements file for easy installation
        requirements_content = '''# LaxyFile dependencies
rich>=13.0.0
click>=8.0.0
pyyaml>=6.0
watchdog>=3.0.0
python-magic>=0.4.27
pillow>=9.0.0
pygments>=2.14.0
'''

        requirements_file = resources_dir / 'requirements.txt'
        requirements_file.write_text(requirements_content)

        # Create installation script
        install_script = resources_dir / 'install_dependencies.sh'
        install_content = '''#!/bin/bash
echo "Installing LaxyFile dependencies..."
pip3 install -r requirements.txt
echo "Dependencies installed successfully!"
'''
        install_script.write_text(install_content)
        install_script.chmod(0o755)

    def create_dmg(self, app_bundle_path: Path):
        """Create DMG installer"""
        print("Creating DMG installer...")

        dmg_name = f"{self.app_name}-{self.app_version}"
        dmg_path = self.dist_dir / f"{dmg_name}.dmg"

        # Remove existing DMG
        if dmg_path.exists():
            dmg_path.unlink()

        # Create temporary DMG directory
        dmg_temp_dir = self.build_dir / 'dmg_temp'
        if dmg_temp_dir.exists():
            shutil.rmtree(dmg_temp_dir)
        dmg_temp_dir.mkdir()

        # Copy app bundle to temp directory
        shutil.copytree(app_bundle_path, dmg_temp_dir / f"{self.app_name}.app")

        # Create Applications symlink
        applications_link = dmg_temp_dir / 'Applications'
        applications_link.symlink_to('/Applications')

        # Copy additional files
        readme_content = f'''# {self.app_name} {self.app_version}

{self.app_description}

## Installation

1. Drag {self.app_name}.app to the Applications folder
2. Open Terminal and run the dependency installer:
   ```
   /Applications/{self.app_name}.app/Contents/Resources/install_dependencies.sh
   ```
3. Launch {self.app_name} from Applications or Spotlight

## Requirements

- macOS 10.12 or later
- Python 3.8 or later
- Xcode Command Line Tools (for some dependencies)

## Support

For support and documentation, visit: https://github.com/user/laxyfile
'''

        readme_file = dmg_temp_dir / 'README.txt'
        readme_file.write_text(readme_content)

        # Create DMG using hdiutil
        try:
            subprocess.run([
                'hdiutil', 'create',
                '-volname', dmg_name,
                '-srcfolder', str(dmg_temp_dir),
                '-ov',
                '-format', 'UDZO',
                str(dmg_path           ], check=True)

            print(f"DMG created: {dmg_path}")
            return dmg_path

        except subprocess.CalledProcessError as e:
            print(f"Failed to create DMG: {e}")
            return None

        finally:
            # Clean up temp directory
            if dmg_temp_dir.exists():
                shutil.rmtree(dmg_temp_dir)

    def create_homebrew_formula(self):
        """Create Homebrew formula"""
        print("Creating Homebrew formula...")

        formula_dir = self.dist_dir / 'homebrew'
        formula_dir.mkdir(exist_ok=True)

        formula_content = f'''class Laxyfile < Formula
  desc "{self.app_description}"
  homepage "https://github.com/user/laxyfile"
  url "https://github.com/user/laxyfile/archive/v{self.app_version}.tar.gz"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"  # Update with actual SHA256
  license "MIT"

  depends_on "python@3.11"

  def install
    # Install Python dependencies
    system Formula["python@3.11"].opt_bin/"pip3", "install", "-r", "requirements.txt", "--prefix=\#{prefix}"

    # Install LaxyFile
    libexec.install Dir["*"]

    # Create wrapper script
    (bin/"laxyfile").write <<~EOS
      #!/bin/bash
      export PYTHONPATH="\#{libexec}:\#{Formula["python@3.11"].opt_lib}/python3.11/site-packages:$PYTHONPATH"
      cd "\#{libexec}"
      exec "\#{Formula["python@3.11"].opt_bin}/python3" -m laxyfile "$@"
    EOS
  end

  test do
    system bin/"laxyfile", "--version"
  end
end
'''

        formula_file = formula_dir / 'laxyfile.rb'
        formula_file.write_text(formula_content)

        print(f"Homebrew formula created: {formula_file}")
        print("To use:")
        print(f"  brew install {formula_file}")

        return formula_file

    def build_all(self):
        """Build all macOS packages"""
        print(f"Building macOS packages for {self.app_name} {self.app_version}")
        print()

        # Prepare source
        self.prepare_source()

        packages = []

        # Create app bundle
        try:
            app_bundle = self.create_app_bundle()
            packages.append(('App Bundle', app_bundle))
        except Exception as e:
            print(f"App bundle creation failed: {e}")
            return packages

        # Create DMG
        try:
            dmg_file = self.create_dmg(app_bundle)
            if dmg_file:
                packages.append(('DMG Installer', dmg_file))
        except Exception as e:
            print(f"DMG creation failed: {e}")

        # Create Homebrew formula
        try:
            formula_file = self.create_homebrew_formula()
            packages.append(('Homebrew Formula', formula_file))
        except Exception as e:
            print(f"Homebrew formula creation failed: {e}")

        print()
        print("macOS package build complete!")
        print("Created packages:")
        for package_type, package_file in packages:
            print(f"  {package_type}: {package_file}")

        return packages


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Build macOS packages for LaxyFile')
    parser.add_argument('--app-only', action='store_true', help='Build app bundle only')
    parser.add_argument('--dmg-only', action='store_true', help='Build DMG only')
    parser.add_argument('--homebrew-only', action='store_true', help='Create Homebrew formula only')

    args = parser.parse_args()

    builder = MacOSAppBuilder()

    if args.app_only:
        builder.prepare_source()
        builder.create_app_bundle()
    elif args.dmg_only:
        builder.prepare_source()
        app_bundle = builder.create_app_bundle()
        builder.create_dmg(app_bundle)
    elif args.homebrew_only:
        builder.create_homebrew_formula()
    else:
        builder.build_all()


if __name__ == '__main__':
    main()