#!/usr/bin/env python3
"""
Deployment Validation Script

Validates that all deployment artifacts are ready and functional
"""

import os
import sys
import subprocess
import requests
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import tempfile
import zipfile
import tarfile


class DeploymentValidator:
    """Validates deployment readiness"""

    def __init__(self, version: str):
        self.version = version
        self.project_root = Path(__file__).parent.parent
        self.dist_dir = self.project_root / "dist"
        self.errors = []
        self.warnings = []

    def log_error(self, message: str):
        """Log an error"""
        self.errors.append(message)
        print(f"❌ {message}")

    def log_warning(self, message: str):
        """Log a warning"""
        self.warnings.append(message)
        print(f"⚠️ {message}")

    def log_success(self, message: str):
        """Log a success"""
        print(f"✅ {message}")

    def validate_version_consistency(self) -> bool:
        """Validate version consistency across files"""
        print("🔍 Validating version consistency...")

        version_files = {
            "laxyfile/__init__.py": r'__version__\s*=\s*["\']([^"\']+)["\']',
            "setup.py": r'version\s*=\s*["\']([^"\']+)["\']',
            "pyproject.toml": r'version\s*=\s*["\']([^"\']+)["\']'
        }

        versions_found = {}

        for file_path, pattern in version_files.items():
            full_path = self.project_root / file_path
            if full_path.exists():
                content = full_path.read_text()
                import re
                match = re.search(pattern, content)
                if match:
                    versions_found[file_path] = match.group(1)
                else:
                    self.log_warning(f"Version not found in {file_path}")
            else:
                self.log_warning(f"File not found: {file_path}")

        # Check consistency
        unique_versions = set(versions_found.values())
        if len(unique_versions) == 1:
            found_version = list(unique_versions)[0]
            if found_version == self.version:
                self.log_success(f"Version consistency validated: {self.version}")
                return True
            else:
                self.log_error(f"Version mismatch: expected {self.version}, found {found_version}")
                return False
        elif len(unique_versions) > 1:
            self.log_error(f"Inconsistent versions found: {versions_found}")
            return False
        else:
            self.log_error("No versions found in any file")
            return False

    def validate_package_files(self) -> bool:
        """Validate that all expected package files exist"""
        print("📦 Validating package files...")

        expected_files = [
            f"laxyfile-{self.version}-source.tar.gz",
            f"laxyfile-{self.version}-py3-none-any.whl",
            f"RELEASE_NOTES_v{self.version}.md",
            f"checksums_v{self.version}.json",
            "SHA256SUMS"
        ]

        optional_files = [
            f"laxyfile-{self.version}-linux-standalone",
            f"LaxyFile-{self.version}-macOS.tar.gz",
            f"laxyfile-{self.version}-windows-standalone.exe",
            f"laxyfile_{self.version}_all.deb"
        ]

        all_valid = True

        # Check required files
        for file_name in expected_files:
            file_path = self.dist_dir / file_name
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                self.log_success(f"Found {file_name} ({size_mb:.1f} MB)")
            else:
                self.log_error(f"Missing required file: {file_name}")
                all_valid = False

        # Check optional files
        for file_name in optional_files:
            file_path = self.dist_dir / file_name
            if file_path.exists():
                size_mb = file_path.stat().st_size / (1024 * 1024)
                self.log_success(f"Found optional {file_name} ({size_mb:.1f} MB)")
            else:
                self.log_warning(f"Optional file not found: {file_name}")

        return all_valid

    def validate_wheel_package(self) -> bool:
        """Validate wheel package structure"""
        print("🎡 Validating wheel package...")

        wheel_path = self.dist_dir / f"laxyfile-{self.version}-py3-none-any.whl"
        if not wheel_path.exists():
            self.log_error("Wheel package not found")
            return False

        try:
            with zipfile.ZipFile(wheel_path, 'r') as wheel:
                files = wheel.namelist()

                # Check for required files
                required_patterns = [
                    "laxyfile/",
                    "laxyfile/__init__.py",
                    "laxyfile/main.py",
                    "laxyfile-*.dist-info/METADATA",
                    "laxyfile-*.dist-info/WHEEL"
                ]

                for pattern in required_patterns:
                    if pattern.endswith('/'):
                        # Directory check
                        if not any(f.startswith(pattern) for f in files):
                            self.log_error(f"Missing directory in wheel: {pattern}")
                            return False
                    elif '*' in pattern:
                        # Pattern check
                        import fnmatch
                        if not any(fnmatch.fnmatch(f, pattern) for f in files):
                            self.log_error(f"Missing file pattern in wheel: {pattern}")
                            return False
                    else:
                        # Exact file check
                        if pattern not in files:
                            self.log_error(f"Missing file in wheel: {pattern}")
                            return False

                self.log_success(f"Wheel package structure validated ({len(files)} files)")
                return True

        except Exception as e:
            self.log_error(f"Error validating wheel: {e}")
            return False

    def validate_source_package(self) -> bool:
        """Validate source package structure"""
        print("📄 Validating source package...")

        source_path = self.dist_dir / f"laxyfile-{self.version}-source.tar.gz"
        if not source_path.exists():
            self.log_error("Source package not found")
            return False

        try:
            with tarfile.open(source_path, 'r:gz') as tar:
                files = tar.getnames()

                # Check for required files
                required_files = [
                    f"laxyfile-{self.version}-source/laxyfile/__init__.py",
                    f"laxyfile-{self.version}-source/laxyfile/main.py",
                    f"laxyfile-{self.version}-source/setup.py",
                    f"laxyfile-{self.version}-source/README.md",
                    f"laxyfile-{self.version}-source/LICENSE"
                ]

                for required_file in required_files:
                    if required_file not in files:
                        self.log_error(f"Missing file in source package: {required_file}")
                        return False

                self.log_success(f"Source package structure validated ({len(files)} files)")
                return True

        except Exception as e:
            self.log_error(f"Error validating source package: {e}")
            return False

    def validate_checksums(self) -> bool:
        """Validate checksums file"""
        print("🔐 Validating checksums...")

        checksums_path = self.dist_dir / f"checksums_v{self.version}.json"
        sha256sums_path = self.dist_dir / "SHA256SUMS"

        if not checksums_path.exists():
            self.log_error("Checksums JSON file not found")
            return False

        if not sha256sums_path.exists():
            self.log_error("SHA256SUMS file not found")
            return False

        try:
            # Validate JSON format
            with open(checksums_path) as f:
                checksums_data = json.load(f)

            # Validate SHA256SUMS format
            sha256sums_content = sha256sums_path.read_text()

            # Check that files mentioned in checksums exist
            for filename in checksums_data.keys():
                file_path = self.dist_dir / filename
                if not file_path.exists():
                    self.log_error(f"File mentioned in checksums but not found: {filename}")
                    return False

            self.log_success(f"Checksums validated for {len(checksums_data)} files")
            return True

        except Exception as e:
            self.log_error(f"Error validating checksums: {e}")
            return False

    def validate_release_notes(self) -> bool:
        """Validate release notes"""
        print("📝 Validating release notes...")

        release_notes_path = self.dist_dir / f"RELEASE_NOTES_v{self.version}.md"
        if not release_notes_path.exists():
            self.log_error("Release notes not found")
            return False

        try:
            content = release_notes_path.read_text()

            # Check for required sections
            required_sections = [
                f"# LaxyFile v{self.version} Release Notes",
                "## 🚀 What's New",
                "## 📦 Installation",
                "## 🔧 System Requirements"
            ]

            for section in required_sections:
                if section not in content:
                    self.log_error(f"Missing section in release notes: {section}")
                    return False

            # Check minimum length
            if len(content) < 1000:
                self.log_warning("Release notes seem quite short")

            self.log_success("Release notes validated")
            return True

        except Exception as e:
            self.log_error(f"Error validating release notes: {e}")
            return False

    def validate_package_manager_configs(self) -> bool:
        """Validate package manager configurations"""
        print("📦 Validating package manager configurations...")

        configs = {
            "packaging/homebrew/laxyfile.rb": "Homebrew formula",
            "packaging/chocolatey/laxyfile.nuspec": "Chocolatey nuspec",
            "packaging/chocolatey/tools/chocolateyinstall.ps1": "Chocolatey install script"
        }

        all_valid = True

        for config_path, description in configs.items():
            full_path = self.project_root / config_path
            if full_path.exists():
                # Check if version is mentioned in the file
                content = full_path.read_text()
                if self.version in content:
                    self.log_success(f"{description} validated")
                else:
                    self.log_warning(f"{description} doesn't contain version {self.version}")
            else:
                self.log_warning(f"{description} not found: {config_path}")
                all_valid = False

        return all_valid

    def validate_ci_config(self) -> bool:
        """Validate CI/CD configuration"""
        print("🔄 Validating CI/CD configuration...")

        ci_files = [
            ".github/workflows/release.yml",
            ".github/workflows/test.yml"
        ]

        all_valid = True

        for ci_file in ci_files:
            full_path = self.project_root / ci_file
            if full_path.exists():
                self.log_success(f"CI config found: {ci_file}")
            else:
                self.log_warning(f"CI config not found: {ci_file}")
                all_valid = False

        return all_valid

    def test_package_installation(self) -> bool:
        """Test package installation in a virtual environment"""
        print("🧪 Testing package installation...")

        wheel_path = self.dist_dir / f"laxyfile-{self.version}-py3-none-any.whl"
        if not wheel_path.exists():
            self.log_error("Wheel package not found for testing")
            return False

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create virtual environment
                venv_path = Path(temp_dir) / "test_venv"
                subprocess.run([
                    sys.executable, "-m", "venv", str(venv_path)
                ], check=True, capture_output=True)

                # Get python executable in venv
                if os.name == 'nt':
                    python_exe = venv_path / "Scripts" / "python.exe"
                else:
                    python_exe = venv_path / "bin" / "python"

                # Install wheel
                subprocess.run([
                    str(python_exe), "-m", "pip", "install", str(wheel_path)
                ], check=True, capture_output=True)

                # Test import
                result = subprocess.run([
                    str(python_exe), "-c", "import laxyfile; print(laxyfile.__version__)"
                ], capture_output=True, text=True, check=True)

                installed_version = result.stdout.strip()
                if installed_version == self.version:
                    self.log_success(f"Package installation test passed (v{installed_version})")
                    return True
                else:
                    self.log_error(f"Version mismatch after installation: expected {self.version}, got {installed_version}")
                    return False

        except subprocess.CalledProcessError as e:
            self.log_error(f"Package installation test failed: {e}")
            return False
        except Exception as e:
            self.log_error(f"Error during installation test: {e}")
            return False

    def validate_all(self) -> bool:
        """Run all validations"""
        print(f"🔍 Validating LaxyFile v{self.version} deployment...")
        print("=" * 60)

        validations = [
            ("Version Consistency", self.validate_version_consistency),
            ("Package Files", self.validate_package_files),
            ("Wheel Package", self.validate_wheel_package),
            ("Source Package", self.validate_source_package),
            ("Checksums", self.validate_checksums),
            ("Release Notes", self.validate_release_notes),
            ("Package Manager Configs", self.validate_package_manager_configs),
            ("CI/CD Configuration", self.validate_ci_config),
            ("Package Installation", self.test_package_installation)
        ]

        results = {}

        for name, validation_func in validations:
            print(f"\n--- {name} ---")
            try:
                results[name] = validation_func()
            except Exception as e:
                self.log_error(f"Validation failed with exception: {e}")
                results[name] = False

        # Summary
        print("\n" + "=" * 60)
        print("🎯 Validation Summary")
        print("=" * 60)

        passed = sum(1 for result in results.values() if result)
        total = len(results)

        for name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {name}")

        print(f"\n📊 Results: {passed}/{total} validations passed")

        if self.warnings:
            print(f"⚠️ Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  - {warning}")

        if self.errors:
            print(f"❌ Errors: {len(self.errors)}")
            for error in self.errors:
                print(f"  - {error}")

        all_passed = all(results.values())

        if all_passed:
            print("\n🎉 All validations passed! Deployment is ready.")
        else:
            print("\n❌ Some validations failed. Please fix issues before deployment.")

        return all_passed


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Validate LaxyFile deployment")
    parser.add_argument("--version", help="Version to validate (default: from __init__.py)")

    args = parser.parse_args()

    # Get version
    version = args.version
    if not version:
        try:
            import laxyfile
            version = laxyfile.__version__
        except:
            version = "1.0.0"  # fallback

    validator = DeploymentValidator(version)

    try:
        success = validator.validate_all()
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n❌ Validation cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())