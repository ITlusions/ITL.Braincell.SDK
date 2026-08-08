# Azure DevOps Pipeline — ITL.Braincell.SDK

## Overview

This is a **production-grade Python package pipeline** for ITL.Braincell.SDK using GitFlow branching strategy.

```
trigger: main, develop, release/*, hotfix/*, tags (v*.*.*)
  ↓
Build & Test (Python 3.12, ruff, mypy, pytest ≥80% coverage)
  ↓
Security Scan (Semgrep SAST, pip-audit, credential-scan, SBOM)
  ↓
Publish Artifacts
  ├─ main + tags → PyPI (production)
  ├─ release/* → TestPyPI (pre-release)
  └─ develop → Azure Artifacts (internal)
```

---

## Pipeline Flow

### Branch Behavior

| Branch | Trigger | Version | Publish Target | Approval |
|--------|---------|---------|-----------------|----------|
| `develop` | Push | dev | Azure Artifacts | None |
| `feature/*` | PR to develop | — | (skip) | Code review only |
| `release/v*.*.* ` | Push | rc | TestPyPI | None (auto) |
| `main` | Merge from release | prod | PyPI | Approval required |
| `hotfix/*` | Push | patch | Azure Artifacts | Code review |
| `v*.*.*` tag | Git tag | prod | PyPI + Release | Auto (tag trigger) |

### Versioning Strategy

**Automatic from Git tags** (SemVer 2.0):

```bash
# Development build (develop branch)
0.1.0.dev20240815

# Release candidate (release/v0.1.0 branch)
0.1.0rc1

# Production (main branch or v0.1.0 tag)
0.1.0

# Post-release hotfix
0.1.1
```

**How it works:**
1. Code lands on `develop` → pipeline builds `0.1.0.dev*`
2. Create `release/v0.1.0` branch → pipeline builds `0.1.0rc*` (pre-release)
3. Merge to `main` + tag `v0.1.0` → pipeline builds `0.1.0` (stable) → publish to PyPI
4. Hotfixes on `hotfix/` branches are tagged and merged back

---

## Setup Instructions

### 1. Prerequisites

