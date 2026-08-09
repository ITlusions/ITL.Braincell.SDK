# Reusable CI Workflow Template

A reusable GitHub Actions workflow for testing, linting, and building Python packages with intelligent artifact naming.

## Features

- **Test** — Import validation and pytest
- **Lint** — black, mypy, ruff, bandit (non-blocking)
- **Build** — Wheel creation with setuptools-scm version detection
- Automatic artifact naming based on branch:
  - `main` → `braincell-sdk-wheel-v1.0.0`
  - `develop` → `braincell-sdk-wheel-v1.0.0-development`
  - `release/**` → `braincell-sdk-wheel-v1.0.0`
  - `feature/**` → `braincell-sdk-wheel-v1.0.0-feat-x123-abc1234`
  - `hotfix/**` → `braincell-sdk-wheel-v1.0.0-hotfix-abc1234`
- Configurable test imports and source directory
- Works across multiple repositories

## Usage in Your Repository

### 1. Create Your CI Workflow

Create `.github/workflows/ci.yml`:

```yaml
name: CI - Test and Validate

on:
  pull_request:
    branches: [ main, develop ]
  push:
    branches: [ main, develop, 'release/**', 'feature/**', 'hotfix/**' ]
  workflow_dispatch:

jobs:
  ci:
    uses: ITlusions/ITL.Braincell.SDK/.github/workflows/ci-reusable.yml@main
    with:
      python_version: '3.12'
      test_import_path: 'your_package.core.config'
      test_import_class: 'Settings'
      src_directory: 'src'
```

### 2. Minimal Setup (With Defaults)

If you want to use defaults:

```yaml
jobs:
  ci:
    uses: ITlusions/ITL.Braincell.SDK/.github/workflows/ci-reusable.yml@main
```

### 3. Configure Your pyproject.toml

Ensure you have dev dependencies defined:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "mypy>=1.8",
    "black>=24.1",
    "ruff>=0.2",
    "bandit>=1.7",
]
```

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `python_version` | `3.12` | Python version for testing and building |
| `test_import_path` | `itl_braincell_sdk.core.config` | Module path for import test |
| `test_import_class` | `Settings` | Class/object name to import from `test_import_path` |
| `src_directory` | `src` | Source directory for linting (black, mypy, ruff, bandit) |

## Workflow Jobs

### Job: Test
- Installs dev dependencies
- Runs import validation test
- Caches pip packages

### Job: Lint
- Runs black (format check only)
- Runs mypy (type checking)
- Runs ruff (code quality)
- Runs bandit (security scan)
- All non-blocking (use `|| true`)

### Job: Build
- Depends on: test + lint
- Detects latest git tag
- Generates artifact name based on branch
- Builds wheel with setuptools-scm
- Uploads artifact (30-day retention)

## Examples

### Example 1: FastAPI Package

```yaml
jobs:
  ci:
    uses: ./.github/workflows/ci-reusable.yml
    with:
      python_version: '3.12'
      test_import_path: 'my_api.core.app'
      test_import_class: 'FastAPIApp'
      src_directory: 'src'
```

### Example 2: Data Package

```yaml
jobs:
  ci:
    uses: ./.github/workflows/ci-reusable.yml
    with:
      python_version: '3.11'
      test_import_path: 'my_data.models'
      test_import_class: 'DataProcessor'
      src_directory: 'src'
```

### Example 3: Minimal (Using All Defaults)

```yaml
name: CI

on:
  push:
    branches: [ main, develop ]

jobs:
  ci:
    uses: ITlusions/ITL.Braincell.SDK/.github/workflows/ci-reusable.yml@main
```

## Artifact Naming

Artifacts are automatically named based on the branch and latest git tag:

```
braincell-sdk-wheel-{tag}[-{branch}[-{short-sha}]]
```

| Branch | Example Artifact Name |
|--------|----------------------|
| `main` | `braincell-sdk-wheel-v1.0.0` |
| `develop` | `braincell-sdk-wheel-v1.0.0-development` |
| `release/v1.1` | `braincell-sdk-wheel-v1.1.0` |
| `feature/auth` | `braincell-sdk-wheel-v1.0.0-feature/auth-abc1234` |
| `hotfix/critical` | `braincell-sdk-wheel-v1.0.0-hotfix/critical-abc1234` |

## Reusing in Other Repositories

### Option A: Copy the Template
```bash
cp .github/workflows/ci-reusable.yml ../other-repo/.github/workflows/
```

Then in `other-repo/.github/workflows/ci.yml`:
```yaml
jobs:
  ci:
    uses: ./.github/workflows/ci-reusable.yml
    with:
      python_version: '3.12'
      test_import_path: 'your_package.core'
      test_import_class: 'YourClass'
      src_directory: 'src'
```

### Option B: Reference from ITL.Braincell.SDK
```yaml
jobs:
  ci:
    uses: ITlusions/ITL.Braincell.SDK/.github/workflows/ci-reusable.yml@main
    with:
      python_version: '3.12'
      test_import_path: 'your_package.core'
      test_import_class: 'YourClass'
      src_directory: 'src'
```

## Troubleshooting

### Import Test Fails

**Cause**: Wrong `test_import_path` or `test_import_class`

**Fix**: Check your package structure:
```bash
python -c "from your_package.core.config import Settings"
# Then use:
# test_import_path: 'your_package.core.config'
# test_import_class: 'Settings'
```

### Lint Checks Fail

**Cause**: Code doesn't match style standards

**Fix**: The workflow is non-blocking, but you can run locally:
```bash
black src/
mypy src/ --ignore-missing-imports
ruff check src/
bandit -r src/
```

### Build Fails

**Cause**: Missing setuptools-scm or incorrect pyproject.toml

**Fix**: Ensure:
```toml
[build-system]
requires = ["setuptools>=68", "wheel", "setuptools-scm>=8"]

[project]
dynamic = ["version"]

[tool.setuptools-scm]
tag_regex = "^v(?P<version>\\d+\\.\\d+\\.\\d+(?:[a-zA-Z0-9\\-\\.]*)?)$"
```

### Artifact Not Uploading

**Cause**: Missing git tags

**Fix**: Create at least one tag:
```bash
git tag v0.0.0
git push origin v0.0.0
```
