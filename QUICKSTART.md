# Quick Start: Azure DevOps Pipeline for ITL.Braincell.SDK

## One-Time Setup (5 minutes)

### 1. Connect Pipeline to Azure DevOps

```bash
# Create the pipeline in Azure DevOps UI
# Project: ITLusions
# Repo: ITL.Braincell.SDK
# Pipeline YAML: azure-pipelines.yml (at repo root)

# Or use Azure CLI:
az pipelines create \
  --name "ITL.Braincell.SDK" \
  --repository ITL.Braincell.SDK \
  --repository-type github \
  --branch main \
  --yml-path azure-pipelines.yml
```

### 2. Set Up Service Connections (for publishing)

In Azure DevOps → Project Settings → Service Connections:

- **PyPI Publishing**:
  ```
  Name: PyPI-Production
  Token: (get from https://pypi.org/account/tokens/)
  ```

- **TestPyPI Publishing**:
  ```
  Name: PyPI-Test
  Token: (get from https://test.pypi.org/account/tokens/)
  ```

- **GitHub Releases** (optional):
  ```
  Name: GitHub-itlusions
  Token: (Personal Access Token with repo scope)
  ```

### 3. Configure Variable Groups (optional)

```powershell
az pipelines variable-group create \
  --name "braincell-sdk-prod" \
  --variables \
    ARTIFACTS_FEED_URL="https://pkgs.dev.azure.com/itlusions/_packaging/itlusions-feed/pypi/upload" \
    COVERAGE_MIN=80
```

---

## Daily Development Workflow

### Feature Development (from `develop`)

```bash
# Create feature branch
git checkout -b feature/my-cool-feature develop

# Make changes, test locally
pytest tests/
ruff check .
mypy src/itl_braincell_sdk --strict

# Commit with semantic message
git commit -m "feat(cells): add new memory cell type for temporal data"

# Push and create pull request
git push -u origin feature/my-cool-feature
# → Create PR in GitHub (base: develop)
```

### Release Management (GitFlow)

#### Scenario A: Release v0.1.0 from develop

```bash
# 1. Create release branch (when develop is stable)
git checkout -b release/v0.1.0 develop
git push -u origin release/v0.1.0

# 2. Azure DevOps builds as v0.1.0rc1 and publishes to TestPyPI
#    Verify: pip install --pre --index-url https://test.pypi.org/simple/ itl-braincell-sdk

# 3. If bugs found, fix on release/v0.1.0 and cherry-pick to develop
git commit -am "fix: resolve issue #123"
git push
# → Pipeline rebuilds as v0.1.0rc2

# 4. Once stable, merge to main
git checkout main
git pull origin main
git merge --no-ff release/v0.1.0
git tag -a v0.1.0 -m "Release v0.1.0: add temporal cells"
git push origin main --tags

# 5. Pipeline automatically publishes to PyPI ✅
#    Verify: pip install itl-braincell-sdk

# 6. Merge back to develop to keep in sync
git checkout develop
git pull origin develop
git merge --no-ff main
git push origin develop

# 7. Delete release branch
git push origin --delete release/v0.1.0
```

#### Scenario B: Hotfix for production bug

```bash
# 1. Create hotfix from main
git checkout -b hotfix/v0.1.1 main
git commit -am "fix: critical security issue in token validation"
git push -u origin hotfix/v0.1.1

# 2. Test and verify (pipeline runs full suite)

# 3. Merge to main and tag
git checkout main
git pull origin main
git merge --no-ff hotfix/v0.1.1
git tag -a v0.1.1 -m "Hotfix v0.1.1: security patch"
git push origin main --tags

# 4. Merge to develop
git checkout develop
git pull origin develop
git merge --no-ff main
git push origin develop

# 5. Delete hotfix branch
git push origin --delete hotfix/v0.1.1
```

---

## Pipeline Behavior Reference