- **Azure DevOps Project**: https://dev.azure.com/itlusions/
- **Service Connections**:
  - `PyPI-Production`: Personal API token for PyPI (https://pypi.org)
  - `PyPI-Test`: Personal API token for TestPyPI (https://test.pypi.org)
  - `Azure-Artifacts-Feed`: Already configured via REGISTRY_URL
- **GitHub Branch Protection** (optional but recommended):
  - Require pull request review
  - Require status check to pass (`Azure DevOps / azure-pipelines`)
  - Dismiss stale reviews on new commits

### 2. Configure Azure DevOps Project

1. **Go to Pipelines > Environments**
   - Create environment: `Release` (for approval gates on `main`)
   - Create environment: `Production` (for PyPI publishing)

2. **Go to Pipelines > Library > Secure Files**
   - Upload `.pypirc` with PyPI token:
     ```ini
     [distutils]
     index-servers =
         pypi
         testpypi
     
     [pypi]
     repository: https://upload.pypi.org/legacy/
     username: __token__
     password: pypi-AgEIcH...YOUR_TOKEN_HERE
     
     [testpypi]
     repository: https://test.pypi.org/legacy/
     username: __token__
     password: pypi-AgEIcH...YOUR_TEST_TOKEN_HERE
     ```

3. **Go to Project Settings > Permissions**
   - Grant `itlusions-feed` feed access to build service account

### 3. Local Git Setup

```bash
# Ensure branch protection is configured
git clone https://github.com/ITlusions/ITL.Braincell.SDK.git
cd ITL.Braincell.SDK

# Create develop branch if not present
git checkout -b develop origin/develop || git checkout develop

# Create your feature branch
git checkout -b feature/my-feature develop

# After work, push and create PR to develop
git push -u origin feature/my-feature
```

---

## Usage: Release Workflow (GitFlow)

### Creating a Release (RC → Production)

```bash
# 1. Update version in pyproject.toml (or let pipeline auto-detect)
# git commit -am "chore: version 0.1.0"

# 2. Create release branch from develop
git checkout -b release/v0.1.0 develop
git push -u origin release/v0.1.0

# 3. Azure DevOps Pipeline runs:
#    - Build & Test (Python 3.12)
#    - Security Scan (Semgrep, pip-audit, SBOM)
#    - Publish to TestPyPI as v0.1.0rc1

# 4. Test the release candidate
pip install --pre --index-url https://test.pypi.org/simple/ itl-braincell-sdk

# 5. Fix any bugs on release/v0.1.0, cherry-pick to main if needed
# Once stable, merge to main:

git checkout main
git pull origin main
git merge --no-ff release/v0.1.0

# 6. Tag the release (triggers PyPI publish)
git tag -a v0.1.0 -m "Release v0.1.0"
git push origin main --tags

# 7. Create GitHub Release (optional, automated by pipeline)
# Merge release branch back to develop:
git checkout develop
git pull origin develop
git merge --no-ff main
git push origin develop

# 8. Delete release branch
git push origin --delete release/v0.1.0
```

### Publishing to PyPI (Automatic)

When you tag `v0.1.0` on `main`:
- Pipeline detects the tag
- Builds distribution (wheel + sdist)
- Runs full security scan
- Publishes to PyPI automatically (no manual approval needed for stable versions)
- Creates GitHub Release with release notes

---

## Security Scanning Details

### SAST (Static Analysis Security Testing)
- **Semgrep**: Security rules for Python (OWASP, CWE)
- **Ruff**: Code quality (E/F/I/UP/B/SIM)
- **MyPy (strict)**: Type safety

### Dependency Scanning
- **pip-audit**: Checks for known CVEs in dependencies
- **Pip-requirements**: Resolves transitive dependencies

### Software Bill of Materials (SBOM)
- **CycloneDX**: SBOM in JSON format
- Uploaded as build artifact for compliance audits
- Published with releases

### Secrets Detection
- **Credential Scanner**: Detects hardcoded credentials, API keys, tokens
- Blocks commit if secrets are found

### Compliance Mapping
- **NIST CSF**: IA-2 (auth), SC-7 (security boundaries), SC-30 (monitoring)
- **ISO 27001**: A.8.3 (technical controls), A.12.2 (vulnerability mgmt)

---

## Pipeline Stages Explained

### Stage 1: Build & Test
```yaml
Job: PythonBuild
  Steps:
    1. Install Python 3.12
    2. Install dependencies (pip install -e .[dev])
    3. Ruff lint + format check
    4. MyPy strict type checking
    5. Pytest with coverage ≥80%
    6. Build wheel distribution
  Artifacts: python-wheel (dist/)
  Failure: Blocks downstream stages
```

**Pass Criteria:**
- ✅ All linting rules pass
- ✅ Type checking passes (strict mode)
- ✅ All tests pass
- ✅ Coverage ≥80%

### Stage 2: Security Scan
```yaml
Job: SecurityScan
  Steps:
    1. Semgrep SAST (Python security rules)
    2. pip-audit (dependency CVEs)
    3. Credential scanner (secret detection)
    4. CycloneDX SBOM generation
  Artifacts: sbom.json, security-report.json
  Failure: Blocks publishing stages
```

**Pass Criteria:**
- ✅ No critical Semgrep findings
- ✅ No known CVEs in dependencies (or acceptable risk)
- ✅ No hardcoded secrets detected
- ✅ SBOM generated successfully

### Stage 3: Publish
```yaml
Condition: Branch is main, release/*, or tag is v*.*.*

Jobs:
  - PublishToAzureArtifacts (all branches)
  - PublishToTestPyPI (release/* only)
  - PublishToPyPI (main + tags only)
  - CreateGitHubRelease (tags only)
```

---

## Updating Dependencies

1. **Update pyproject.toml:**
   ```bash
   pip-audit  # Check current dependencies
   pip index versions fastapi  # Check latest version
   ```

2. **Update in pyproject.toml** and run tests:
   ```bash
   pip install -e .[dev]
   pytest tests/
   ```

3. **Commit and push** — pipeline runs automatically:
   ```bash
   git commit -am "chore: update fastapi to 0.128.0"
   git push origin feature/update-deps
   ```

---

## Troubleshooting

### Pipeline Failed: "Coverage below 80%"
- Run locally: `pytest tests/ --cov=src/itl_braincell_sdk --cov-fail-under=80`
- Add missing test cases or increase coverage
- Commit and re-run

### Pipeline Failed: "SAST violations found"
- View report in pipeline run details → Security tab
- Either fix the code or suppress false positives in `.semgrep.yml`
- Re-run pipeline

### PyPI Publish Failed: "Invalid distribution format"
- Ensure `pyproject.toml` has valid `[build-system]` section
- Run locally: `python -m build` to verify wheel builds
- Check wheel contents: `unzip -l dist/*.whl`

### Token Expired: "Authentication failed for PyPI"
- Regenerate PyPI API token
- Update in Azure DevOps Library > Secure Files
- Re-run publish stage

---

## Related Documentation

- [GitFlow Workflow](https://nvie.com/posts/a-successful-git-branching-model/) — Branch strategy rationale
- [Semantic Versioning 2.0.0](https://semver.org/) — Version numbering scheme
- [PyPI Release Guidelines](https://packaging.python.org/guides/publishing-package-distribution-releases-to-pypi/) — Publishing best practices
- [SBOM Guide](https://cyclonedx.org/) — Software Bill of Materials format

---

## Quick Commands

```bash
# Check pipeline status
az pipelines build queue --project itlusions --definition-name "ITL.Braincell.SDK"

# Manually trigger for a branch
az pipelines build queue --project itlusions --definition-name "ITL.Braincell.SDK" \
  --branch refs/heads/develop

# View latest run
az pipelines build definition show --project itlusions --name "ITL.Braincell.SDK"

# Publish to Azure Artifacts locally (test)
twine upload --repository-url $(REGISTRY_URL) dist/*
```

---

**Last updated:** 2026-08-02  
**Status:** Production Ready
