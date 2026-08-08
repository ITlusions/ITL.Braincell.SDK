# PyPI Configuration for Trusted Publishing

To enable secure publishing to PyPI without storing API tokens, follow these steps:

## 1. Configure PyPI Trusted Publishing

### For Production PyPI (pypi.org)

1. Go to https://pypi.org/manage/account/publishing/
2. Add a new trusted publisher with these details:
   - **PyPI Project Name**: `itl-controlplane-sdk`
   - **Owner**: `ITlusions` (or your GitHub organization)
   - **Repository name**: `ITL.ControlPanel.SDK`
   - **Workflow filename**: `build-publish.yml`
   - **Environment name**: `production`

### For Test PyPI (test.pypi.org)

1. Go to https://test.pypi.org/manage/account/publishing/
2. Add a new trusted publisher with these details:
   - **PyPI Project Name**: `itl-controlplane-sdk`
   - **Owner**: `ITlusions` (or your GitHub organization)
   - **Repository name**: `ITL.ControlPanel.SDK`
   - **Workflow filename**: `build-publish.yml`
   - **Environment name**: `staging`

## 2. GitHub Repository Settings

### Environments

Create these environments in your repository settings:

1. **staging**:
   - No approval required
   - Used for Test PyPI publishing
   - Can be used for all branches

2. **production**:
   - Require approval from maintainers (recommended)
   - Used for production PyPI publishing
   - Restrict to main branch and version tags

### Secrets (Alternative to Trusted Publishing)

If you prefer using API tokens instead of trusted publishing:

- `PYPI_TOKEN`: Your production PyPI API token
- `TEST_PYPI_TOKEN`: Your Test PyPI API token
- `TEAMS_WEBHOOK`: (Optional) Microsoft Teams webhook URL

## 3. Package Registration

Before first publication, register your package:

1. Create account on https://pypi.org/
2. Create account on https://test.pypi.org/
3. Reserve the package name `itl-controlplane-sdk`

## 4. First Release

1. Update version in `pyproject.toml`
2. Create and push a version tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
3. The pipeline will automatically publish to both Test PyPI and PyPI

## 5. Verification

After successful publication:

- **Test PyPI**: https://test.pypi.org/project/itl-controlplane-sdk/
- **Production PyPI**: https://pypi.org/project/itl-controlplane-sdk/

## 6. Installation Commands

Users can install your package with:

```bash
# Latest version
pip install itl-controlplane-sdk

# Specific version
pip install itl-controlplane-sdk==1.0.0

# From Test PyPI (for testing)
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ itl-controlplane-sdk
```