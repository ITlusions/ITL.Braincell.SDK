# Reusable Publish Workflow Template

A reusable GitHub Actions workflow for publishing Python packages to PyPI and TestPyPI with intelligent branch detection.

## Features

- Automatic publishing based on branch patterns:
  - `feature/**` → TestPyPI (prerelease)
  - `hotfix/**` → PyPI (stable)
  - GitHub Release (prerelease flag) → TestPyPI
  - GitHub Release (stable) → PyPI
- OIDC-based Trusted Publisher authentication
- Configurable Python version and PyPI URLs
- Works across multiple repositories

## Usage in Your Repository

### 1. Create Your Publish Workflow

Create `.github/workflows/publish.yml`:

```yaml
name: Publish

on:
  release:
    types: [ published ]
  push:
    branches: [ 'feature/**', 'hotfix/**' ]
  workflow_dispatch:
    inputs:
      publish_target:
        description: 'Publish target'
        required: false
        default: 'auto'
        type: choice
        options:
          - auto
          - testpypi
          - pypi

jobs:
  publish:
    uses: ITlusions/ITL.Braincell.SDK/.github/workflows/publish-reusable.yml@main
    with:
      python_version: '3.12'
      testpypi_url: 'https://test.pypi.org/legacy/'
      pypi_url: 'https://upload.pypi.org/legacy/'
    secrets: inherit
```

### 2. Set Up Trusted Publishers

For **PyPI**:
1. Go to https://pypi.org/manage/account/publishing/
2. Add trusted publisher:
   - GitHub repository: `owner/repo`
   - Workflow name: `publish.yml` or `Publish`
   - Environment: `pypi`

For **TestPyPI**:
1. Go to https://test.pypi.org/manage/account/publishing/
2. Add trusted publisher (same steps)

### 3. Ensure Your pyproject.toml Uses setuptools-scm

```toml
[build-system]
requires = ["setuptools>=68", "wheel", "setuptools-scm>=8"]
build-backend = "setuptools.build_meta"

[project]
name = "your-package"
dynamic = ["version"]

[tool.setuptools-scm]
write_to = "src/your_package/_version.py"
write_to_template = '__version__ = "{version}"\n'
tag_regex = "^v(?P<version>\\d+\\.\\d+\\.\\d+(?:[a-zA-Z0-9\\-\\.]*)?)$"
```

## Workflow Triggers

| Trigger | Branch | Action |
|---------|--------|--------|
| **Push** | `feature/**` | Build & publish to TestPyPI |
| **Push** | `hotfix/**` | Build & publish to PyPI |
| **GitHub Release** | any | Publish to PyPI (or TestPyPI if prerelease) |
| **Manual dispatch** | any | Build & publish to selected target |

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `python_version` | `3.12` | Python version to use for build |
| `testpypi_url` | `https://test.pypi.org/legacy/` | TestPyPI repository URL |
| `pypi_url` | `https://upload.pypi.org/legacy/` | PyPI repository URL |

## Examples

### Publish Feature to TestPyPI (Automatic)

```bash
git checkout -b feature/new-feature
# Make changes
git push origin feature/new-feature
# Workflow automatically triggers → publishes to TestPyPI
```

### Publish Hotfix to PyPI (Automatic)

```bash
git checkout -b hotfix/critical-bug
# Make changes
git push origin hotfix/critical-bug
# Workflow automatically triggers → publishes to PyPI
```

### Create Stable Release

```bash
git tag v1.0.0
git push origin v1.0.0
gh release create v1.0.0 --title "v1.0.0" --notes "Release notes"
# Workflow automatically triggers → publishes to PyPI
```

### Create Prerelease

```bash
git tag v1.0.0-rc1
git push origin v1.0.0-rc1
gh release create v1.0.0-rc1 --title "v1.0.0-rc1" --prerelease
# Workflow automatically triggers → publishes to TestPyPI
```

## Reusing in Other Repositories

To use this template in another repository:

1. **Option A: Copy the template**
   - Copy `publish-reusable.yml` to your repo's `.github/workflows/`
   - Create your own `publish.yml` that calls it

2. **Option B: Reference from ITL.Braincell.SDK**
   ```yaml
   uses: ITlusions/ITL.Braincell.SDK/.github/workflows/publish-reusable.yml@main
   ```
   (Requires public access to the repository)

## Troubleshooting

### "invalid-publisher" Error

**Cause**: Missing `environment: name: pypi` in your workflow job

**Fix**: Add to your job definition:
```yaml
jobs:
  publish:
    environment:
      name: pypi
```

### Package Not Building

**Cause**: Missing setuptools-scm dependency

**Fix**: Add to `[build-system].requires`:
```toml
requires = ["setuptools>=68", "wheel", "setuptools-scm>=8"]
```

### Version Mismatch

**Cause**: pyproject.toml has hardcoded version instead of `dynamic = ["version"]`

**Fix**: Remove `version = "X.Y.Z"` from `[project]` and add `dynamic = ["version"]`
