# LaxyFile Release Checklist

This checklist ensures a smooth and complete release process for LaxyFile.

## Pre-Release Preparation

### Code Quality

- [ ] All tests pass (`pytest tests/`)
- [ ] Code coverage is acceptable (>80%)
- [ ] No critical security vulnerabilities
- [ ] Performance benchmarks meet requirements
- [ ] Documentation is up to date

### Version Management

- [ ] Version number updated in `laxyfile/__init__.py`
- [ ] Version number updated in `pyproject.toml`
- [ ] Version number updated in `setup.py`
- [ ] CHANGELOG.md updated with new version
- [ ] Release notes prepared

### Dependencies

- [ ] All dependencies are pinned to stable versions
- [ ] requirements.txt is up to date
- [ ] No unused dependencies
- [ ] License compatibility checked

## Build and Test

### Local Testing

- [ ] Test on Linux (Ubuntu/Debian)
- [ ] Test on macOS (latest version)
- [ ] Test on Windows 10/11
- [ ] Test with Python 3.8, 3.9, 3.10, 3.11, 3.12
- [ ] Test installation from source
- [ ] Test installation from wheel

### Package Building

- [ ] Source distribution builds successfully
- [ ] Wheel distribution builds successfully
- [ ] Standalone executables build for all platforms
- [ ] Linux packages (deb, rpm) build successfully
- [ ] macOS app bundle builds successfully
- [ ] Windows installer builds successfully

### Quality Assurance

- [ ] All built packages install correctly
- [ ] Application starts without errors
- [ ] Core functionality works in all packages
- [ ] AI features work with API key
- [ ] Themes and UI render correctly
- [ ] File operations work correctly

## Release Deployment

### PyPI Deployment

- [ ] Test PyPI deployment successful
- [ ] Production PyPI deployment successful
- [ ] Package appears correctly on PyPI
- [ ] Installation via pip works: `pip install laxyfile`

### GitHub Release

- [ ] Git tag created: `git tag -a v1.0.0 -m "Release 1.0.0"`
- [ ] Tag pushed to GitHub: `git push origin v1.0.0`
- [ ] GitHub release created with assets
- [ ] Release notes published
- [ ] Checksums file uploaded

### Package Managers

- [ ] Homebrew formula updated
- [ ] Chocolatey package updated
- [ ] AUR package updated (if applicable)
- [ ] Snap package updated (if applicable)

## Post-Release

### Documentation

- [ ] README.md updated with new version
- [ ] Documentation website updated
- [ ] API documentation regenerated
- [ ] Tutorial videos updated (if needed)

### Communication

- [ ] Release announcement on GitHub
- [ ] Social media announcement
- [ ] Community forums notification
- [ ] Email newsletter (if applicable)

### Monitoring

- [ ] Monitor PyPI download statistics
- [ ] Monitor GitHub release downloads
- [ ] Check for user-reported issues
- [ ] Monitor error tracking (if implemented)

## Rollback Plan

If critical issues are discovered after release:

### Immediate Actions

- [ ] Document the issue clearly
- [ ] Assess impact and severity
- [ ] Decide on rollback vs. hotfix

### PyPI Rollback

- [ ] Contact PyPI support to remove package
- [ ] Or release a new version with fixes

### GitHub Rollback

- [ ] Delete the release
- [ ] Delete the git tag
- [ ] Push corrected version

### Communication

- [ ] Notify users of the issue
- [ ] Provide workarounds if available
- [ ] Announce fix timeline

## Release Automation

### Scripts Used

- [ ] `scripts/build_release.py` - Build all packages
- [ ] `scripts/deploy_pypi.py` - Deploy to PyPI
- [ ] `scripts/create_changelog.py` - Generate changelog
- [ ] `scripts/deploy_all.py` - Complete deployment orchestration

### GitHub Actions

- [ ] Release workflow triggered
- [ ] All platform builds successful
- [ ] Artifacts uploaded correctly
- [ ] Tests pass on all platforms

## Version-Specific Checklist (v1.0.0)

### New Features to Highlight

- [ ] SuperFile-inspired interface
- [ ] AI-powered assistant
- [ ] Advanced media support
- [ ] 5 beautiful themes
- [ ] Cross-platform compatibility

### Breaking Changes

- [ ] None (initial release)

### Migration Guide

- [ ] Not applicable (initial release)

## Sign-off

### Development Team

- [ ] Lead Developer approval: ******\_\_\_\_******
- [ ] QA Engineer approval: ******\_\_\_\_******
- [ ] Documentation approval: ******\_\_\_\_******

### Release Manager

- [ ] Final approval: ******\_\_\_\_******
- [ ] Release date: ******\_\_\_\_******
- [ ] Release completed: ******\_\_\_\_******

---

## Quick Release Commands

```bash
# 1. Run tests
pytest tests/ -v

# 2. Build packages
python scripts/build_release.py

# 3. Deploy to Test PyPI
python scripts/deploy_pypi.py --test

# 4. Deploy to Production PyPI
python scripts/deploy_pypi.py

# 5. Create GitHub release
git tag -a v1.0.0 -m "Release 1.0.0"
git push origin v1.0.0

# 6. Complete deployment
python scripts/deploy_all.py 1.0.0

# 7. Generate changelog
python scripts/create_changelog.py --version 1.0.0
```

## Emergency Contacts

- **PyPI Support**: https://pypi.org/help/
- **GitHub Support**: https://support.github.com/
- **Lead Developer**: [contact information]
- **Release Manager**: [contact information]

---

**Note**: This checklist should be reviewed and updated for each release to ensure it remains current and comprehensive.
