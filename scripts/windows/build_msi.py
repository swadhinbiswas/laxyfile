#!/usr/bin/env python3
"""
Windows MSI Builder for LaxyFile

This script creates a Windows MSI installer package using cx_Freeze or similar tools.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from cx_Freeze import setup, Executable
    CX_FREEZE_AVAILABLE = True
except ImportError:
    CX_FREEZE_AVAILABLE = False
    print("WARNING: cx_Freeze not available. Install with: pip install cx_Freeze")


class WindowsMSIBuilder:
    """Windows MSI package builder"""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.build_dir = self.project_root / 'build' / 'windows'
        self.dist_dir = self.project_root / 'dist' / 'windows'

        # Package information
        self.app_name = "LaxyFile"
        self.app_version = "1.0.0"
        self.app_description = "Advanced terminal file manager with AI capabilities"
        self.app_author = "LaxyFile Team"
        self.app_url = "https://github.com/user/laxyfile"

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

        # Create main executable script
        main_script = self.build_dir / 'laxyfile_main.py'
        main_content = '''#!/usr/bin/env python3
import sys
from pathlib import Path

# Add laxyfile to path
sys.path.insert(0, str(Path(__file__).parent / 'laxyfile'))

from laxyfile.main import main

if __name__ == '__main__':
    main()
'''
        main_script.write_text(main_content)

        print(f"Source prepared in: {self.build_dir}")

    def create_cx_freeze_setup(self):
        """Create cx_Freeze setup configuration"""
        if not CX_FREEZE_AVAILABLE:
        raise Exception("cx_Freeze is required for MSI building")

        print("Creating cx_Freeze setup...")

        # Build options
        build_exe_options = {
            "packages": [
                "laxyfile",
                "rich",
                "click",
                "yaml",
                "watchdog",
                "magic",
                "PIL",
                "pygments"
            ],
            "excludes": [
                "tkinter",
                "unittest",
                "test",
                "distutils"
            ],
            "include_files": [
                (str(self.build_dir / 'laxyfile'), 'laxyfile'),
                (str(self.build_dir / 'README.md'), 'README.md'),
                (str(self.build_dir / 'LICENSE'), 'LICENSE')
            ],
            "build_exe": str(self.build_dir / 'exe'),
            "optimize": 2
        }

        # MSI options
        bdist_msi_options = {
            "upgrade_code": "{12345678-1234-1234-1234-123456789012}",
            "add_to_path": True,
            "initial_target_dir": f"[ProgramFilesFolder]\\\\{self.app_name}",
            "install_icon": str(self.project_root / "assets" / "icon.ico") if (self.project_root / "assets" / "icon.ico").exists() else None
        }

        # Executable configuration
        executables = [
            Executable(
                str(self.build_dir / 'laxyfile_main.py'),
                base="Console",
                target_name="laxyfile.exe",
                icon=str(self.project_root / "assets" / "icon.ico") if (self.project_root / "assets" / "icon.ico").exists() else None
            )
        ]

        # Create setup script
        setup_script = self.build_dir / 'setup_cx_freeze.py'
        setup_content = f'''
import sys
from cx_Freeze import setup, Executable

build_exe_options = {build_exe_options}
bdist_msi_options = {bdist_msi_options}

executables = [
    Executable(
        "laxyfile_main.py",
        base="Console",
        target_name="laxyfile.exe"
    )
]

setup(
    name="{self.app_name}",
    version="{self.app_version}",
    description="{self.app_description}",
    author="{self.app_author}",
    url="{self.app_url}",
    options={{
        "build_exe": build_exe_options,
        "bdist_msi": bdist_msi_options
    }},
    executables=executables
)
'''
        setup_script.write_text(setup_content)

        return setup_script

    def build_msi(self):
        """Build MSI package"""
        print("Building MSI package...")

        setup_script = self.create_cx_freeze_setup()

        # Change to build directory
        original_cwd = os.getcwd()
        os.chdir(self.build_dir)

        try:
            # Run cx_Freeze
            subprocess.run([
                sys.executable,
                str(setup_script),
                "bdist_msi"
            ], check=True)

            # Move MSI to dist directory
            msi_files = list((self.build_dir / 'dist').glob('*.msi'))
            if msi_files:
                msi_file = msi_files[0]
                target_msi = self.dist_dir / f"{self.app_name}-{self.app_version}-win64.msi"
                shutil.move(str(msi_file), str(target_msi))
                print(f"MSI created: {target_msi}")
                return target_msi
            else:
                raise Exception("MSI file not found after build")

        finally:
            os.chdir(original_cwd)

    def create_nsis_installer(self):
        """Create NSIS installer script as alternative"""
        print("Creating NSIS installer script...")

        nsis_script = self.build_dir / 'laxyfile_installer.nsi'
        nsis_content = f'''
; LaxyFile NSIS Installer Script

!define APPNAME "{self.app_name}"
!define APPVERSION "{self.app_version}"
!define APPNAMEANDVERSION "${{APPNAME}} ${{APPVERSION}}"

; Main Install settings
Name "${{APPNAMEANDVERSION}}"
InstallDir "$PROGRAMFILES\\\\${{APPNAME}}"
InstallDirRegKey HKLM "Software\\\\${{APPNAME}}" ""
OutFile "{self.dist_dir}\\\\{self.app_name}-{self.app_version}-setup.exe"

; Use compression
SetCompressor LZMA

; Modern interface settings
!include "MUI2.nsh"

!define MUI_ABORTWARNING
!define MUI_ICON "${{NSISDIR}}\\\\Contrib\\\\Graphics\\\\Icons\\\\modern-install.ico"
!define MUI_UNICON "${{NSISDIR}}\\\\Contrib\\\\Graphics\\\\Icons\\\\modern-uninstall.ico"

; Interface pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

; Set languages (first is default language)
!insertmacro MUI_LANGUAGE "English"

; Install section
Section "Main Application" SecMain
    SetOutPath "$INSTDIR"

    ; Copy files
    File /r "laxyfile\\\\*"
    File "laxyfile_main.py"
    File "README.md"
    File "LICENSE"

    ; Create executable wrapper
    FileOpen $0 "$INSTDIR\\\\laxyfile.bat" w
    FileWrite $0 "@echo off$\\r$\\n"
    FileWrite $0 "cd /d \\"$INSTDIR\\"$\\r$\\n"
    FileWrite $0 "python laxyfile_main.py %*$\\r$\\n"
    FileClose $0

    ; Create uninstaller
    WriteUninstaller "$INSTDIR\\\\Uninstall.exe"

    ; Registry entries
    WriteRegStr HKLM "Software\\\\${{APPNAME}}" "" "$INSTDIR"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "DisplayName" "${{APPNAMEANDVERSION}}"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "UninstallString" "$INSTDIR\\\\Uninstall.exe"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "DisplayVersion" "${{APPVERSION}}"
    WriteRegStr HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}" "Publisher" "{self.app_author}"

    ; Start menu shortcuts
    CreateDirectory "$SMPROGRAMS\\\\${{APPNAME}}"
    CreateShortCut "$SMPROGRAMS\\\\${{APPNAME}}\\\\${{APPNAME}}.lnk" "$INSTDIR\\\\laxyfile.bat"
    CreateShortCut "$SMPROGRAMS\\\\${{APPNAME}}\\\\Uninstall.lnk" "$INSTDIR\\\\Uninstall.exe"

SectionEnd

; Uninstall section
Section "Uninstall"
    ; Remove files
    RMDir /r "$INSTDIR"

    ; Remove shortcuts
    RMDir /r "$SMPROGRAMS\\\\${{APPNAME}}"

    ; Remove registry entries
    DeleteRegKey HKLM "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Uninstall\\\\${{APPNAME}}"
    DeleteRegKey HKLM "Software\\\\${{APPNAME}}"

SectionEnd
'''
        nsis_script.write_text(nsis_content)

        print(f"NSIS script created: {nsis_script}")
        print("To build installer, run: makensis laxyfile_installer.nsi")

        return nsis_script

    def build_portable_zip(self):
        """Create portable ZIP package"""
        print("Creating portable ZIP package...")

        # Create portable directory structure
        portable_dir = self.build_dir / 'portable'
        if portable_dir.exists():
            shutil.rmtree(portable_dir)

        portable_dir.mkdir()

        # Copy files
        shutil.copytree(self.build_dir / 'laxyfile', portable_dir / 'laxyfile')
        shutil.copy2(self.build_dir / 'laxyfile_main.py', portable_dir / 'laxyfile_main.py')

        # Copy additional files
        for file_name in ['README.md', 'LICENSE']:
            source_file = self.build_dir / file_name
            if source_file.exists():
                shutil.copy2(source_file, portable_dir / file_name)

        # Create launcher batch file
        launcher_bat = portable_dir / 'laxyfile.bat'
        launcher_content = '''@echo off
cd /d "%~dp0"
python laxyfile_main.py %*
'''
        launcher_bat.write_text(launcher_content)

        # Create ZIP
        zip_file = self.dist_dir / f"{self.app_name}-{self.app_version}-portable.zip"
        shutil.make_archive(
            str(zip_file.with_suffix('')),
            'zip',
            str(portable_dir.parent),
            str(portable_dir.name)
        )

        print(f"Portable ZIP created: {zip_file}")
        return zip_file

    def build_all(self):
        """Build all Windows packages"""
        print(f"Building Windows packages for {self.app_name} {self.app_version}")
        print()

        # Prepare source
        self.prepare_source()

        packages = []

        # Build MSI (if cx_Freeze available)
        if CX_FREEZE_AVAILABLE:
            try:
                msi_file = self.build_msi()
                packages.append(('MSI', msi_file))
            except Exception as e:
                print(f"MSI build failed: {e}")

        # Create NSIS script
        try:
            nsis_script = self.create_nsis_installer()
            packages.append(('NSIS Script', nsis_script))
        except Exception as e:
            print(f"NSIS script creation failed: {e}")

        # Build portable ZIP
        try:
            zip_file = self.build_portable_zip()
            packages.append(('Portable ZIP', zip_file))
        except Exception as e:
            print(f"Portable ZIP build failed: {e}")

        print()
        print("Windows package build complete!")
        print("Created packages:")
        for package_type, package_file in packages:
            print(f"  {package_type}: {package_file}")

        return packages


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Build Windows packages for LaxyFile')
    parser.add_argument('--msi-only', action='store_true', help='Build MSI only')
    parser.add_argument('--portable-only', action='store_true', help='Build portable ZIP only')
    parser.add_argument('--nsis-only', action='store_true', help='Create NSIS script only')

    args = parser.parse_args()

    builder = WindowsMSIBuilder()

    if args.msi_only:
        builder.prepare_source()
        if CX_FREEZE_AVAILABLE:
            builder.build_msi()
        else:
            print("ERROR: cx_Freeze not available for MSI building")
            sys.exit(1)
    elif args.portable_only:
        builder.prepare_source()
        builder.build_portable_zip()
    elif args.nsis_only:
        builder.prepare_source()
        builder.create_nsis_installer()
    else:
        builder.build_all()


if __name__ == '__main__':
    main()