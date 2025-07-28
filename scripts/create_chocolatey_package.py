#!/usr/bin/env python3
"""
Chocolatey Package Generator

Creates and updates Chocolatey package for LaxyFile
"""

import os
import sys
from pathlib import Path
import argparse
import datetime


def create_nuspec_file(version: str) -> str:
    """Create Chocolatey nuspec file content"""

    current_year = datetime.datetime.now().year

    nuspec_content = f'''<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://schemas.microsoft.com/packaging/2015/06/nuspec.xsd">
  <metadata>
    <id>laxyfile</id>
    <version>{version}</version>
    <packageSourceUrl>https://github.com/swadhinbiswas/laxyfile</packageSourceUrl>
    <owners>LaxyFile Team</owners>
    <title>LaxyFile - Advanced Terminal File Manager</title>
    <authors>LaxyFile Team</authors>
    <projectUrl>https://github.com/swadhinbiswas/laxyfile</projectUrl>
    <iconUrl>https://raw.githubusercontent.com/swadhinbiswas/laxyfile/main/docs/assets/icon.png</iconUrl>
    <copyright>{current_year} LaxyFile Team</copyright>
    <licenseUrl>https://github.com/swadhinbiswas/laxyfile/blob/main/LICENSE</licenseUrl>
    <requireLicenseAcceptance>false</requireLicenseAcceptance>
    <projectSourceUrl>https://github.com/swadhinbiswas/laxyfile</projectSourceUrl>
    <docsUrl>https://github.com/swadhinbiswas/laxyfile#readme</docsUrl>
    <bugTrackerUrl>https://github.com/swadhinbiswas/laxyfile/issues</bugTrackerUrl>
    <tags>file-manager terminal cli python ai superfile</tags>
    <summary>Beautiful, AI-powered terminal file manager inspired by Superfile</summary>
    <description><![CDATA[
LaxyFile is an advanced terminal file manager that combines the elegant interface of Superfile with powerful AI capabilities.

## Features

- **Beautiful Interface**: Dual-pane layout with modern terminal UI
- **AI Assistant**: Intelligent file analysis, organization, and security auditing
- **Media Support**: Image preview, video analysis, and metadata extraction
- **File Operations**: Copy, move, delete, batch operations with progress tracking
- **Cross-Platform**: Native support for Windows, macOS, and Linux
- **Themes**: 5 beautiful built-in themes with customization options
- **Performance**: Optimized for large directories and file collections

## Requirements

- Python 3.8 or higher
- Modern terminal with color support
- 256MB+ RAM
- 50MB+ free disk space

## AI Setup

1. Get a free API key from OpenRouter (https://openrouter.ai/)
2. Set environment variable: `$env:OPENROUTER_API_KEY="your-key"`
3. Launch LaxyFile and enjoy AI features!

## Usage

After installation, simply run `laxyfile` in your terminal to start the application.

For more information, visit: https://github.com/swadhinbiswas/laxyfile
]]></description>
    <releaseNotes>https://github.com/swadhinbiswas/laxyfile/releases/tag/v{version}</releaseNotes>
    <dependencies>
      <dependency id="python3" version="3.8.0" />
    </dependencies>
  </metadata>
  <files>
    <file src="tools\\**" target="tools" />
  </files>
</package>
'''

    return nuspec_content


def create_install_script(version: str) -> str:
    """Create Chocolatey install script"""

    install_script = f'''$ErrorActionPreference = 'Stop'

$packageName = 'laxyfile'
$version = '{version}'

Write-Host "Installing LaxyFile v$version..." -ForegroundColor Green

# Check for Python
$pythonCmd = $null
$pythonPaths = @("python", "python3", "py")

foreach ($cmd in $pythonPaths) {{
    try {{
        $result = & $cmd --version 2>$null
        if ($LASTEXITCODE -eq 0 -and $result -match "Python 3\.([8-9]|1[0-9])") {{
            $pythonCmd = $cmd
            Write-Host "Found Python: $result" -ForegroundColor Green
            break
        }}
    }} catch {{
        # Command not found, continue
    }}
}}

if (-not $pythonCmd) {{
    throw @"
Python 3.8+ is required but not found in PATH.

Please install Python from:
- Microsoft Store: https://apps.microsoft.com/store/detail/python-311/9NRWMJP3717K
- Python.org: https://www.python.org/downloads/windows/
- Chocolatey: choco install python

After installation, restart your terminal and try again.
"@
}}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
& $pythonCmd -m pip install --upgrade pip

# Install LaxyFile
Write-Host "Installing LaxyFile from PyPI..." -ForegroundColor Yellow
$installResult = & $pythonCmd -m pip install "laxyfile==$version" 2>&1

if ($LASTEXITCODE -ne 0) {{
    Write-Host "Failed to install from PyPI, trying latest version..." -ForegroundColor Yellow
    $installResult = & $pythonCmd -m pip install laxyfile 2>&1

    if ($LASTEXITCODE -ne 0) {{
        throw "Failed to install LaxyFile: $installResult"
    }}
}}

# Verify installation
Write-Host "Verifying installation..." -ForegroundColor Yellow
$verifyResult = & $pythonCmd -c "import laxyfile; print('LaxyFile installed successfully!')" 2>&1

if ($LASTEXITCODE -ne 0) {{
    throw "Installation verification failed: $verifyResult"
}}

# Create launcher script in a location that's likely to be in PATH
$launcherDir = "$env:LOCALAPPDATA\\Microsoft\\WindowsApps"
$launcherPath = "$launcherDir\\laxyfile.cmd"

if (Test-Path $launcherDir) {{
    $launcherContent = @"
@echo off
$pythonCmd -m laxyfile %*
"@

    try {{
        Set-Content -Path $launcherPath -Value $launcherContent -Encoding ASCII
        Write-Host "Created launcher: $launcherPath" -ForegroundColor Green
    }} catch {{
        Write-Host "Could not create launcher in $launcherDir" -ForegroundColor Yellow
    }}
}}

Write-Host ""
Write-Host "🎉 LaxyFile v$version installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Usage:" -ForegroundColor Cyan
Write-Host "  laxyfile          # Start LaxyFile"
Write-Host "  laxyfile --help   # Show help"
Write-Host ""
Write-Host "🤖 AI Setup (Optional):" -ForegroundColor Cyan
Write-Host "  1. Get free API key from https://openrouter.ai/"
Write-Host "  2. Set environment variable:"
Write-Host "     `$env:OPENROUTER_API_KEY=`"your-key`""
Write-Host "  3. Restart terminal and enjoy AI features!"
Write-Host ""
Write-Host "📚 Documentation: https://github.com/swadhinbiswas/laxyfile#readme" -ForegroundColor Cyan
Write-Host "🐛 Issues: https://github.com/swadhinbiswas/laxyfile/issues" -ForegroundColor Cyan
'''

    return install_script


