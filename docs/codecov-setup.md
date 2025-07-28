# Codecov Integration Setup Guide

This guide explains how to set up and configure Codecov for LaxyFile's code coverage reporting.

## Overview

Codecov is integrated into LaxyFile's CI/CD pipeline to provide:

- **Automated coverage reporting** for all pull requests and commits
- **Coverage trends** and historical data
- **Component-based coverage** tracking for different parts of the codebase
- **Coverage status checks** to maintain code quality

## Setup Steps

### 1. Codecov Account Setup

1. **Sign up for Codecov**: Go to [codecov.io](https://codecov.io) and sign up with your GitHub account
2. **Add Repository**: Add the `swadhinbiswas/laxyfile` repository to your Codecov dashboard
3. **Get Upload Token**: Copy the repository upload token from Codecov dashboard

### 2. GitHub Secrets Configuration

Add the following secrets to your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add new repository secret:
   - **Name**: `CODECOV_TOKEN`
   - **Value**: Your Codecov upload token from step 1.3

### 3. Configuration Files

The following files are already configured in the repository:

#### `codecov.yml` - Main Configuration

```yaml
coverage:
  precision: 2
  round: down
  range: "70...100"

  status:
    project:
      default:
        target: 80% # Overall project coverage target
        threshold: 1% # Allow 1% decrease
    patch:
      default:
        target: 75% # New code coverage target
        threshold: 2% # Allow 2% decrease for patches
```

#### Component Coverage Targets

- **Core Components**: 85% coverage target
- **File Operations**: 85% coverage target
- **Utilities**: 85% coverage target
- **AI Components**: 80% coverage target
- **Plugin System**: 80% coverage target
- **UI Components**: 75% coverage target
- **Preview System**: 75% coverage target

### 4. GitHub Actions Integration

Coverage is automatically collected and uploaded in two workflows:

#### Test Workflow (`.github/workflows/test.yml`)

- Runs on every push and pull request
- Tests across multiple OS and Python versions
- Uploads coverage with detailed flags

#### Release Workflow (`.github/workflows/release.yml`)

- Runs on tagged releases
- Ensures coverage before deployment
- Uploads release-specific coverage data

## Coverage Reports

### Viewing Coverage

1. **Codecov Dashboard**: Visit your repository on codecov.io
2. **GitHub PR Comments**: Codecov automatically comments on pull requests
3. **GitHub Status Checks**: Coverage status appears in PR checks
4. **Local HTML Reports**: Generated in `htmlcov/` directory after running tests

### Coverage Flags

The integration uses several flags to organize coverage data:

- `unittests`: Unit test coverage
- `integration`: Integration test coverage
- `performance`: Performance test coverage
- `release`: Release build coverage
- OS flags: `ubuntu-latest`, `macos-latest`, `windows-latest`
- Python version flags: `python3.8`, `python3.9`, etc.

### Understanding Coverage Reports

#### Project Coverage

- **Overall percentage** of code covered by tests
- **Trend analysis** showing coverage changes over time
- **File-by-file breakdown** of coverage percentages

#### Patch Coverage

- **New code coverage** for pull requests
- **Line-by-line analysis** of what's covered
- **Suggestions** for improving coverage

#### Component Coverage

- **Module-specific targets** for different parts of the codebase
- **Individual status checks** for each component
- **Focused improvement** recommendations

## Best Practices

### Writing Tests for Coverage

1. **Aim for 80%+ overall coverage**
2. **Focus on critical paths** first
3. **Test edge cases** and error conditions
4. **Mock external dependencies** appropriately

### Improving Coverage

1. **Identify uncovered lines** using coverage reports
2. **Add tests for missing scenarios**
3. **Remove dead code** that can't be covered
4. **Use `# pragma: no cover`** for intentionally uncovered code

### Coverage Exclusions

The following are excluded from coverage:

- Test files (`tests/`)
- Documentation (`docs/`)
- Build scripts (`scripts/`)
- Package metadata (`setup.py`, `__main__.py`)
- Generated files (`build/`, `dist/`)

## Troubleshooting

### Common Issues

#### Coverage Not Uploading

- Check that `CODECOV_TOKEN` is set correctly
- Verify the coverage.xml file is generated
- Check GitHub Actions logs for upload errors

#### Low Coverage Warnings

- Review uncovered lines in Codecov dashboard
- Add tests for critical uncovered code
- Consider adjusting coverage targets if appropriate

#### Status Check Failures

- Check if coverage dropped below thresholds
- Review the specific component that failed
- Add tests to bring coverage back up

### Getting Help

1. **Codecov Documentation**: [docs.codecov.com](https://docs.codecov.com)
2. **GitHub Issues**: Report integration issues
3. **Coverage Reports**: Use detailed reports to identify gaps

## Monitoring and Maintenance

### Regular Tasks

1. **Review coverage trends** monthly
2. **Update coverage targets** as codebase matures
3. **Clean up excluded files** list periodically
4. **Monitor component coverage** for balance

### Coverage Goals

- **Short-term**: Maintain 80%+ overall coverage
- **Medium-term**: Achieve 85%+ for core components
- **Long-term**: Establish 90%+ coverage for critical paths

## Integration Benefits

With Codecov properly configured, you get:

✅ **Automated coverage reporting** on every commit
✅ **Pull request coverage analysis** with detailed feedback
✅ **Historical coverage tracking** and trend analysis
✅ **Component-based coverage goals** for focused improvement
✅ **Integration with GitHub status checks** for quality gates
✅ **Visual coverage reports** with line-by-line analysis

This ensures LaxyFile maintains high code quality and comprehensive test coverage across all components and platforms.
