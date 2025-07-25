# Contributing to LaxyFile

Thank you for your interest in contributing to LaxyFile! This document provides guidelines and information for contributors.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Development Setup](#development-setup)
3. [Contributing Guidelines](#contributing-guidelines)
4. [Code Standards](#code-standards)
5. [Testing](#testing)
6. [Documentation](#documentation)
7. [Pull Request Process](#pull-request-process)
8. [Community Guidelines](#community-guidelines)

## Getting Started

### Ways to Contribute

There are many ways to contribute to LaxyFile:

- **Bug Reports**: Report issues you encounter
- **Feature Requests**: Suggest new features or improvements
- **Code Contributions**: Fix bugs or implement new features
- **Documentation**: Improve or add documentation
- **Testing**: Help test new features and releases
- **Plugins**: Create plugins to extend functionality
- **Themes**: Design new themes for the UI
- **Translations**: Help translate LaxyFile to other languages

### Before You Start

1. **Check Existing Issues**: Look through existing issues to avoid duplicates
2. **Read the Documentation**: Familiarize yourself with LaxyFile's architecture
3. **Join the Community**:ect with other contributors on Discord or GitHub Discussions
4. **Start Small**: Begin with small contributions to get familiar with the codebase

## Development Setup

### Prerequisites

- **Python 3.8+** (Python 3.11+ recommended)
- **Git** for version control
- **Terminal** with good Unicode support
- **Code Editor** (VS Code, PyCharm, or similar recommended)

### Setting Up the Development Environment

1. **Fork and Clone the Repository**

   ```bash
   git clone https://github.com/your-username/laxyfile.git
   cd laxyfile
   ```

2. **Create a Virtual Environment**

   ```bash
   python -m venv venv

   # On Windows
   venv\Scripts\activate

   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install Dependencies**

   ```bash
   # Install development dependencies
   pip install -e ".[dev]"

   # Or install from requirements
   pip install -r requirements-dev.txt
   ```

4. **Install Pre-commit Hooks**

   ```bash
   pre-commit install
   ```

5. **Verify Installation**

   ```bash
   # Run LaxyFile in development mode
   python -m laxyfile --debug

   # Run tests
   pytest

   # Run linting
   flake8 laxyfile/
   black --check laxyfile/
   mypy laxyfile/
   ```

### Development Tools

We use several tools to maintain code quality:

- **Black**: Code formatting
- **Flake8**: Linting and style checking
- **MyPy**: Type checking
- **Pytest**: Testing framework
- **Pre-commit**: Git hooks for code quality
- **Coverage**: Test coverage reporting

### Project Structure

```
laxyfile/
├── laxyfile/           # Main package
│   ├── core/          # Core components
│   ├── ui/            # User interface
│   ├── ai/            # AI integration
│   ├── operations/    # File operations
│   ├── plugins/       # Plugin system
│   └── utils/         # Utilities
├── tests/             # Test suite
│   ├── unit/          # Unit tests
│   ├── integration/   # Integration tests
│   ├── e2e/           # End-to-end tests
│   └── performance/   # Performance tests
├── docs/              # Documentation
├── scripts/           # Build and utility scripts
└── examples/          # Example configurations and plugins
```

## Contributing Guidelines

### Issue Reporting

When reporting bugs or requesting features:

1. **Use Issue Templates**: Fill out the provided templates completely
2. **Be Specific**: Provide detailed descriptions and steps to reproduce
3. **Include Context**: Operating system, Python version, LaxyFile version
4. **Add Screenshots**: Visual issues benefit from screenshots
5. **Check Logs**: Include relevant log output when reporting bugs

#### Bug Report Template

```markdown
**Bug Description**
A clear description of the bug.

**Steps to Reproduce**

1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior**
What you expected to happen.

**Actual Behavior**
What actually happened.

**Environment**

- OS: [e.g., Windows 11, macOS 13, Ubuntu 22.04]
- Python Version: [e.g., 3.11.2]
- LaxyFile Version: [e.g., 2.0.0]
- Terminal: [e.g., Windows Terminal, iTerm2]

**Additional Context**
Any other context about the problem.

**Logs**
```

Paste relevant log output here

```

```

#### Feature Request Template

```markdown
**Feature Description**
A clear description of the feature you'd like to see.

**Use Case**
Describe the problem this feature would solve.

**Proposed Solution**
How you envision this feature working.

**Alternatives Considered**
Other solutions you've considered.

**Additional Context**
Any other context or screenshots about the feature request.
```

### Code Contributions

#### Choosing What to Work On

- **Good First Issues**: Look for issues labeled `good first issue`
- **Help Wanted**: Issues labeled `help wanted` need contributors
- **Feature Requests**: Implement requested features
- **Bug Fixes**: Fix reported bugs
- **Performance**: Optimize existing code
- **Documentation**: Improve or add documentation

#### Before Starting Development

1. **Comment on the Issue**: Let others know you're working on it
2. **Discuss Approach**: For large changes, discuss your approach first
3. **Create a Branch**: Use descriptive branch names
4. **Keep it Focused**: One feature or fix per pull request

#### Branch Naming Convention

```bash
# Feature branches
feature/add-git-integration
feature/improve-ai-analysis

# Bug fix branches
fix/file-copy-progress-bar
fix/theme-switching-crash

# Documentation branches
docs/update-api-reference
docs/add-plugin-tutorial

# Performance branches
perf/optimize-directory-listing
perf/reduce-memory-usage
```

## Code Standards

### Python Style Guide

We follow PEP 8 with some modifications:

- **Line Length**: 88 characters (Black default)
- **Imports**: Use absolute imports, group by standard/third-party/local
- **Docstrings**: Use Google-style docstrings
- **Type Hints**: Required for all public functions and methods
- **Naming**: Use descriptive names, avoid abbreviations

### Code Formatting

We use **Black** for code formatting:

```bash
# Format all code
black laxyfile/ tests/

# Check formatting
black --check laxyfile/ tests/
```

### Type Checking

We use **MyPy** for type checking:

```bash
# Run type checking
mypy laxyfile/

# Configuration in pyproject.toml
[tool.mypy]
python_version = "3.8"
strict = true
warn_return_any = true
warn_unused_configs = true
```

### Linting

We use **Flake8** for linting:

```bash
# Run linting
flake8 laxyfile/

# Configuration in .flake8
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist
```

### Documentation Standards

#### Docstring Format

Use Google-style docstrings:

```python
def analyze_file(
    self,
    file_path: Path,
    analysis_type: AnalysisType = AnalysisType.COMPREHENSIVE
) -> AnalysisResult:
    """Analyze a file using AI.

    Args:
        file_path: Path to the file to analyze
        analysis_type: Type of analysis to perform

    Returns:
        Analysis result containing insights and suggestions

    Raises:
        FileNotFoundError: If the file doesn't exist
        AIProviderError: If AI analysis fails

    Example:
        >>> assistant = AdvancedAIAssistant(config)
        >>> result = await assistant.analyze_file(Path("document.pdf"))
        >>> print(result.analysis)
    """
```

#### Code Comments

- **Explain Why**: Comments should explain why, not what
- **Complex Logic**: Comment complex algorithms or business logic
- **TODOs**: Use TODO comments for future improvements
- **Performance**: Comment performance-critical sections

```python
# Good: Explains why
# Use LRU cache to improve performance for frequently accessed files
self.file_cache = LRUCache(maxsize=1000)

# Bad: Explains what (obvious from code)
# Create an LRU cache
self.file_cache = LRUCache(maxsize=1000)
```

### Error Handling

#### Exception Handling

```python
# Use specific exceptions
try:
    result = await ai_provider.analyze(content)
except AIProviderError as e:
    self.logger.error(f"AI analysis failed: {e}")
    raise AnalysisError(f"Failed to analyze file: {e}") from e
except Exception as e:
    self.logger.exception("Unexpected error during analysis")
    raise

# Provide user-friendly error messages
class LaxyFileError(Exception):
    """Base exception for LaxyFile errors"""

    def __init__(self, message: str, user_message: str = None):
        super().__init__(message)
        self.user_message = user_message or message
```

#### Logging

```python
import logging

# Use module-level logger
logger = logging.getLogger(__name__)

# Log at appropriate levels
logger.debug("Starting file analysis")  # Detailed debugging info
logger.info("File analysis completed")   # General information
logger.warning("AI provider slow")       # Warning conditions
logger.error("Analysis failed")          # Error conditions
logger.critical("System failure")        # Critical errors

# Include context in log messages
logger.info(
    "File analysis completed",
    extra={
        "file_path": str(file_path),
        "analysis_type": analysis_type.value,
        "duration": duration
    }
)
```

### Async Programming

#### Async Best Practices

```python
# Use async/await for I/O operations
async def list_directory(self, path: Path) -> List[FileInfo]:
    """List directory contents asynchronously"""
    loop = asyncio.get_event_loop()

    # Use thread pool for blocking I/O
    with ThreadPoolExecutor() as executor:
        files = await loop.run_in_executor(executor, os.listdir, path)

    # Process files concurrently
    tasks = [self._get_file_info(path / f) for f in files]
    return await asyncio.gather(*tasks, return_exceptions=True)

# Handle exceptions in async code
async def safe_operation(self, operation: Callable) -> Optional[Any]:
    """Safely execute async operation with error handling"""
    try:
        return await operation()
    except Exception as e:
        logger.exception(f"Operation failed: {e}")
        return None

# Use context managers for resources
async def process_file(self, file_path: Path) -> None:
    """Process file with proper resource management"""
    async with aiofiles.open(file_path, 'r') as f:
        content = await f.read()
        await self.analyze_content(content)
```

## Testing

### Testing Philosophy

- **Test-Driven Development**: Write tests before or alongside code
- **Comprehensive Coverage**: Aim for high test coverage
- **Fast Tests**: Unit tests should run quickly
- **Isolated Tests**: Tests should not depend on each other
- **Realistic Tests**: Integration tests should use realistic scenarios

### Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_file_manager.py
│   ├── test_ai_assistant.py
│   └── test_ui_components.py
├── integration/             # Integration tests
│   ├── test_file_workflows.py
│   ├── test_ai_integration.py
│   └── test_plugin_system.py
├── e2e/                     # End-to-end tests
│   └── test_user_workflows.py
├── performance/             # Performance tests
│   └── test_benchmarks.py
├── fixtures/                # Test fixtures
│   ├── sample_files/
│   └── test_configs/
└── conftest.py             # Pytest configuration
```

### Writing Tests

#### Unit Tests

```python
import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from laxyfile.core.advanced_file_manager import AdvancedFileManager
from laxyfile.core.types import FileInfo

class TestAdvancedFileManager:
    """Test suite for AdvancedFileManager"""

    @pytest.fixture
    def file_manager(self, mock_config):
        """Create file manager for testing"""
        return AdvancedFileManager(mock_config)

    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing"""
        config = Mock()
        config.get.return_value = 1000  # cache_size
        return config

    @pytest.mark.asyncio
    async def test_list_directory_success(self, file_manager, tmp_path):
        """Test successful directory listing"""
        # Create test files
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.txt").write_text("content2")

        # Test directory listing
        files = await file_manager.list_directory(tmp_path)

        # Assertions
        assert len(files) == 2
        assert all(isinstance(f, FileInfo) for f in files)
        assert {f.name for f in files} == {"file1.txt", "file2.txt"}

    @pytest.mark.asyncio
    async def test_list_directory_permission_error(self, file_manager):
        """Test directory listing with permission error"""
        with patch('os.listdir', side_effect=PermissionError("Access denied")):
            with pytest.raises(PermissionError):
                await file_manager.list_directory(Path("/restricted"))

    def test_cache_behavior(self, file_manager, tmp_path):
        """Test file info caching"""
        file_path = tmp_path / "test.txt"
        file_path.write_text("content")

        # First call should cache the result
        info1 = file_manager.get_file_info_sync(file_path)

        # Second call should return cached result
        with patch('os.stat') as mock_stat:
            info2 = file_manager.get_file_info_sync(file_path)
            mock_stat.assert_not_called()

        assert info1 == info2
```

#### Integration Tests

```python
import pytest
import tempfile
from pathlib import Path

from laxyfile.main import LaxyFileApp
from laxyfile.core.config import Config

class TestFileWorkflows:
    """Integration tests for file workflows"""

    @pytest.fixture
    def app(self):
        """Create LaxyFile app for testing"""
        config = Config()
        config.set('ai.enabled', False)  # Disable AI for testing
        return LaxyFileApp(config)

    @pytest.fixture
    def test_workspace(self):
        """Create temporary workspace for testing"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            workspace = Path(tmp_dir)

            # Create test structure
            (workspace / "documents").mkdir()
            (workspace / "documents" / "file1.txt").write_text("content1")
            (workspace / "documents" / "file2.txt").write_text("content2")

            (workspace / "images").mkdir()
            (workspace / "images" / "photo.jpg").write_bytes(b"fake image data")

            yield workspace

    @pytest.mark.asyncio
    async def test_copy_files_workflow(self, app, test_workspace):
        """Test complete file copy workflow"""
        source_dir = test_workspace / "documents"
        dest_dir = test_workspace / "backup"
        dest_dir.mkdir()

        # Select files to copy
        files_to_copy = list(source_dir.glob("*.txt"))

        # Perform copy operation
        success = await app.file_manager.copy_files(
            files_to_copy,
            dest_dir
        )

        # Verify results
        assert success
        assert (dest_dir / "file1.txt").exists()
        assert (dest_dir / "file2.txt").exists()
        assert (dest_dir / "file1.txt").read_text() == "content1"
        assert (dest_dir / "file2.txt").read_text() == "content2"
```

#### Performance Tests

```python
import pytest
import time
from pathlib import Path

class TestPerformance:
    """Performance tests"""

    @pytest.mark.performance
    def test_large_directory_listing_performance(self, file_manager, large_directory):
        """Test performance with large directory (1000+ files)"""
        start_time = time.time()

        files = file_manager.list_directory_sync(large_directory)

        end_time = time.time()
        duration = end_time - start_time

        # Performance assertions
        assert len(files) >= 1000
        assert duration < 2.0  # Should complete within 2 seconds

    @pytest.mark.performance
    def test_memory_usage(self, file_manager, large_directory):
        """Test memory usage during operations"""
        import psutil
        import gc

        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Perform memory-intensive operation
        for _ in range(10):
            files = file_manager.list_directory_sync(large_directory)

        peak_memory = process.memory_info().rss
        memory_increase = (peak_memory - initial_memory) / 1024 / 1024  # MB

        # Force garbage collection
        gc.collect()
        final_memory = process.memory_info().rss

        # Memory assertions
        assert memory_increase < 100  # Should not use more than 100MB
        assert final_memory < peak_memory + 10 * 1024 * 1024  # Should release memory
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/unit/                    # Unit tests only
pytest tests/integration/             # Integration tests only
pytest -m "not performance"          # Exclude performance tests

# Run with coverage
pytest --cov=laxyfile --cov-report=html

# Run performance tests
pytest -m performance --benchmark-only

# Run tests in parallel
pytest -n auto

# Run specific test
pytest tests/unit/test_file_manager.py::TestAdvancedFileManager::test_list_directory
```

### Test Configuration

```python
# conftest.py
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock

@pytest.fixture
def temp_dir():
    """Create temporary directory for testing"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

@pytest.fixture
def mock_config():
    """Mock configuration for testing"""
    config = Mock()
    config.get = Mock(side_effect=lambda key, default=None: {
        'cache_size': 1000,
        'ai.enabled': False,
        'ui.theme': 'default'
    }.get(key, default))
    return config

@pytest.fixture
def large_directory(temp_dir):
    """Create directory with many files for performance testing"""
    large_dir = temp_dir / "large"
    large_dir.mkdir()

    # Create 1000 test files
    for i in range(1000):
        (large_dir / f"file_{i:04d}.txt").write_text(f"content {i}")

    return large_dir

# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "performance: mark test as performance test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
```

## Documentation

### Documentation Types

1. **API Documentation**: Docstrings and API reference
2. **User Documentation**: User manual, tutorials, guides
3. **Developer Documentation**: Architecture, contributing guidelines
4. **Code Comments**: Inline documentation for complex code

### Writing Documentation

#### User Documentation

- **Clear and Concise**: Use simple language and short sentences
- **Step-by-Step**: Provide detailed instructions with examples
- **Visual Aids**: Include screenshots and diagrams where helpful
- **Up-to-Date**: Keep documentation synchronized with code changes

#### API Documentation

- **Complete**: Document all public APIs
- **Examples**: Provide usage examples for complex APIs
- **Type Information**: Include type hints and parameter descriptions
- **Error Conditions**: Document possible exceptions and error conditions

#### Code Documentation

```python
class AdvancedFileManager:
    """Advanced file manager with caching and async operations.

    This class provides high-performance file management capabilities
    with intelligent caching, asynchronous operations, and comprehensive
    error handling.

    Attributes:
        config: Configuration object
        cache: LRU cache for file metadata
        performance_tracker: Performance monitoring

    Example:
        >>> config = Config()
        >>> manager = AdvancedFileManager(config)
        >>> files = await manager.list_directory(Path("/home/user"))
    """

    def __init__(self, config: Config):
        """Initialize the file manager.

        Args:
            config: Configuration object containing settings

        Raises:
            ConfigurationError: If configuration is invalid
        """
        self.config = config
        self.cache = LRUCache(config.get('cache_size', 1000))
        self.performance_tracker = PerformanceTracker()
```

### Building Documentation

```bash
# Install documentation dependencies
pip install -e ".[docs]"

# Build HTML documentation
cd docs/
make html

# Build and serve documentation locally
make livehtml

# Check for documentation issues
make linkcheck
make spelling
```

## Pull Request Process

### Before Submitting

1. **Test Your Changes**: Ensure all tests pass
2. **Update Documentation**: Update relevant documentation
3. **Check Code Quality**: Run linting and formatting tools
4. **Write Good Commit Messages**: Use descriptive commit messages
5. **Rebase if Needed**: Keep a clean commit history

### Commit Message Format

We use conventional commit format:

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `perf`: Performance improvements
- `chore`: Maintenance tasks

**Examples:**

```
feat(ai): add support for local AI models

Add support for Ollama and GPT4All local AI models to provide
offline AI capabilities for privacy-conscious users.

Closes #123

fix(ui): resolve theme switching crash on Windows

The theme switching functionality was causing crashes on Windows
due to path separator issues in theme file loading.

Fixes #456

docs(api): update plugin development guide

Add comprehensive examples and best practices for plugin
development, including security considerations.
```

### Pull Request Template

```markdown
## Description

Brief description of the changes in this PR.

## Type of Change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing

- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] Performance impact assessed

## Checklist

- [ ] Code follows the project's style guidelines
- [ ] Self-review of code completed
- [ ] Code is commented, particularly in hard-to-understand areas
- [ ] Corresponding changes to documentation made
- [ ] No new warnings introduced
- [ ] Tests added that prove the fix is effective or feature works
- [ ] New and existing unit tests pass locally

## Screenshots (if applicable)

Add screenshots to help explain your changes.

## Additional Notes

Any additional information that reviewers should know.
```

### Review Process

1. **Automated Checks**: CI/CD pipeline runs tests and checks
2. **Code Review**: Maintainers review code for quality and design
3. **Feedback**: Address review comments and suggestions
4. **Approval**: Get approval from required reviewers
5. **Merge**: Maintainer merges the PR

### Review Criteria

Reviewers will check for:

- **Functionality**: Does the code work as intended?
- **Code Quality**: Is the code well-written and maintainable?
- **Testing**: Are there adequate tests for the changes?
- **Documentation**: Is documentation updated appropriately?
- **Performance**: Are there any performance implications?
- **Security**: Are there any security concerns?
- **Compatibility**: Does it maintain backward compatibility?

## Community Guidelines

### Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please read and follow our [Code of Conduct](CODE_OF_CONDUCT.md).

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General discussions and questions
- **Discord**: Real-time chat with the community
- **Email**: Direct contact with maintainers

### Getting Help

If you need help:

1. **Check Documentation**: Look through existing documentation
2. **Search Issues**: See if your question has been asked before
3. **Ask in Discussions**: Use GitHub Discussions for questions
4. **Join Discord**: Get real-time help from the community

### Recognition

We value all contributions and recognize contributors in several ways:

- **Contributors File**: All contributors listed in CONTRIBUTORS.md
- **Release Notes**: Significant contributions mentioned in releases
- **Hall of Fame**: Outstanding contributors featured on website
- **Swag**: Contributors may receive LaxyFile merchandise

### Maintainer Responsibilities

Maintainers are responsible for:

- **Code Review**: Reviewing and providing feedback on PRs
- **Issue Triage**: Organizing and prioritizing issues
- **Release Management**: Planning and executing releases
- **Community Management**: Fostering a positive community
- **Documentation**: Maintaining high-quality documentation

Thank you for contributing to LaxyFile! Your contributions help make LaxyFile better for everyone. 🚀
