#!/usr/bin/env python3
"""
Comprehensive Deployment Script for LaxyFile

Automated deployment to all distribution channels:
- PyPI (Python Package Index)
- GitHub Releases
- Package managers (Homebrew, Chocolatey, etc.)
"""

import os
import sys
import subprocess
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional
import tempfile

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DIST_DIR = PROJECT_ROOT / "dist"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Import our deployment modules
sys.path.insert(0, str(SCRIPTS_DIR))
from deploy_pypi import PyPIDeployer
from build_release import ReleaseBuilder


class GitHubReleaseManager:
    """Manages GitHub releases and asset uploads"""

    def __init__(self, repo_owner: str, repo_name: str, token: str):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token
        self.api_base = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def create_release(self, tag_name: str, name: str, body: str,
                      draft: bool = False, prerelease: bool = False) -> Optional[Dict]:
        """Create a new GitHub release"""
        print(f"🚀 Creating GitHub release: {name}")

        url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/releases"

        data = {
            "tag_name": tag_name,
            "target_commitish": "main",
            "name": name,
            "body": body,
            "draft": draft,
            "prerelease": prerelease
        }

        try:
            response = requests.post(url, headers=self.headers, json=data)

            if response.status_code == 201:
                release_data = response.json()
                print(f"✅ Release created: {release_data['html_url']}")
                return release_data
            else:
                print(f"❌ Failed to create release: {response.status_code}")
                print(response.text)
                return None

        except requests.RequestException as e:
            print(f"❌ Error creating release: {e}")
            return None

    def upload_release_asset(self, release_id: int, file_path: Path,
                           content_type: str = "application/octet-stream") -> bool:
        """Upload an asset to a GitHub release"""
        print(f"📤 Uploading asset: {file_path.name}")

        upload_url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/releases/{release_id}/assets"

        params = {"name": file_path.name}
        headers = {**self.headers, "Content-Type": content_type}

        try:
            with open(file_path, "rb") as f:
                response = requests.post(upload_url, headers=headers,
                                       params=params, data=f)

            if response.status_code == 201:
                asset_data = response.json()
                print(f"✅ Asset uploaded: {asset_data['browser_download_url']}")
                return True
            else:
                print(f"❌ Failed to upload asset: {response.status_code}")
                print(response.text)
                return False

        except Exception as e:
            print(f"❌ Error uploading asset: {e}")
            return False


