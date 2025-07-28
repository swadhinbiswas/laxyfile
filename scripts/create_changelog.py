#!/usr/bin/env python3
"""
Changelog Generator

Automatically generates changelog from git commits and GitHub issues/PRs
"""

import os
import sys
import subprocess
import json
import requests
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import argparse
import datetime
import re


class ChangelogGenerator:
    """Generates changelog from git history and GitHub data"""

    def __init__(self, repo_owner: str, repo_name: str, github_token: Optional[str] = None):
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.github_token = github_token
        self.api_base = "https://api.github.com"

        self.headers = {}
        if github_token:
            self.headers["Authorization"] = f"token {github_token}"
            self.headers["Accept"] = "application/vnd.github.v3+json"

    def get_git_tags(self) -> List[str]:
        """Get all git tags sorted by version"""
        try:
            result = subprocess.run(
                ["git", "tag", "-l", "--sort=-version:refname"],
                capture_output=True, text=True, check=True
            )
            return [tag.strip() for tag in result.stdout.split('\n') if tag.strip()]
        except subprocess.CalledProcessError:
            return []

    def get_commits_between_tags(self, from_tag: Optional[str], to_tag: Optional[str]) -> List[Dict]:
        """Get commits between two tags"""
        try:
            # Build git log command
            cmd = ["git", "log", "--pretty=format:%H|%s|%an|%ae|%ad", "--date=iso"]

            if from_tag and to_tag:
                cmd.append(f"{from_tag}..{to_tag}")
            elif to_tag:
                cmd.append(to_tag)
            elif from_tag:
                cmd.append(f"{from_tag}..HEAD")
            else:
                cmd.append("HEAD")

            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            commits = []