def create_uninstall_script() -> str:
    """Create Chocolatey uninstall script"""

    uninstall_script = '''$ErrorActionPreference = 'Stop'

$packageName = 'laxyfile'

Write-Host "Uninstalling LaxyFile..." -ForegroundColor Yellow

# Find Python command
$pythonCmd = $null
$pythonPaths = @("python", "python3", "py")

foreach ($cmd in $pythonPaths) {
    try {
        $result = & $cmd --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = $cmd
            break
        }
    } catch {
        # Command not found, continue
    }
}

if ($pythonCmd) {
    # Uninstall LaxyFile
    Write-Host "Removing LaxyFile package..." -ForegroundColor Yellow
    & $pythonCmd -m pip uninstall laxyfile -y 2>$null

    if ($LASTEXITCODE -eq 0) {
        Write-Host "LaxyFile package removed successfully" -ForegroundColor Green
    } else {
        Write-Host "LaxyFile package was not found or already removed" -ForegroundColor Yellow
    }
} else {
    Write-Host "Python not found, skipping package removal" -ForegroundColor Yellow
}

# Remove launcher script
$launcherPath = "$env:LOCALAPPDATA\\Microsoft\\WindowsApps\\laxyfile.cmd"
if (Test-Path $launcherPath) {
    try {
        Remove-Item $launcherPath -Force
        Write-Host "Removed launcher: $launcherPath" -ForegroundColor Green
    } catch {
        Write-Host "Could not remove launcher: $launcherPath" -ForegroundColor Yellow
    }
}

Write-Host "LaxyFile uninstalled successfully!" -ForegroundColor Green
'''

    return uninstall_script


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Create Chocolatey package for LaxyFile")
    parser.add_argument("--version", required=True, help="Version to create package for")
    parser.add_argument("--output-dir", help="Output directory (default: packaging/chocolatey)")

    args = parser.parse_args()

    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        project_root = Path(__file__).parent.parent
        output_dir = project_root / "packaging" / "chocolatey"

    # Create output directories
    output_dir.mkdir(parents=True, exist_ok=True)
    tools_dir = output_dir / "tools"
    tools_dir.mkdir(exist_ok=True)

    print(f"🍫 Creating Chocolatey package for LaxyFile v{args.version}")

    # Create nuspec file
    nuspec_content = create_nuspec_file(args.version)
    nuspec_path = output_dir / "laxyfile.nuspec"
    nuspec_path.write_text(nuspec_content, encoding='utf-8')
    print(f"✅ Created nuspec: {nuspec_path}")

    # Create install script
    install_content = create_install_script(args.version)
    install_path = tools_dir / "chocolateyinstall.ps1"
    install_path.write_text(install_content, encoding='utf-8')
    print(f"✅ Created install script: {install_path}")

    # Create uninstall script
    uninstall_content = create_uninstall_script()
    uninstall_path = tools_dir / "chocolateyuninstall.ps1"
    uninstall_path.write_text(uninstall_content, encoding='utf-8')
    print(f"✅ Created uninstall script: {uninstall_path}")

    print()
    print("📋 Next steps:")
    print("1. Test the package locally:")
    print(f"   choco pack {nuspec_path}")
    print(f"   choco install laxyfile -s . -f")
    print("2. Submit to Chocolatey Community Repository:")
    print("   https://docs.chocolatey.org/en-us/community-repository/moderation/")
    print("3. Or host in your own repository:")
    print("   https://docs.chocolatey.org/en-us/guides/organizations/organizational-deployment-guide")

    return 0


if __name__ == "__main__":
    sys.exit(main())