class ComprehensiveDeployer:
    """Main deployment orchestrator"""

    def __init__(self, version: str):
        self.version = version
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.repo_owner = "swadhinbiswas"
        self.repo_name = "laxyfile"

    def validate_environment(self) -> bool:
        """Validate deployment environment"""
        print("🔍 Validating deployment environment...")

        # Check required environment variables
        required_vars = ["GITHUB_TOKEN"]
        missing_vars = []

        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)

        if missing_vars:
            print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False

        # Check required tools
        required_tools = ["git", "python3"]
        missing_tools = []

        for tool in required_tools:
            try:
                subprocess.run([tool, "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                missing_tools.append(tool)

        if missing_tools:
            print(f"❌ Missing required tools: {', '.join(missing_tools)}")
            return False

        print("✅ Environment validation passed")
        return True

    def build_release_packages(self) -> List[Path]:
        """Build all release packages"""
        print("🔨 Building release packages...")

        builder = ReleaseBuilder()
        packages = builder.build_all_packages()

        if not packages:
            print("❌ No packages were built")
            return []

        print(f"✅ Built {len(packages)} packages")
        return packages

    def deploy_to_pypi(self, test_first: bool = True) -> bool:
        """Deploy to PyPI"""
        print("🐍 Deploying to PyPI...")

        # Deploy to Test PyPI first
        if test_first:
            print("📝 Deploying to Test PyPI first...")
            test_deployer = PyPIDeployer(test_pypi=True)
            if not test_deployer.deploy():
                print("❌ Test PyPI deployment failed")
                return False

            response = input("Test PyPI deployment successful. Deploy to production PyPI? (y/N): ")
            if response.lower() != 'y':
                print("❌ Production PyPI deployment cancelled")
                return False

        # Deploy to production PyPI
        prod_deployer = PyPIDeployer(test_pypi=False)
        return prod_deployer.deploy()

    def deploy_to_github(self, packages: List[Path]) -> bool:
        """Deploy to GitHub Releases"""
        print("🐙 Deploying to GitHub Releases...")

        if not self.github_token:
            print("❌ GITHUB_TOKEN not found")
            return False

        github = GitHubReleaseManager(self.repo_owner, self.repo_name, self.github_token)

        # Read release notes
        release_notes_path = DIST_DIR / f"RELEASE_NOTES_v{self.version}.md"
        if release_notes_path.exists():
            release_body = release_notes_path.read_text()
        else:
            release_body = f"LaxyFile v{self.version} release"

        # Create release
        tag_name = f"v{self.version}"
        release_name = f"LaxyFile v{self.version}"

        release_data = github.create_release(
            tag_name=tag_name,
            name=release_name,
            body=release_body,
            draft=False,
            prerelease=False
        )

        if not release_data:
            return False

        # Upload assets
        release_id = release_data["id"]
        success_count = 0

        for package_path in packages:
            if package_path.exists():
                # Determine content type
                content_type = "application/octet-stream"
                if package_path.suffix == ".tar.gz":
                    content_type = "application/gzip"
                elif package_path.suffix == ".zip":
                    content_type = "application/zip"
                elif package_path.suffix == ".deb":
                    content_type = "application/vnd.debian.binary-package"
                elif package_path.suffix == ".msi":
                    content_type = "application/x-msi"

                if github.upload_release_asset(release_id, package_path, content_type):
                    success_count += 1

        print(f"✅ Uploaded {success_count}/{len(packages)} assets to GitHub")
        return success_count > 0

    def create_deployment_summary(self, packages: List[Path]) -> None:
        """Create deployment summary"""
        print("\n" + "="*60)
        print(f"🎉 LaxyFile v{self.version} Deployment Summary")
        print("="*60)

        print(f"\n📦 Packages Built: {len(packages)}")
        for package in packages:
            if package.exists():
                size_mb = package.stat().st_size / (1024 * 1024)
                print(f"  ✅ {package.name} ({size_mb:.1f} MB)")

        print(f"\n🚀 Deployment Channels:")
        print(f"  📦 PyPI: https://pypi.org/project/laxyfile/{self.version}/")
        print(f"  🐙 GitHub: https://github.com/{self.repo_owner}/{self.repo_name}/releases/tag/v{self.version}")

        print(f"\n📋 Installation Commands:")
        print(f"  pip install laxyfile=={self.version}")

        print(f"\n🔗 Useful Links:")
        print(f"  📚 Documentation: https://github.com/{self.repo_owner}/{self.repo_name}#readme")
        print(f"  🐛 Issues: https://github.com/{self.repo_owner}/{self.repo_name}/issues")
        print(f"  💬 Discussions: https://github.com/{self.repo_owner}/{self.repo_name}/discussions")

    def deploy_all(self) -> bool:
        """Deploy to all channels"""
        print(f"🚀 Starting comprehensive deployment for LaxyFile v{self.version}")
        print()

        # Validate environment
        if not self.validate_environment():
            return False

        # Build packages
        packages = self.build_release_packages()
        if not packages:
            return False

        deployment_success = True

        # Deploy to PyPI
        try:
            if not self.deploy_to_pypi():
                print("⚠️ PyPI deployment failed")
                deployment_success = False
        except Exception as e:
            print(f"❌ PyPI deployment error: {e}")
            deployment_success = False

        # Deploy to GitHub
        try:
            if not self.deploy_to_github(packages):
                print("⚠️ GitHub deployment failed")
                deployment_success = False
        except Exception as e:
            print(f"❌ GitHub deployment error: {e}")
            deployment_success = False

        # Create summary
        self.create_deployment_summary(packages)

        return deployment_success


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Deploy LaxyFile to all channels")
    parser.add_argument("--version", help="Version to deploy (default: from setup.py)")
    parser.add_argument("--skip-pypi", action="store_true", help="Skip PyPI deployment")
    parser.add_argument("--skip-github", action="store_true", help="Skip GitHub deployment")
    parser.add_argument("--dry-run", action="store_true", help="Build packages only")

    args = parser.parse_args()

    # Get version
    version = args.version
    if not version:
        # Try to get version from setup.py or __init__.py
        try:
            import laxyfile
            version = laxyfile.__version__
        except:
            version = "1.0.0"  # fallback

    deployer = ComprehensiveDeployer(version)

    if args.dry_run:
        print("🧪 Dry run mode - building packages only")
        packages = deployer.build_release_packages()
        if packages:
            print(f"✅ Built {len(packages)} packages successfully")
            return 0
        else:
            print("❌ Package building failed")
            return 1

    try:
        success = deployer.deploy_all()
        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n❌ Deployment cancelled by user")
        return 1
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())