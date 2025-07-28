#!/usr/bin/env python3
"""
PyPI Deployment Script

Automated script for publishing LaxyFile to PyPI.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path
import json
import requests

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"


class PyPIDeployer:
    """PyPI deployment manager"""

    def __init__(self, test_pypi=False):
        self.test_pypi = test_pypi
        self.pypi_url = "https://test.pypi.org/simple/" if test_pypi else "https://pypi.org/simple/"
        self.upload_url = "https://test.pypi.org/legacy/" if test_pypi else "https://upload.pypi.org/legacy/"

    def check_credentials(self):
        """Check if PyPI credentials are available"""
        print("🔐 Checking PyPI credentials...")

        # Check for API token
        token_env = "TEST_PYPI_API_TOKEN" if self.test_pypi else "PYPI_API_TOKEN"
        if os.getenv(token_env):
            print("✅ API token found in environment")
            return True

        # Check for username/password
        username = os.getenv("PYPI_USERNAME")
        password = os.getenv("PYPI_PASSWORD")

        if username and password:
            print("✅ Username/password found in environment")
            return True

        # Check .pypirc file
        pypirc_path = Path.home() / ".pypirc"
        if pypirc_path.exists():
            print("✅ .pypirc file found")
            return True

        print("❌ No PyPI credentials found")
        print("Please set one of:")
        print(f"  - {token_env} environment variable")
        print("  - PYPI_USERNAME and PYPI_PASSWORD environment variables")
        print("  - ~/.pypirc file")
        return False

    def check_package_exists(self, package_name, version):
        """Check if package version already exists on PyPI"""
        print(f"🔍 Checking if {package_name} v{version} exists on PyPI...")

        try:
            url = f"https://pypi.org/pypi/{package_name}/{version}/json"
            if self.test_pypi:
                url = f"https://test.pypi.org/pypi/{package_name}/{version}/json"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                print(f"⚠️ Package {package_name} v{version} already exists")
                return True
            elif response.status_code == 404:
                print(f"✅ Package {package_name} v{version} does not exist")
                return False
            else:
                print(f"⚠️ Unable to check package existence (HTTP {response.status_code})")
                return False

        except requests.RequestException as e:
            print(f"⚠️ Error checking package existence: {e}")
            return False

    def build_package(self):
        """Build the package for distribution"""
        print("🔨 Building package...")

        # Clean previous builds
        if DIST_DIR.exists():
            import shutil
            shutil.rmtree(DIST_DIR)

        # Build source distribution and wheel
        try:
            result = subprocess.run([
                sys.executable, "-m", "build"
            ], cwd=PROJECT_ROOT, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Package built successfully")

                # List built packages
                if DIST_DIR.exists():
                    packages = list(DIST_DIR.glob("*"))
                    print("📦 Built packages:")
                    for pkg in packages:
                        size_mb = pkg.stat().st_size / (1024 * 1024)
                        print(f"  - {pkg.name} ({size_mb:.1f} MB)")
                    return packages
                else:
                    print("❌ No packages found after build")
                    return []
            else:
                print(f"❌ Package build failed: {result.stderr}")
                return []

        except Exception as e:
            print(f"❌ Error building package: {e}")
            return []

    def validate_package(self, package_path):
        """Validate package before upload"""
        print(f"🔍 Validating package: {package_path.name}")

        try:
            # Use twine to check the package
            result = subprocess.run([
                sys.executable, "-m", "twine", "check", str(package_path)
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Package validation passed")
                return True
            else:
                print(f"❌ Package validation failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error validating package: {e}")
            return False

    def upload_package(self, packages):
        """Upload packages to PyPI"""
        repository = "testpypi" if self.test_pypi else "pypi"
        print(f"📤 Uploading packages to {repository}...")

        try:
            # Upload using twine
            cmd = [sys.executable, "-m", "twine", "upload"]

            if self.test_pypi:
                cmd.extend(["--repository", "testpypi"])

            cmd.extend([str(pkg) for pkg in packages])

            result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Packages uploaded successfully")
                print(result.stdout)
                return True
            else:
                print(f"❌ Package upload failed: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ Error uploading packages: {e}")
            return False

    def verify_upload(self, package_name, version):
        """Verify that the package was uploaded successfully"""
        print(f"🔍 Verifying upload of {package_name} v{version}...")

        try:
            # Wait a moment for PyPI to process
            import time
            time.sleep(5)

            # Check if package is available
            url = f"https://pypi.org/pypi/{package_name}/{version}/json"
            if self.test_pypi:
                url = f"https://test.pypi.org/pypi/{package_name}/{version}/json"

            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                print("✅ Package successfully uploaded and available")
                print(f"📦 Package URL: {data['info']['package_url']}")
                return True
            else:
                print(f"❌ Package not found after upload (HTTP {response.status_code})")
                return False

        except requests.RequestException as e:
            print(f"⚠️ Error verifying upload: {e}")
            return False

    def deploy(self):
        """Main deployment process"""
        env_name = "Test PyPI" if self.test_pypi else "PyPI"
        print(f"🚀 Deploying LaxyFile to {env_name}")
        print()

        # Check credentials
        if not self.check_credentials():
            return False

        # Build package
        packages = self.build_package()
        if not packages:
            return False

        # Validate packages
        valid_packages = []
        for pkg in packages:
            if self.validate_package(pkg):
                valid_packages.append(pkg)

        if not valid_packages:
            print("❌ No valid packages to upload")
            return False

        # Check if package already exists
        from laxyfile import __version__
        if self.check_package_exists("laxyfile", __version__):
            response = input("Package version already exists. Continue anyway? (y/N): ")
            if response.lower() != 'y':
                print("❌ Deployment cancelled")
                return False

        # Upload packages
        if not self.upload_package(valid_packages):
            return False

        # Verify upload
        if not self.verify_upload("laxyfile", __version__):
            print("⚠️ Upload verification failed, but package may still be available")

        print()
        print(f"🎉 LaxyFile successfully deployed to {env_name}!")

        if self.test_pypi:
            print("📦 Test installation command:")
            print("pip install --index-url https://test.pypi.org/simple/ laxyfile")
        else:
            print("📦 Installation command:")
            print("pip install laxyfile")

        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Deploy LaxyFile to PyPI")
    parser.add_argument("--test", action="store_true",
                       help="Deploy to Test PyPI instead of production PyPI")
    parser.add_argument("--dry-run", action="store_true",
                       help="Build and validate packages without uploading")

    args = parser.parse_args()

    deployer = PyPIDeployer(test_pypi=args.test)

    if args.dry_run:
        print("🧪 Dry run mode - building and validating packages only")
        packages = deployer.build_package()
        if packages:
            for pkg in packages:
                deployer.validate_package(pkg)
        return 0

    try:
        success = deployer.deploy()
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n❌ Deployment cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())