# LaxyFile Test Suite

This directory contains the comprehensive test suite for LaxyFile, covering all major components and functionality with unit tests, integration tests, end-to-end tests, and performance benchmarks.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Pytest configuration and shared fixtures
├── run_tests.py               # Test runner script
├── README.md                  # This file
├── unit/                      # Unit tests
│   ├── __init__.py
│   ├── test_advanced_file_manager.py    # File manager tests
│   ├── test_ai_assistant.py             # AI assistant tests
│   ├── test_superfile_ui.py             # UI system tests
│   ├── test_file_operations.py          # File operations tests
│   └── test_plugin_system.py            # Plugin system tests
├── integration/               # Integration tests (to be created)
├── e2e/                      # End-to-end tests (to be created)
└── performance/              # Performance tests (to be created)
```

## Test Categories

### Unit Tests (`tests/unit/`)

Unit tests focus on testing individual components in isolation with comprehensive coverage:

#### `test_advanced_file_manager.py`

- **LRUCache**: Cache implementation with eviction policies
- **AdvancedFileManager**: Enhanced file management with metadata, caching, and performance optimizations
- **File Operations**: Directory listing, file info retrieval, search, and statistics
- **Performance**: Large directory handling, concurrent operations
- **Error Handling**: Permission errors, invalid paths, graceful degradation

#### `test_ai_assistant.py`

- **AIModel & AIModelManager**: Multi-model support and management
- **ResponseCache**: AI response caching with TTL and eviction
- **AdvancedAIAssistant**: Comprehensive file analysis and AI integration
- **Analysis Types**: Content, security, performance, organization analysis
- **Provider Support**: OpenRouter, Ollama, GPT4All, OpenAI, Anthropic
- **Error Handling**: API failures, invalid responses, model unavailability

#### `test_superfile_ui.py`

- **SuperFileUI**: SuperFile-inspired interface with dual panels
- **Layout Management**: Responsive design, panel sizing, theme integration
- **Rendering**: File panels, sidebar, footer, header with rich formatting
- **System Integration**: System info display, progress bars, modal dialogs
- **Theme Support**: Dynamic theme switching and customization
- **Error Handling**: Graceful degradation for rendering errors

#### `test_file_operations.py`

- **ComprehensiveFileOperations**: Copy, move, delete with progress tracking
- **Archive Operations**: ZIP, TAR, 7Z creation and extraction
- **Batch Processing**: Multiple file operations with conflict resolution
- **Progress Tracking**: Real-time progress callbacks and cancellation
- **Platform Support**: Cross-platform file operations
- **Error Handling**: Permission errors, disk full, operation failures

#### `test_plugin_system.py`

- **BasePlugin**: Abstract plugin interface and lifecycle management
- **PluginAPI**: Plugin capabilities, command registration, event handling
- **PluginManager**: Plugin loading, enabling, dependency checking
- **PluginIntegration**: System integration and API setup
- **Dynamic Loading**: Runtime plugin discovery and reloading
- **Error Handling**: Plugin failures, dependency issues

## Test Features

### Comprehensive Coverage

- **Functionality**: All major features and edge cases
- **Error Handling**: Exception scenarios and graceful degradation
- **Performance**: Large data sets and concurrent operations
- **Platform Support**: Cross-platform compatibility testing
- **Integration**: Component interaction and system integration

### Advanced Testing Patterns

- **Async Testing**: Full async/await support with pytest-asyncio
- **Mocking**: Comprehensive mocking of external dependencies
- **Fixtures**: Reusable test data and component setup
- **Parametrization**: Multiple test scenarios with different inputs
- **Performance Testing**: Timing and resource usage validation

### Test Utilities

- **Shared Fixtures**: Common test data and mock objects
- **Helper Functions**: Test utilities for file creation and validation
- **Performance Timers**: Execution time measurement
- **Mock Factories**: Standardized mock object creation

## Running Tests

### Using the Test Runner

```bash
# Run all unit tests
python tests/run_tests.py unit

