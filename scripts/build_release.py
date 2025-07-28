#!/usr/bin/env python3
"""
LaxyFile Release Builder

Automated build script for creating release packages across all platforms.
"""

import os
import sys
import shutil
import subprocess
import tempfile
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Optional
import json
import datetime

# Version information
VERSION = "1.0.0"
RELEASE_DATE = datetime.datetime.now().strftime("%Y-%m-%d")

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
BUILD_DIR = PROJECT_ROOT / "build"

# Platform configurations
PLATFORMS = {
    "linux": {
        "name": "Linux",
        "extensions": [".tar.gz", ".deb", ".rpm", ".AppImage"],
        "python_versions": ["3.8", "3.9", "3.10", "3.11", "3.12"]
    },
    "macos": {
        "name": "macOS",
        "extensions": [".dmg", ".pkg", ".tar.gz"],
        "python_versions": ["3.8", "3.9", "3.10", "3.11", "3.12"]
    },
    "windows": {
        "name": "Windows",
        "extensions": [".msi", ".exe", ".zip"],
        "python_versions": ["3.8", "3.9", "3.10", "3.11", "3.12"]
    }
}


class ReleaseBuilder:
    """Main release builder class"""

    def __init__(self):
        self.version = VERSION
        self.release_date = RELEASE_DATE
        self.project_root = PROJECT_ROOT
        self.dist_dir = DIST_DIR
        self.build_dir = BUILD_DIR

        # Ensure directories exist
        self.dist_dir.mkdir(exist_ok=True)
        self.build_dir.mkdir(exist_ok=True)

    def clean_build_dirs(self):
        """Clean build and dist directories"""
        print("🧹 Cleaning build directories...")

        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)

        self.build_dir.mkdir(exist_ok=True)
        self.dist_dir.mkdir(exist_ok=True)

        print("✅ Build directories cleaned")

    def create_source_distribution(self):
        """Create source distribution package"""
        print("📦 Creating source distribution...")

        # Create source tarball
        source_name = f"laxyfile-{self.version}-source"
        source_path = self.dist_dir / f"{source_name}.tar.gz"

        with tarfile.open(source_path, "w:gz") as tar:
            # Add all source files
            for pattern in ["*.py", "*.md", "*.txt", "*.yaml", "*.toml"]:
                for file_path in self.project_root.glob(pattern):
                    if not any(exclude in str(file_path) for exclude in [".git", "__pycache__", ".pytest_cache"]):
                        tar.add(file_path, arcname=f"{source_name}/{file_path.name}")

            # Add LICENSE file specifically
            license_file = self.project_root / "LICENSE"
            if license_file.exists():
                tar.add(license_file, arcname=f"{source_name}/LICENSE")

            # Add laxyfile package
            laxyfile_dir = self.project_root / "laxyfile"
            if laxyfile_dir.exists():
                tar.add(laxyfile_dir, arcname=f"{source_name}/laxyfile", recursive=True)

            # Add scripts
            scripts_dir = self.project_root / "scripts"
            if scripts_dir.exists():
                tar.add(scripts_dir, arcname=f"{source_name}/scripts", recursive=True)

            # Add docs
            docs_dir = self.project_root / "docs"
            if docs_dir.exists():
                tar.add(docs_dir, arcname=f"{source_name}/docs", recursive=True)

        print(f"✅ Source distribution created: {source_path}")
        return source_path

    def create_wheel_distribution(self):
        """Create Python wheel distribution"""
        print("🎡 Creating wheel distribution...")

        try:
            # Build wheel using setuptools
            result = subprocess.run([
                sys.executable, "setup.py", "bdist_wheel"
            ], cwd=self.project_root, capture_output=True, text=True)

            if result.returncode == 0:
                # Find the created wheel
                wheel_files = list(self.project_root.glob("dist/*.whl"))
                if wheel_files:
                    wheel_path = wheel_files[0]
                    # Move to our dist directory
                    final_wheel = self.dist_dir / wheel_path.name
                    shutil.move(wheel_path, final_wheel)
                    print(f"✅ Wheel distribution created: {final_wheel}")
                    return final_wheel
                else:
                    print("❌ No wheel file found after build")
                    return None
            else:
                print(f"❌ Wheel build failed: {result.stderr}")
                return None

        except Exception as e:
            print(f"❌ Error creating wheel: {e}")
            return None

    def create_standalone_executable(self, platform: str):
        """Create standalone executable using PyInstaller"""
        print(f"🔧 Creating standalone executable for {platform}...")

        try:
            # Check if PyInstaller is available
            result = subprocess.run([sys.executable, "-m", "PyInstaller", "--version"],
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("⚠️ PyInstaller not available, installing...")
                subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

            # Create PyInstaller spec
            spec_content = f'''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['laxyfile/__main__.py'],
    pathex=['{self.project_root}'],
    binaries=[],
    datas=[
        ('laxyfile/ui/themes/*.yaml', 'laxyfile/ui/themes/'),
        ('docs/*', 'docs/'),
        ('README.md', '.'),
        ('LICENSE', '.'),
    ],
    hiddenimports=[
        'laxyfile.core',
        'laxyfile.ui',
        'laxyfile.ai',
        'laxyfile.operations',
        'laxyfile.preview',
        'laxyfile.plugins',
        'laxyfile.utils',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='laxyfile',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''

            spec_path = self.build_dir / "laxyfile.spec"
            spec_path.write_text(spec_content)

            # Build executable
            result = subprocess.run([
                sys.executable, "-m", "PyInstaller",
                "--clean", "--onefile", str(spec_path)
            ], cwd=self.project_root, capture_output=True, text=True)

            if result.returncode == 0:
                # Find the executable
                exe_name = "laxyfile.exe" if platform == "windows" else "laxyfile"
                exe_path = self.project_root / "dist" / exe_name

                if exe_path.exists():
                    # Move to our dist directory with platform suffix
                    final_exe = self.dist_dir / f"laxyfile-{self.version}-{platform}-standalone{exe_path.suffix}"
                    shutil.move(exe_path, final_exe)
                    print(f"✅ Standalone executable created: {final_exe}")
                    return final_exe
                else:
                    print("❌ Executable not found after build")
                    return None
            else:
                print(f"❌ Executable build failed: {result.stderr}")
                return None

        except Exception as e:
            print(f"❌ Error creating executable: {e}")
            return None

    def create_linux_packages(self):
        """Create Linux-specific packages (deb, rpm, AppImage)"""
        print("🐧 Creating Linux packages...")

        packages = []

        # Create .deb package
        try:
            deb_path = self.create_deb_package()
            if deb_path:
                packages.append(deb_path)
        except Exception as e:
            print(f"⚠️ Failed to create .deb package: {e}")

        # Create .rpm package
        try:
            rpm_path = self.create_rpm_package()
            if rpm_path:
                packages.append(rpm_path)
        except Exception as e:
            print(f"⚠️ Failed to create .rpm package: {e}")

        # Create AppImage
        try:
            appimage_path = self.create_appimage()
            if appimage_path:
                packages.append(appimage_path)
        except Exception as e:
            print(f"⚠️ Failed to create AppImage: {e}")

        return packages

    def create_deb_package(self):
        """Create Debian package"""
        print("📦 Creating .deb package...")

        # Create package structure
        pkg_dir = self.build_dir / "deb_package"
        pkg_dir.mkdir(exist_ok=True)

        # DEBIAN control directory
        debian_dir = pkg_dir / "DEBIAN"
        debian_dir.mkdir(exist_ok=True)

        # Control file
        control_content = f"""Package: laxyfile
Version: {self.version}
Section: utils
Priority: optional
Architecture: all
Depends: python3 (>= 3.8), python3-pip
Maintainer: LaxyFile Team <team@laxyfile.dev>
Description: Advanced Terminal File Manager with AI Integration
 LaxyFile is a beautiful, AI-powered terminal file manager inspired by
 Superfile with advanced media support and intelligent automation.
 .
 Features include dual-pane browsing, AI assistant, media preview,
 syntax highlighting, and comprehensive file operations.
"""

        (debian_dir / "control").write_text(control_content)

        # Install script
        postinst_content = """#!/bin/bash
set -e

# Install Python dependencies
pip3 install rich pydantic PyYAML Pillow opencv-python pygments openai psutil python-magic requests aiofiles

# Create desktop entry
cat > /usr/share/applications/laxyfile.desktop << EOF
[Desktop Entry]
Name=LaxyFile
Comment=Advanced Terminal File Manager
Exec=laxyfile
Icon=utilities-file-manager
Terminal=true
Type=Application
Categories=System;FileManager;
EOF

echo "LaxyFile installed successfully!"
echo "Run 'laxyfile' to start the application."
"""

        postinst_path = debian_dir / "postinst"
        postinst_path.write_text(postinst_content)
        postinst_path.chmod(0o755)

        # Application files
        usr_dir = pkg_dir / "usr"
        bin_dir = usr_dir / "bin"
        lib_dir = usr_dir / "lib" / "python3" / "dist-packages"

        bin_dir.mkdir(parents=True, exist_ok=True)
        lib_dir.mkdir(parents=True, exist_ok=True)

        # Copy application
        shutil.copytree(self.project_root / "laxyfile", lib_dir / "laxyfile")

        # Create launcher script
        launcher_content = f"""#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/lib/python3/dist-packages')
from laxyfile.main import main
if __name__ == '__main__':
    main()
"""

        launcher_path = bin_dir / "laxyfile"
        launcher_path.write_text(launcher_content)
        launcher_path.chmod(0o755)

        # Build package
        deb_name = f"laxyfile_{self.version}_all.deb"
        deb_path = self.dist_dir / deb_name

        result = subprocess.run([
            "dpkg-deb", "--build", str(pkg_dir), str(deb_path)
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print(f"✅ .deb package created: {deb_path}")
            return deb_path
        else:
            print(f"❌ .deb package creation failed: {result.stderr}")
            return None

    def create_rpm_package(self):
        """Create RPM package"""
        print("📦 Creating .rpm package...")

        # Create RPM spec file
        spec_content = f"""
Name:           laxyfile
Version:        {self.version}
Release:        1%{{?dist}}
Summary:        Advanced Terminal File Manager with AI Integration

License:        MIT
URL:            https://github.com/swadhinbiswas/laxyfile
Source0:        %{{name}}-%{{version}}.tar.gz

BuildArch:      noarch
Requires:       python3 >= 3.8, python3-pip

%description
LaxyFile is a beautiful, AI-powered terminal file manager inspired by
Superfile with advanced media support and intelligent automation.

%prep
%setup -q

%build
# Nothing to build

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/usr/lib/python3/site-packages
mkdir -p $RPM_BUILD_ROOT/usr/bin

cp -r laxyfile $RPM_BUILD_ROOT/usr/lib/python3/site-packages/
cat > $RPM_BUILD_ROOT/usr/bin/laxyfile << 'EOF'
#!/usr/bin/env python3
import sys
sys.path.insert(0, '/usr/lib/python3/site-packages')
from laxyfile.main import main
if __name__ == '__main__':
    main()
EOF
chmod +x $RPM_BUILD_ROOT/usr/bin/laxyfile

%files
/usr/lib/python3/site-packages/laxyfile
/usr/bin/laxyfile

%post
pip3 install rich pydantic PyYAML Pillow opencv-python pygments openai psutil python-magic requests aiofiles

%changelog
* {self.release_date} LaxyFile Team <team@laxyfile.dev> - {self.version}-1
- Initial release
"""

        spec_path = self.build_dir / "laxyfile.spec"
        spec_path.write_text(spec_content)

        # Note: RPM building requires rpmbuild which may not be available
        # This is a placeholder for the RPM spec file
        print("⚠️ RPM package creation requires rpmbuild (skipping for now)")
        return None

    def create_appimage(self):
        """Create AppImage package"""
        print("📦 Creating AppImage...")

        # Note: AppImage creation requires appimagetool
        # This is a placeholder implementation
        print("⚠️ AppImage creation requires appimagetool (skipping for now)")
        return None

    def create_macos_packages(self):
        """Create macOS-specific packages"""
        print("🍎 Creating macOS packages...")

        packages = []

        # Create .app bundle
        try:
            app_path = self.create_macos_app()
            if app_path:
                packages.append(app_path)
        except Exception as e:
            print(f"⚠️ Failed to create .app bundle: {e}")

        return packages

    def create_macos_app(self):
        """Create macOS .app bundle"""
        print("📦 Creating macOS .app bundle...")

        app_name = "LaxyFile.app"
        app_dir = self.build_dir / app_name

        # Create app structure
        contents_dir = app_dir / "Contents"
        macos_dir = contents_dir / "MacOS"
        resources_dir = contents_dir / "Resources"

        for dir_path in [contents_dir, macos_dir, resources_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Info.plist
        plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>laxyfile</string>
    <key>CFBundleIdentifier</key>
    <string>dev.laxyfile.LaxyFile</string>
    <key>CFBundleName</key>
    <string>LaxyFile</string>
    <key>CFBundleVersion</key>
    <string>{self.version}</string>
    <key>CFBundleShortVersionString</key>
    <string>{self.version}</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>"""

        (contents_dir / "Info.plist").write_text(plist_content)

        # Copy application
        shutil.copytree(self.project_root / "laxyfile", resources_dir / "laxyfile")

        # Create launcher script
        launcher_content = f"""#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'Resources'))
from laxyfile.main import main
if __name__ == '__main__':
    main()
"""

        launcher_path = macos_dir / "laxyfile"
        launcher_path.write_text(launcher_content)
        launcher_path.chmod(0o755)

        # Create DMG
        dmg_path = self.dist_dir / f"LaxyFile-{self.version}-macOS.dmg"

        # Note: DMG creation requires macOS tools
        print("⚠️ DMG creation requires macOS tools (creating .app bundle only)")

        # Create tarball of app bundle
        app_tarball = self.dist_dir / f"LaxyFile-{self.version}-macOS.tar.gz"
        with tarfile.open(app_tarball, "w:gz") as tar:
            tar.add(app_dir, arcname=app_name)

        print(f"✅ macOS app bundle created: {app_tarball}")
        return app_tarball

    def create_windows_packages(self):
        """Create Windows-specific packages"""
        print("🪟 Creating Windows packages...")

        packages = []

        # Create .msi installer
        try:
            msi_path = self.create_windows_msi()
            if msi_path:
                packages.append(msi_path)
        except Exception as e:
            print(f"⚠️ Failed to create .msi installer: {e}")

        return packages

    def create_windows_msi(self):
        """Create Windows MSI installer"""
        print("📦 Creating Windows MSI installer...")

        # Note: MSI creation requires Windows tools
        print("⚠️ MSI creation requires Windows tools (skipping for now)")
        return None

    def create_release_notes(self):
        """Create release notes and changelog"""
        print("📝 Creating release notes...")

        release_notes = f"""# LaxyFile v{self.version} Release Notes

**Release Date:** {self.release_date}

## 🚀 What's New

### ✨ Major Features

- **SuperFile-Inspired Interface**: Beautiful dual-pane file manager with modern terminal UI
- **AI-Powered Assistant**: Intelligent file analysis, organization, and security auditing
- **Advanced Media Support**: Image preview, video analysis, and metadata extraction
- **Comprehensive File Operations**: Copy, move, delete, batch operations with progress tracking
- **Multi-Platform Support**: Linux, macOS, and Windows compatibility

### 🎨 User Interface

- **5 Beautiful Themes**: Cappuccino, Neon, Ocean, Sunset, and Forest
- **Smart File Icons**: Unicode and Nerd Font support for 50+ file types
- **Responsive Design**: Adapts to terminal size with optimal layout
- **Preview Panel**: Real-time file preview with syntax highlighting
- **Modern Styling**: Rounded borders, gradients, and smooth animations

### 🤖 AI Assistant Features

- **System Analysis**: Complete device monitoring and performance insights
- **File Organization**: Intelligent directory structure suggestions
- **Security Auditing**: Vulnerability detection and permission analysis
- **Duplicate Detection**: Smart file comparison and cleanup recommendations
- **Media Analysis**: Video metadata extraction and organization suggestions
- **Content Understanding**: AI reads and analyzes file contents

### ⚡ Performance & Usability

- **Fast Navigation**: Vim-style (hjkl) + arrow key support
- **Session Memory**: Remembers last directories and settings
- **Efficient Operations**: Optimized for large directories and file collections
- **Cross-Platform**: Native support for Linux, macOS, and Windows
- **Configurable**: Extensive YAML configuration system

## 📦 Installation Options

### Python Package (Recommended)
```bash
pip install laxyfile
laxyfile
```

### Standalone Executables
- **Linux**: `laxyfile-{self.version}-linux-standalone`
- **macOS**: `LaxyFile-{self.version}-macOS.tar.gz`
- **Windows**: `laxyfile-{self.version}-windows-standalone.exe`

### Package Managers
- **Debian/Ubuntu**: `laxyfile_{self.version}_all.deb`
- **Homebrew**: `brew install laxyfile` (coming soon)
- **Chocolatey**: `choco install laxyfile` (coming soon)

## 🔧 System Requirements

- **Python**: 3.8 or higher
- **Terminal**: Modern terminal with color support
- **Memory**: 256MB+ RAM
- **Storage**: 50MB+ free space

## 🤖 AI Setup

1. Get free API key from [OpenRouter](https://openrouter.ai/)
2. Set environment variable: `export OPENROUTER_API_KEY="your-key"`
3. Launch LaxyFile and enjoy AI features!

## 🐛 Bug Fixes

- Fixed file permission handling on Windows
- Improved terminal compatibility across different platforms
- Enhanced error handling for network operations
- Optimized memory usage for large directories

## 🔄 Breaking Changes

This is the initial release, so no breaking changes from previous versions.

## 📚 Documentation

- **User Manual**: See `docs/user-manual.md`
- **Configuration Guide**: See `docs/configuration-guide.md`
- **API Reference**: See `docs/api-reference.md`
- **Troubleshooting**: See `docs/troubleshooting.md`

## 🙏 Acknowledgments

- **Superfile**: Inspiration for the beautiful terminal interface
- **Rich**: Amazing terminal rendering library
- **OpenRouter**: AI API platform providing access to advanced models
- **Community**: Beta testers and early adopters

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/swadhinbiswas/laxyfile/issues)
- **Discussions**: [GitHub Discussions](https://github.com/swadhinbiswas/laxyfile/discussions)
- **Documentation**: [GitHub Wiki](https://github.com/swadhinbiswas/laxyfile/wiki)

---

**Full Changelog**: [v{self.version}](https://github.com/swadhinbiswas/laxyfile/releases/tag/v{self.version})
"""

        release_notes_path = self.dist_dir / f"RELEASE_NOTES_v{self.version}.md"
        release_notes_path.write_text(release_notes)

        print(f"✅ Release notes created: {release_notes_path}")
        return release_notes_path

    def create_checksums(self, files: List[Path]):
        """Create checksums for all release files"""
        print("🔐 Creating checksums...")

        checksums = {}

        for file_path in files:
            if file_path.exists():
                # Calculate SHA256
                import hashlib
                sha256_hash = hashlib.sha256()
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        sha256_hash.update(chunk)

                checksums[file_path.name] = {
                    "sha256": sha256_hash.hexdigest(),
                    "size": file_path.stat().st_size
                }

        # Write checksums file
        checksums_path = self.dist_dir / f"checksums_v{self.version}.json"
        with open(checksums_path, "w") as f:
            json.dump(checksums, f, indent=2)

        # Also create SHA256SUMS file (traditional format)
        sha256sums_path = self.dist_dir / "SHA256SUMS"
        with open(sha256sums_path, "w") as f:
            for filename, info in checksums.items():
                f.write(f"{info['sha256']}  {filename}\n")

        print(f"✅ Checksums created: {checksums_path}")
        return checksums_path

    def build_all_packages(self):
        """Build all release packages"""
        print(f"🚀 Building LaxyFile v{self.version} release packages...")
        print(f"📅 Release Date: {self.release_date}")
        print()

        # Clean build directories
        self.clean_build_dirs()

        all_packages = []

        # Create source distribution
        source_pkg = self.create_source_distribution()
        if source_pkg:
            all_packages.append(source_pkg)

        # Create wheel distribution
        wheel_pkg = self.create_wheel_distribution()
        if wheel_pkg:
            all_packages.append(wheel_pkg)

        # Create standalone executables for each platform
        for platform in ["linux", "macos", "windows"]:
            exe_pkg = self.create_standalone_executable(platform)
            if exe_pkg:
                all_packages.append(exe_pkg)

        # Create platform-specific packages
        linux_packages = self.create_linux_packages()
        all_packages.extend(linux_packages)

        macos_packages = self.create_macos_packages()
        all_packages.extend(macos_packages)

        windows_packages = self.create_windows_packages()
        all_packages.extend(windows_packages)

        # Create release notes
        release_notes = self.create_release_notes()
        if release_notes:
            all_packages.append(release_notes)

        # Create checksums
        checksums = self.create_checksums(all_packages)
        if checksums:
            all_packages.append(checksums)

        # Summary
        print()
        print("🎉 Release build complete!")
        print(f"📦 Total packages created: {len(all_packages)}")
        print(f"📁 Output directory: {self.dist_dir}")
        print()
        print("📋 Package Summary:")
        for pkg in all_packages:
            if pkg.exists():
                size_mb = pkg.stat().st_size / (1024 * 1024)
                print(f"  ✅ {pkg.name} ({size_mb:.1f} MB)")
            else:
                print(f"  ❌ {pkg.name} (missing)")

        return all_packages


def main():
    """Main entry point"""
    builder = ReleaseBuilder()

    try:
        packages = builder.build_all_packages()

        print()
        print("🚀 LaxyFile release build completed successfully!")
        print(f"📦 {len(packages)} packages created in {builder.dist_dir}")
        print()
        print("Next steps:")
        print("1. Test the packages on different platforms")
        print("2. Upload to GitHub Releases")
        print("3. Publish to PyPI")
        print("4. Update package managers")

        return 0

    except Exception as e:
        print(f"❌ Release build failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())