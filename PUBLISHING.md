# Publishing toon_format to PyPI

This guide explains how to publish the toon_format package to PyPI (Python Package Index).

## Prerequisites

### 1. PyPI Accounts

Create accounts on both platforms:

- **TestPyPI** (for testing): https://test.pypi.org/account/register/
- **PyPI** (production): https://pypi.org/account/register/

### 2. GitHub Environments

The publish workflow uses GitHub environments with trusted publishing (no API tokens needed!).

#### Set up environments in GitHub:

1. Go to your repository Settings > Environments
2. Create two environments:
   - `testpypi` - for TestPyPI releases
   - `pypi` - for production PyPI releases
3. For each environment, configure:
   - **Deployment protection rules** (optional but recommended):
     - Required reviewers (for production releases)
     - Wait timer (optional delay before deployment)

#### Configure Trusted Publishers:

**For TestPyPI:**
1. Log in to https://test.pypi.org
2. Go to Account Settings > Publishing
3. Add a new pending publisher:
   - PyPI Project Name: `toon_format`
   - Owner: `toon-format`
   - Repository: `toon-python`
   - Workflow: `publish.yml`
   - Environment: `testpypi`

**For PyPI:**
1. Log in to https://pypi.org
2. Go to Account Settings > Publishing
3. Add a new pending publisher:
   - PyPI Project Name: `toon_format`
   - Owner: `toon-format`
   - Repository: `toon-python`
   - Workflow: `publish.yml`
   - Environment: `pypi`

> Note: After the first successful publish, the project will be registered and future publishes will use the same trusted publisher configuration.

## Release Process

### Step 1: Prepare the Release

1. **Update version number** in two places:
   - `pyproject.toml` (line 3): `version = "X.Y.Z"`
   - `src/toon_format/__init__.py` (line 28): `__version__ = "X.Y.Z"`

2. **Update changelog** (if exists) or create release notes

3. **Run tests locally**:
   ```bash
   uv run pytest
   uv run ruff check .
   uv run mypy src/toon_format
   ```

4. **Build and test locally**:
   ```bash
   # Clean previous builds
   rm -rf dist/ build/ *.egg-info

   # Build the package
   python -m build

   # Verify the package contents
   python -m zipfile -l dist/toon_format-X.Y.Z-py3-none-any.whl

   # Test installation in a clean environment
   python -m venv test_env
   test_env/bin/pip install dist/toon_format-X.Y.Z-py3-none-any.whl
   test_env/bin/python -c "import toon_format; print(toon_format.__version__)"
   rm -rf test_env
   ```

### Step 2: Commit and Tag

1. **Commit version changes**:
   ```bash
   git add pyproject.toml src/toon_format/__init__.py
   git commit -m "Bump version to X.Y.Z"
   ```

2. **Create and push tag**:
   ```bash
   git tag -a vX.Y.Z -m "Release version X.Y.Z"
   git push origin main
   git push origin vX.Y.Z
   ```

### Step 3: Test on TestPyPI (Recommended)

Before publishing to production PyPI, test on TestPyPI:

1. Go to GitHub Actions: https://github.com/toon-format/toon-python/actions
2. Select the "Publish to PyPI" workflow
3. Click "Run workflow"
4. Select branch: `main` (or the tag `vX.Y.Z`)
5. Click "Run workflow"
   - Note: Manual workflow dispatch automatically publishes to TestPyPI

6. **Verify the TestPyPI upload**:
   - Check the package: https://test.pypi.org/project/toon_format/
   - Test installation:
     ```bash
     pip install --index-url https://test.pypi.org/simple/ toon_format
     ```

### Step 4: Publish to PyPI

**Automatic (via GitHub Release)**

1. Go to https://github.com/toon-format/toon-python/releases/new
2. Select the tag you created: `vX.Y.Z`
3. Release title: `Version X.Y.Z`
4. Description: Add release notes and changelog
5. Click "Publish release"
6. The GitHub Action will automatically build and publish to PyPI

### Step 5: Verify the Release

1. **Check PyPI**: https://pypi.org/project/toon_format/
2. **Test installation**:
   ```bash
   pip install toon_format
   python -c "import toon_format; print(toon_format.__version__)"
   ```
3. **Update README badge** (optional):
   ```markdown
   [![PyPI version](https://badge.fury.io/py/toon_format.svg)](https://pypi.org/project/toon_format/)
   ```

## Troubleshooting

### Build fails with "metadata missing"

This is usually a configuration issue in `pyproject.toml`. Verify:
- All required fields are present (name, version, description, etc.)
- Project URLs are properly formatted
- Author email is valid

### Trusted publishing fails

If the trusted publisher configuration fails:
1. Verify the environment name matches exactly
2. Check that the repository owner and name are correct
3. Ensure the workflow file path is correct (`publish.yml`)
4. Make sure the PyPI project name is available or already claimed by you

### Package already exists on PyPI

PyPI doesn't allow overwriting published versions. You must:
1. Increment the version number
2. Create a new tag
3. Publish the new version

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):

- **MAJOR version** (X.0.0): Incompatible API changes
- **MINOR version** (0.X.0): New functionality, backward compatible
- **PATCH version** (0.0.X): Bug fixes, backward compatible

### Agreed Roadmap (from Discussion #18):

- **0.8.x** - Initial code set, tests, documentation, migration from toon-llm
- **0.9.x** - Serializer, spec compliance, publishing to PyPI (test and prod)
- **1.0.0-rc.x** - Production readiness candidates
- **1.0.0** - Official stable release 🎉

Examples:
- `0.9.0-beta.1` - First beta release for testing
- `0.9.0-beta.2` - Second beta with fixes
- `0.9.0` - First minor release with new features
- `1.0.0-rc.1` - Release candidate
- `1.0.0` - First stable release

## Checklist

Before each release, verify:

- [ ] All tests pass (`uv run pytest`)
- [ ] Linting passes (`uv run ruff check .`)
- [ ] Type checking passes (`uv run mypy src/toon_format`)
- [ ] Version updated in `pyproject.toml` and `src/toon_format/__init__.py`
- [ ] Changes committed and pushed to `main`
- [ ] Git tag created and pushed
- [ ] Package tested on TestPyPI (optional but recommended)
- [ ] GitHub Release created
- [ ] Package verified on PyPI
- [ ] Installation tested from PyPI

## References

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Trusted Publishing Guide](https://docs.pypi.org/trusted-publishers/)
- [GitHub Actions Publishing](https://packaging.python.org/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
- [TOON Format Specification](https://github.com/toon-format/spec)
