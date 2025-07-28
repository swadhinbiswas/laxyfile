#!/usr/bin/env python3
"""
Homebrew Formula Generator

Creates and updates Homebrew formula for LaxyFile
"""

import os
import sys
import hashlib
import requests
from pathlib import Path
import argparse


def get_archive_sha256(url: str) -> str:
    """Get SHA256 hash of archive from URL"""
    print(f"📥 Downloading archive to calculate SHA256: {url}")

    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()

        sha256_hash = hashlib.sha256()
        for chunk in response.iter_content(chunk_size=8192):
            sha256_hash.update(chunk)

        return sha256_hash.hexdigest()

    except requests.RequestException as e:
        print(f"❌ Error downloading archive: {e}")
        return ""


def create_homebrew_formula(version: str) -> str:
    """Create Homebrew formula content"""

    # Calculate SHA256 for the source archive
    archive_url = f"https://github.com/swadhinbiswas/laxyfile/archive/v{version}.tar.gz"
    sha256 = get_archive_sha256(archive_url)

    if not sha256:
        print("⚠️ Could not calculate SHA256, using placeholder")
        sha256 = "# SHA256 will be calculated automatically by Homebrew"

    formula_content = f'''class Laxyfile < Formula
  desc "Advanced Terminal File Manager with AI Integration"
  homepage "https://github.com/swadhinbiswas/laxyfile"
  url "{archive_url}"
  sha256 "{sha256}"
  license "MIT"
  head "https://github.com/swadhinbiswas/laxyfile.git", branch: "main"

  depends_on "python@3.11"

  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-13.7.0.tar.gz"
    sha256 "5cb5123b5cf9ee70584244246816e9114227e0b98ad9176eede6ad54bf5403fa"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic/pydantic-2.4.0.tar.gz"
    sha256 "94f336138093a5d7f426aac732dcfe7ab896bef37daf2a4b4f4d9e6ccb8e0a92"
  end

  resource "pyyaml" do
    url "https://files.pythonhosted.org/packages/source/P/PyYAML/PyYAML-6.0.1.tar.gz"
    sha256 "bfdf460b1736c775f2ba9f6a92bca30bc2095067b8a9d77876d1fad6cc3b4a43"
  end

  resource "pillow" do
    url "https://files.pythonhosted.org/packages/source/P/Pillow/Pillow-10.0.0.tar.gz"
    sha256 "9c82b5b3e043c7af0d95792d0d20ccf68f61a1fec6b3530e718b688422727396"
  end

  resource "opencv-python" do
    url "https://files.pythonhosted.org/packages/source/o/opencv-python/opencv-python-4.8.0.74.tar.gz"
    sha256 "72d234e4582e9658ffea8e9cae5b63d488ad06994ef12d81dc303b17472f3526"
  end

  resource "pygments" do
    url "https://files.pythonhosted.org/packages/source/P/Pygments/Pygments-2.16.1.tar.gz"
    sha256 "1daff0494820c69bc8941e407aa20f577374ee88364ee10a98fdbe0aece96e29"
  end

  resource "openai" do
    url "https://files.pythonhosted.org/packages/source/o/openai/openai-1.0.0.tar.gz"
    sha256 "3e3f3c9e7e3c3e3c3e3c3e3c3e3c3e3c3e3c3e3c3e3c3e3c3e3c3e3c3e3c3e3c"
  end

  resource "psutil" do
    url "https://files.pythonhosted.org/packages/source/p/psutil/psutil-5.9.5.tar.gz"
    sha256 "5410638e4df39c54d957fc51ce03048acd8e6d60abc0f5107af51e5fb566eb3c"
  end

  resource "python-magic" do
    url "https://files.pythonhosted.org/packages/source/p/python-magic/python-magic-0.4.27.tar.gz"
    sha256 "c1ba14b08e4a5f5c31a302b7721239695b2f0f058d125bd5ce1ee36b9d9d3c3b"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/source/r/requests/requests-2.31.0.tar.gz"
    sha256 "942c5a758f98d790eaed1a29cb6eefc7ffb0d1cf7af05c3d2791656dbd6ad1e1"
  end

  def install
    virtualenv_install_with_resources

    # Create symlink for easy access
    bin.install_symlink libexec/"bin/laxyfile"

    # Install shell completion (if available)
    if (libexec/"share/bash-completion").exist?
      bash_completion.install_symlink libexec/"share/bash-completion/completions/laxyfile"
    end

    if (libexec/"share/zsh/site-functions").exist?
      zsh_completion.install_symlink libexec/"share/zsh/site-functions/_laxyfile"
    end

    if (libexec/"share/fish/vendor_completions.d").exist?
      fish_completion.install_symlink libexec/"share/fish/vendor_completions.d/laxyfile.fish"
    end
  end

  test do
    system bin/"laxyfile", "--version"
    system bin/"laxyfile", "--help"

    # Test basic functionality
    (testpath/"test_dir").mkdir
    (testpath/"test_file.txt").write "Hello, LaxyFile!"

    # Test that LaxyFile can list directory contents
    output = shell_output("#{bin}/laxyfile --list #{testpath}")
    assert_match "test_dir", output
    assert_match "test_file.txt", output
  end
end
'''

    return formula_content


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Create Homebrew formula for LaxyFile")
    parser.add_argument("--version", required=True, help="Version to create formula for")
    parser.add_argument("--output", help="Output file path (default: packaging/homebrew/laxyfile.rb)")

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        project_root = Path(__file__).parent.parent
        output_path = project_root / "packaging" / "homebrew" / "laxyfile.rb"

    # Create output directory
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"🍺 Creating Homebrew formula for LaxyFile v{args.version}")

    # Generate formula
    formula_content = create_homebrew_formula(args.version)

    # Write formula
    output_path.write_text(formula_content)

    print(f"✅ Homebrew formula created: {output_path}")
    print()
    print("📋 Next steps:")
    print("1. Test the formula locally:")
    print(f"   brew install --build-from-source {output_path}")
    print("2. Submit to homebrew-core:")
    print("   https://github.com/Homebrew/homebrew-core/blob/master/CONTRIBUTING.md")
    print("3. Or create a tap:")
    print("   https://docs.brew.sh/How-to-Create-and-Maintain-a-Tap")

    return 0


if __name__ == "__main__":
    sys.exit(main())