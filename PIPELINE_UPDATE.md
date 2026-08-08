# BrainCell SDK CI/CD Pipeline Updates

## Summary of Changes

The CI/CD pipeline for `ITL.Braincell.SDK` has been completely modernized to support the plugin architecture strategy and follow ITL enterprise patterns.

## Updated Files

### 1. `.github/workflows/ci.yml` — Main CI Pipeline
**Status:** ✅ Recreated and modernized

**Key improvements:**
- ✅ **Python version**: Fixed to `3.12` only (was testing 3.8-3.12)
  - SDK requires `>=3.12`, so no need to test older versions
- ✅ **Auto-versioning**: New `detect-version` job reads version from `pyproject.toml`
  - Detects if version changed since last tag
  - Sets output for downstream jobs
- ✅ **Branch strategy**: Added support for feature/release/hotfix branches
  - `feature/**` - feature branches
  - `release/**` - release branches (auto-tagged)
  - `hotfix/**` - hotfix branches
  - `main` - stable releases
  - `develop` - development branch
- ✅ **Improved test job**:
  - Conditional pytest (only runs if tests/ directory exists)
  - Coverage reporting with threshold (80%)
  - Better error messaging and formatting
- ✅ **New `package-build` job**:
  - Builds wheel distribution once (reused by publish workflow)
  - Verifies wheel contents
  - Tests installation in clean virtual environment
  - Uploads artifact for publishing
- ✅ **New `tag-release` job**:
  - Auto-creates Git tags on main branch when version changes
  - Creates GitHub Release with automatic changelog link
  - Only runs on main + version-changed condition
- ✅ **Security & quality checks**:
  - Bandit (security linting)
  - Safety (dependency vulnerabilities)
  - pip-audit (known CVEs)
  - All with JSON reports for CI/CD integration

**Jobs and their dependencies:**
```
detect-version
    ↓
├→ test (depends on detect-version)
│   ↓
│   package-build (depends on detect-version + test)
│       ↓
│       tag-release (depends on all three + conditions)
│
└→ lint-and-security (depends on detect-version)
```

### 2. `.github/workflows/publish.yml` — New Publishing Workflow
**Status:** ✅ Created

**Features:**
- Triggered automatically on `release: published` event
- Manual dispatch option with environment selection (pypi / testpypi)
- Auto-detection: pre-release → TestPyPI, stable → PyPI
- OIDC trusted publisher authentication (no API tokens stored)
- Downloads wheel artifact built by CI (no rebuild)
- Publishes to PyPI or TestPyPI based on release type
- Clear output message with installation instructions

**Workflow:**
```
Release published
    ↓
Detect if pre-release or stable
    ↓
Download wheel from CI artifact
    ↓
Publish to PyPI (stable) or TestPyPI (pre-release)
    ↓
Verify upload and display install command
```

### 3. `pyproject.toml` — Project Configuration
**Status:** ✅ Enhanced

**Added sections:**
- `[project.optional-dependencies]` with `dev` extras:
  - Testing: pytest, pytest-asyncio, pytest-cov
  - Type checking: mypy
  - Code formatting: black
  - Linting: ruff
  - Security: bandit, safety, pip-audit
- `[tool.pytest.ini_options]`:
  - asyncio_mode = "auto" for async test support
  - Coverage threshold 80% fail-under
  - Test path configuration
- `[tool.coverage.run]`:
  - Branch coverage enabled
  - Exclude patterns for tests and __init__.py
- `[tool.mypy]`:
  - Strict mode enabled
  - Python 3.12 target
- `[tool.black]`:
  - 120 character line length
  - Python 3.12 target
- `[tool.ruff]`:
  - Standard ITL linting rules (E, F, I, UP, B, SIM, TCH, ANN, RUF)

**Install dev dependencies:**
```bash
pip install -e ".[dev]"
```

## Branch Protection Strategy

For production use, configure these branch protection rules:

**Main branch:**
- ✅ Require PR reviews before merge (1 approver)
- ✅ Require status checks to pass:
  - `test`
  - `package-build`
  - `lint-and-security`
- ✅ Dismiss stale PR approvals
- ✅ Require up-to-date branches

**Develop branch:**
- ✅ Require status checks
- ✅ Allow auto-merge on PR

## Versioning & Release Flow

### Development Flow
```
feature/fix-X → PR to develop
   ↓
   CI runs on develop
   ↓
Merge to develop (no auto-tag)
```

### Release Flow
```
develop → PR to release/vX.Y
   ↓
   Update version in pyproject.toml
   ↓
   Merge to release/vX.Y
   ↓
   CI detects version change
   ↓
   Create tag v.X.Y
   ↓
   GitHub Release created
   ↓
   Manual publish.yml dispatch OR auto-trigger on release:published
   ↓
   Publish to PyPI
```

### Hotfix Flow
```
main → branch hotfix/description
   ↓
   Fix code
   ↓
   Update version in pyproject.toml (e.g., 0.1.0 → 0.1.1)
   ↓
   PR to main
   ↓
   CI runs + auto-tags + publishes
```

## Local Development Setup

```bash
# Clone repo
git clone <repo>
cd ITL.Braincell.SDK

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run type checking
mypy src/itl_braincell_sdk --ignore-missing-imports

# Check formatting
black --check src/ examples/ test_sdk.py

# Build locally
python -m build
```

## Environment Variables & Secrets

### GitHub Secrets Needed
None! Uses OIDC Trusted Publisher for PyPI authentication.

### Optional Configurations
- `PYTHONPATH`: Set to `src/` if needed
- `.env`: Local development (not committed)

## Artifacts

Artifacts created during CI:
- **braincell-sdk-wheel** (30-day retention): `dist/itl_braincell_sdk-*.whl`
- **security-reports** (30-day retention):
  - `bandit-report.json`
  - `safety-report.json`
  - `audit-report.json`

## Next Steps

1. ✅ **Commit changes** to repository
   ```bash
   git add .github/workflows/ci.yml .github/workflows/publish.yml pyproject.toml
   git commit -m "chore: update CI/CD pipeline with auto-versioning and publishing"
   git push
   ```

2. **Create PyPI Trusted Publisher** (if not already set up):
   - Go to PyPI project settings
   - Add Trusted Publisher (GitHub OIDC)
   - Environment name: `pypi`

3. **Create TestPyPI Trusted Publisher** (optional):
   - Go to TestPyPI project settings
   - Add Trusted Publisher (GitHub OIDC)
   - Environment name: `testpypi`

4. **Test release workflow**:
   - Create a release/vX.Y.Z branch
   - Update version in pyproject.toml
   - Create PR to main
   - CI will auto-tag and trigger publish workflow

## References

- [GitHub Actions: Defining outputs for jobs](https://docs.github.com/en/actions/using-jobs/defining-outputs-for-jobs)
- [GitHub Actions: OIDC token](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect)
- [PyPI: Trusted Publishers](https://docs.github.io/en/actions/publishing-packages-with-github-actions/publishing-to-the-python-package-index-using-github-actions)
- [pytest-cov: Coverage configuration](https://pytest-cov.readthedocs.io/en/latest/)
- [mypy: Configuration](https://mypy.readthedocs.io/en/stable/config_file.html)