# Run with verbose output and coverage
python tests/run_tests.py unit -v -c

# Run specific test file
python tests/run_tests.py unit -t test_advanced_file_manager.py

# Run all tests
python tests/run_tests.py all

# Run performance tests
python tests/run_tests.py performance

# Generate comprehensive report
python tests/run_tests.py report
```

### Using Pytest Directly

```bash
# Run all unit tests
pytest tests/unit/

# Run with coverage
pytest tests/unit/ --cov=laxyfile --cov-report=html

# Run specific test
pytest tests/unit/test_advanced_file_manager.py

# Run with markers
pytest tests/ -m "unit"
pytest tests/ -m "performance"
pytest tests/ -m "slow"
```

### Test Markers

Tests are organized with markers for selective execution:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.e2e`: End-to-end tests
- `@pytest.mark.performance`: Performance tests
- `@pytest.mark.slow`: Tests that take more than 1 second

## Test Configuration

### pytest.ini

- Test discovery patterns
- Marker definitions
- Coverage configuration
- Output formatting

### conftest.py

- Shared fixtures for all tests
- Mock object factories
- Test utilities and helpers
- Async test support

## Coverage Goals

The test suite aims for comprehensive coverage:

- **Line Coverage**: >90% for all core components
- **Branch Coverage**: >85% for critical paths
- **Function Coverage**: 100% for public APIs
- **Integration Coverage**: All component interactions

## Performance Testing

Performance tests validate:

- **Response Times**: Operations complete within acceptable timeframes
- **Memory Usage**: Efficient memory management under load
- **Concurrency**: Proper handling of concurrent operations
- **Scalability**: Performance with large datasets

## Continuous Integration

The test suite is designed for CI/CD integration:

- **Fast Execution**: Unit tests complete quickly for rapid feedback
- **Parallel Execution**: Tests can run in parallel for efficiency
- **Deterministic**: Consistent results across different environments
- **Comprehensive Reporting**: Detailed test results and coverage reports

## Adding New Tests

When adding new functionality:

1. **Create Unit Tests**: Test individual components in isolation
2. **Add Integration Tests**: Test component interactions
3. **Include Error Cases**: Test failure scenarios and edge cases
4. **Add Performance Tests**: Validate performance requirements
5. **Update Documentation**: Document new test patterns and utilities

### Test Naming Conventions

- Test files: `test_<component_name>.py`
- Test classes: `Test<ComponentName>`
- Test methods: `test_<functionality>_<scenario>`
- Fixtures: `<component_name>_<type>` (e.g., `file_manager`, `mock_config`)

### Test Organization

- Group related tests in classes
- Use descriptive test names
- Include docstrings for complex tests
- Separate setup, execution, and assertion phases
- Use fixtures for common test data

## Dependencies

The test suite requires:

- **pytest**: Core testing framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pytest-html**: HTML test reports
- **pytest-benchmark**: Performance testing
- **pytest-mock**: Enhanced mocking capabilities

Install with:

```bash
pip install pytest pytest-asyncio pytest-cov pytest-html pytest-benchmark pytest-mock
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure LaxyFile is in Python path
2. **Async Test Failures**: Check pytest-asyncio configuration
3. **Mock Issues**: Verify mock object setup and patching
4. **Performance Test Failures**: Adjust timing thresholds for environment
5. **Coverage Issues**: Check file paths and exclusion patterns

### Debug Mode

Run tests with debugging:

```bash
pytest tests/unit/ -v -s --tb=long --pdb
```

### Test Isolation

Ensure tests are isolated:

- Use temporary directories for file operations
- Clean up resources in teardown
- Avoid global state modifications
- Use fresh mock objects for each test

## Future Enhancements

Planned improvements:

- **Integration Tests**: Component interaction testing
- **End-to-End Tests**: Full workflow validation
- **Property-Based Testing**: Hypothesis-based testing
- **Mutation Testing**: Test quality validation
- **Visual Testing**: UI component visual regression testing