| Event | Branch | Pipeline Runs | Version | Publishes To |
|-------|--------|--------------|---------|------------|
| Push | `develop` | ✅ Build + Test + Security | `0.1.0.dev20240815` | Azure Artifacts |
| Push | `release/v0.1.0` | ✅ Full pipeline | `0.1.0rc{BUILD_ID}` | TestPyPI |
| Push | `main` | ✅ Full pipeline | `0.1.0` | Azure Artifacts |
| Tag `v0.1.0` | (on main) | ✅ Full pipeline | `0.1.0` | **PyPI** ✨ |
| Push | `feature/*` | ✅ Build + Test + Security | (not published) | — |
| PR to `develop` | (any branch) | ✅ Build + Test + Security | (not published) | — |

---

## Monitoring & Troubleshooting

### Check Pipeline Status

```bash
# View all runs
az pipelines build list \
  --project ITLusions \
  --definition-name "ITL.Braincell.SDK" \
  --top 10

# View latest run details
az pipelines build show \
  --project ITLusions \
  --definition-name "ITL.Braincell.SDK" \
  --id $(az pipelines build list --project ITLusions --definition-name "ITL.Braincell.SDK" --top 1 --query "[0].id" -o tsv)

# Stream build logs
az pipelines build show \
  --project ITLusions \
  --definition-name "ITL.Braincell.SDK" \
  --id <BUILD_ID> \
  --open  # Opens in browser
```

### Common Failures

**Test Coverage Below 80%**
```bash
# Run locally to check
pytest tests/ --cov=src/itl_braincell_sdk --cov-report=term-missing
# Fix: Add missing tests or increase existing coverage
# Add to coverage: pytest tests/ --cov-fail-under=80
```

**MyPy Type Check Failed**
```bash
# Identify type issues
mypy src/itl_braincell_sdk --strict --show-error-codes

# Fix: Add type hints or use # type: ignore with justification
```

**Semgrep Security Finding**
```bash
# Review finding in Pipeline > Security tab
# Suppress if false positive: # nosemgrep: <rule-id>
# Example: x = os.environ.get('password')  # nosemgrep: hardcoded-secrets
```

**PyPI Publish Failed**
```bash
# Check token validity
# Verify wheel format: unzip -l dist/*.whl
# Test locally: twine upload --repository testpypi dist/*
```

---

## Environment Variables & Configuration

### Set in Azure DevOps (Pipeline Variables)

```yaml
PyPiToken: ***  # From https://pypi.org/account/tokens/
TestPyPiToken: ***  # From https://test.pypi.org/account/tokens/
GitHubToken: ***  # Personal access token
ArtifactsFeedUrl: https://pkgs.dev.azure.com/itlusions/_packaging/itlusions-feed/pypi/upload
```

### Local Development (.env or shell)

```bash
# Optional: pre-auth for local testing
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-AgEIcH...YOUR_TOKEN
export TWINE_REPOSITORY_URL=https://upload.pypi.org/legacy/

# Test locally
pip install -e ".[dev]"
pytest tests/
twine upload dist/* --skip-existing
```

---

## Additional Commands

```bash
# Check which version would be built
grep -o 'version = ".*"' pyproject.toml

# Generate SBOM locally
pip install cyclonedx-bom
cyclonedx-bom -o requirements.txt --output-format json > sbom.json

# Scan with Semgrep locally
pip install semgrep
semgrep --config .semgrep.yml src/

# Check for secrets locally
pip install detect-secrets
detect-secrets scan --baseline .secrets.baseline src/

# Validate pyproject.toml
python -m build --sdist  # Will fail if pyproject.toml is invalid

# Test package installation locally
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ itl-braincell-sdk
python -c "import itl_braincell_sdk; print(itl_braincell_sdk.__version__)"
```

---

## Learn More

- **Branching**: https://nvie.com/posts/a-successful-git-branching-model/
- **Versioning**: https://semver.org/
- **Python Packaging**: https://packaging.python.org/
- **Azure DevOps Pipelines**: https://docs.microsoft.com/en-us/azure/devops/pipelines/
- **Semgrep Rules**: https://semgrep.dev/r/
- **SBOM Format**: https://cyclonedx.org/

---

**Questions?** See [PIPELINE.md](./PIPELINE.md) for detailed documentation.
