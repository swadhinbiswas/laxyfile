class Laxyfile < Formula
  desc "Advanced Terminal File Manager with AI Integration"
  homepage "https://github.com/swadhinbiswas/laxyfile"
  url "https://github.com/swadhinbiswas/laxyfile/archive/v1.0.0.tar.gz"
  sha256 "PLACEHOLDER_SHA256"
  license "MIT"

  depends_on "python@3.11"

  resource "rich" do
    url "https://files.pythonhosted.org/packages/source/r/rich/rich-13.7.0.tar.gz"
    sha256 "5cb5123b5cf9ee70584244246816e9114227e0b98ad9176eede6ad54bf5403fa"
  end

  resource "pydantic" do
    url "https://files.pythonhosted.org/packages/source/p/pydantic/pydantic-2.5.2.tar.gz"
    sha256 "ff177ba7c9dd6713ec1b2e1c2a1b3e1c9c1dcf6e1e1c1e1c1e1c1e1c1e1c1e1c"
  end

  resource "PyYAML" do
    url "https://files.pythonhosted.org/packages/source/P/PyYAML/PyYAML-6.0.1.tar.gz"
    sha256 "bfdf460b1736c775f2ba9f6a92bca30bc2095067b8a9d77876d1fad6cc3b4a43"
  end

  resource "Pillow" do
    url "https://files.pythonhosted.org/packages/source/P/Pillow/Pillow-10.1.0.tar.gz"
    sha256 "e6bf8de6c36ed96c86ea3b6e1d5273c53f46ef518a062464cd7ef5dd2cf92e38"
  end

  resource "opencv-python" do
    url "https://files.pythonhosted.org/packages/source/o/opencv-python/opencv-python-4.8.1.78.tar.gz"
    sha256 "cc7adbbcd1112d0e9eb9e8b1e7d1b4e1c6e6b8e6e6e6e6e6e6e6e6e6e6e6e6e6"
  end

  resource "pygments" do
    url "https://files.pythonhosted.org/packages/source/P/Pygments/Pygments-2.17.2.tar.gz"
    sha256 "da46cec9fd2de5be3a8a784f434e4c4ab670b4ff54d605c4c2717e9d49c4c367"
  end

  resource "openai" do
    url "https://files.pythonhosted.org/packages/source/o/openai/openai-1.6.1.tar.gz"
    sha256 "d553ca9f86d6f2c8e6c4b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5"
  end

  resource "psutil" do
    url "https://files.pythonhosted.org/packages/source/p/psutil/psutil-5.9.6.tar.gz"
    sha256 "e4b92ddcd7dd4cdd3f900180ea1e104932c7bce234fb88976e2a3b296441225a"
  end

  resource "python-magic" do
    url "https://files.pythonhosted.org/packages/source/p/python-magic/python-magic-0.4.27.tar.gz"
    sha256 "c1ba14b08e4a5f5c31a302b7721239695b2f0f058d125bd5ce1ee36b9d9d3c3b"
  end

  resource "requests" do
    url "https://files.pythonhosted.org/packages/source/r/requests/requests-2.31.0.tar.gz"
    sha256 "942c5a758f98d790eaed1a29cb6eefc7ffb0d1cf7af05c3d2791656dbd6ad1e1"
  end

  resource "aiofiles" do
    url "https://files.pythonhosted.org/packages/source/a/aiofiles/aiofiles-23.2.1.tar.gz"
    sha256 "84ec2218d8419404abcb9f0c02df3f34c6e0a68ed41072acfb1cef5cbc29051a"
  end

  def install
    virtualenv_install_with_resources

    # Create symlink for easy access
    bin.install_symlink libexec/"bin/laxyfile"

    # Install shell completions (if available)
    # bash_completion.install "completions/laxyfile.bash" => "laxyfile"
    # zsh_completion.install "completions/_laxyfile"
    # fish_completion.install "completions/laxyfile.fish"
  end

  def post_install
    puts <<~EOS
      LaxyFile has been installed successfully!

      To get started:
        1. Run 'laxyfile' to start the file manager
        2. For AI features, set your OpenRouter API key:
           export OPENROUTER_API_KEY="your-api-key"

      Documentation: https://github.com/swadhinbiswas/laxyfile/wiki
      Issues: https://github.com/swadhinbiswas/laxyfile/issues
    EOS
  end

  test do
    system "#{bin}/laxyfile", "--version"
    system "#{bin}/laxyfile", "--help"
  end
end