line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split('|', 4)
                    if len(parts) >= 5:
                        commits.append({
                            'hash': parts[0],
                            'subject': parts[1],
                            'author': parts[2],
                            'email': parts[3],
                            'date': parts[4]
                        })

            return commits

        except subprocess.CalledProcessError:
            return []

    def categorize_commit(self, commit_subject: str) -> str:
        """Categorize commit based on subject"""
        subject_lower = commit_subject.lower()

        # Feature additions
        if any(keyword in subject_lower for keyword in ['feat:', 'feature:', 'add:', 'implement:', 'new:']):
            return 'features'

        # Bug fixes
        if any(keyword in subject_lower for keyword in ['fix:', 'bug:', 'patch:', 'hotfix:']):
            return 'fixes'

        # Performance improvements
        if any(keyword in subject_lower for keyword in ['perf:', 'performance:', 'optimize:', 'speed:']):
            return 'performance'

        # Documentation
        if any(keyword in subject_lower for keyword in ['docs:', 'doc:', 'documentation:', 'readme:']):
            return 'documentation'

        # Tests
        if any(keyword in subject_lower for keyword in ['test:', 'tests:', 'testing:']):
            return 'tests'

        # Refactoring
        if any(keyword in subject_lower for keyword in ['refactor:', 'refact:', 'cleanup:', 'clean:']):
            return 'refactoring'

        # Dependencies
        if any(keyword in subject_lower for keyword in ['deps:', 'dependencies:', 'bump:', 'update:']):
            return 'dependencies'

        # CI/CD
        if any(keyword in subject_lower for keyword in ['ci:', 'cd:', 'build:', 'deploy:']):
            return 'ci'

        # Security
        if any(keyword in subject_lower for keyword in ['security:', 'sec:', 'vulnerability:', 'cve:']):
            return 'security'

        # Default category
        return 'other'

    def get_github_issues_and_prs(self, since_date: Optional[str] = None) -> Tuple[List[Dict], List[Dict]]:
        """Get GitHub issues and PRs"""
        if not self.github_token:
            return [], []

        issues = []
        prs = []

        try:
            # Get issues
            issues_url = f"{self.api_base}/repos/{self.repo_owner}/{self.repo_name}/issues"
            params = {"state": "closed", "sort": "updated", "direction": "desc"}
            if since_date:
                params["since"] = since_date

            response = requests.get(issues_url, headers=self.headers, params=params)
            if response.status_code == 200:
                for item in response.json():
                    if 'pull_request' in item:
                        prs.append(item)
                    else:
                        issues.append(item)

        except requests.RequestException as e:
            print(f"⚠️ Error fetching GitHub data: {e}")

        return issues, prs

    def generate_version_changelog(self, version: str, from_tag: Optional[str],
                                 to_tag: Optional[str], release_date: str) -> str:
        """Generate changelog for a specific version"""

        # Get commits
        commits = self.get_commits_between_tags(from_tag, to_tag)

        # Categorize commits
        categorized_commits = {
            'features': [],
            'fixes': [],
            'performance': [],
            'security': [],
            'documentation': [],
            'tests': [],
            'refactoring': [],
            'dependencies': [],
            'ci': [],
            'other': []
        }

        for commit in commits:
            category = self.categorize_commit(commit['subject'])
            categorized_commits[category].append(commit)

        # Build changelog section
        changelog = f"## [{version}] - {release_date}\n\n"

        # Add sections with content
        section_titles = {
            'features': '### ✨ New Features',
            'fixes': '### 🐛 Bug Fixes',
            'performance': '### ⚡ Performance Improvements',
            'security': '### 🔒 Security',
            'documentation': '### 📚 Documentation',
            'tests': '### 🧪 Tests',
            'refactoring': '### ♻️ Code Refactoring',
            'dependencies': '### 📦 Dependencies',
            'ci': '### 👷 CI/CD',
            'other': '### 🔧 Other Changes'
        }

        for category, title in section_titles.items():
            commits_in_category = categorized_commits[category]
            if commits_in_category:
                changelog += f"{title}\n\n"
                for commit in commits_in_category:
                    # Clean up commit subject
                    subject = commit['subject']
                    # Remove conventional commit prefixes
                    subject = re.sub(r'^(feat|fix|docs|style|refactor|perf|test|chore|ci|build)(\(.+\))?: ', '', subject)

                    changelog += f"- {subject} ([{commit['hash'][:7]}](https://github.com/{self.repo_owner}/{self.repo_name}/commit/{commit['hash']}))\n"
                changelog += "\n"

        return changelog

    def generate_full_changelog(self, output_file: Optional[str] = None) -> str:
        """Generate complete changelog"""

        print("📝 Generating changelog...")

        # Get all tags
        tags = self.get_git_tags()

        # Build changelog
        changelog_content = f"""# Changelog

All notable changes to LaxyFile will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

"""

        # Add unreleased section
        unreleased_commits = self.get_commits_between_tags(tags[0] if tags else None, None)
        if unreleased_commits:
            changelog_content += self.generate_version_changelog(
                "Unreleased",
                tags[0] if tags else None,
                None,
                "TBD"
            )

        # Add sections for each tag
        for i, tag in enumerate(tags):
            # Get previous tag
            prev_tag = tags[i + 1] if i + 1 < len(tags) else None

            # Get tag date
            try:
                result = subprocess.run(
                    ["git", "log", "-1", "--format=%ai", tag],
                    capture_output=True, text=True, check=True
                )
                tag_date = result.stdout.strip().split()[0]
            except subprocess.CalledProcessError:
                tag_date = datetime.datetime.now().strftime("%Y-%m-%d")

            # Clean version (remove 'v' prefix if present)
            version = tag.lstrip('v')

            changelog_content += self.generate_version_changelog(
                version, prev_tag, tag, tag_date
            )

        # Add footer
        changelog_content += f"""
---

**Full Changelog**: https://github.com/{self.repo_owner}/{self.repo_name}/commits/main

For more information about releases, visit: https://github.com/{self.repo_owner}/{self.repo_name}/releases
"""

        # Write to file if specified
        if output_file:
            output_path = Path(output_file)
            output_path.write_text(changelog_content)
            print(f"✅ Changelog written to: {output_path}")

        return changelog_content

    def generate_release_notes(self, version: str, output_file: Optional[str] = None) -> str:
        """Generate release notes for a specific version"""

        print(f"📝 Generating release notes for v{version}...")

        # Get tags to find the range
        tags = self.get_git_tags()

        # Find current and previous tag
        current_tag = f"v{version}"
        prev_tag = None

        for i, tag in enumerate(tags):
            if tag == current_tag:
                prev_tag = tags[i + 1] if i + 1 < len(tags) else None
                break

        # Generate release notes
        release_date = datetime.datetime.now().strftime("%Y-%m-%d")

        release_notes = f"""# LaxyFile v{version} Release Notes

**Release Date:** {release_date}

## 🚀 What's New

{self.generate_version_changelog(version, prev_tag, current_tag, release_date)}

## 📦 Installation

### Python Package (Recommended)
```bash
pip install laxyfile=={version}
laxyfile
```

### Standalone Executables
- **Linux**: Download `laxyfile-{version}-linux-standalone`
- **macOS**: Download `LaxyFile-{version}-macOS.tar.gz`
- **Windows**: Download `laxyfile-{version}-windows-standalone.exe`

## 🔧 System Requirements

- **Python**: 3.8 or higher
- **Terminal**: Modern terminal with color support
- **Memory**: 256MB+ RAM
- **Storage**: 50MB+ free space

## 🤖 AI Setup

1. Get free API key from [OpenRouter](https://openrouter.ai/)
2. Set environment variable: `export OPENROUTER_API_KEY="your-key"`
3. Launch LaxyFile and enjoy AI features!

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/{self.repo_owner}/{self.repo_name}/issues)
- **Discussions**: [GitHub Discussions](https://github.com/{self.repo_owner}/{self.repo_name}/discussions)
- **Documentation**: [GitHub Wiki](https://github.com/{self.repo_owner}/{self.repo_name}/wiki)

---

**Full Changelog**: https://github.com/{self.repo_owner}/{self.repo_name}/compare/{prev_tag}...v{version}
"""

        # Write to file if specified
        if output_file:
            output_path = Path(output_file)
            output_path.write_text(release_notes)
            print(f"✅ Release notes written to: {output_path}")

        return release_notes


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate changelog for LaxyFile")
    parser.add_argument("--version", help="Generate release notes for specific version")
    parser.add_argument("--output", help="Output file path")
    parser.add_argument("--repo-owner", default="swadhinbiswas", help="GitHub repository owner")
    parser.add_argument("--repo-name", default="laxyfile", help="GitHub repository name")
    parser.add_argument("--github-token", help="GitHub token for API access")

    args = parser.parse_args()

    # Get GitHub token from environment if not provided
    github_token = args.github_token or os.getenv("GITHUB_TOKEN")

    generator = ChangelogGenerator(args.repo_owner, args.repo_name, github_token)

    try:
        if args.version:
            # Generate release notes for specific version
            output_file = args.output or f"RELEASE_NOTES_v{args.version}.md"
            generator.generate_release_notes(args.version, output_file)
        else:
            # Generate full changelog
            output_file = args.output or "CHANGELOG.md"
            generator.generate_full_changelog(output_file)

        return 0

    except Exception as e:
        print(f"❌ Error generating changelog: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())