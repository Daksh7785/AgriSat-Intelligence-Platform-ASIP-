# 🤝 Contributing to Kisan Drishti

Thank you for your interest in contributing to **Kisan Drishti**! This guide explains everything you need to know to submit high-quality contributions.

---

## 📋 Table of Contents
1. [Code of Conduct](#code-of-conduct)
2. [How to Contribute](#how-to-contribute)
3. [Development Setup](#development-setup)
4. [Coding Standards](#coding-standards)
5. [Submitting Changes](#submitting-changes)
6. [Reporting Issues](#reporting-issues)

---

## Code of Conduct

By participating in this project you agree to abide by the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

---

## How to Contribute

### 🐛 Bug Reports
- Open a [GitHub Issue](https://github.com/Daksh7785/AgriSat-Intelligence-Platform-ASIP-/issues/new?template=bug_report.md)
- Include: environment, steps to reproduce, expected vs actual behavior, logs

### 🌟 Feature Requests
- Open a [GitHub Issue](https://github.com/Daksh7785/AgriSat-Intelligence-Platform-ASIP-/issues/new?template=feature_request.md)
- Describe the use case, expected behavior, and any related satellite/ML research

### 💻 Code Contributions

We welcome contributions in these areas:

| Area | Examples |
|------|---------|
| 🛰️ Satellite Connectors | RESOURCESAT-2A, Landsat-9, CARTOSAT |
| 🧠 ML Models | Improved classifiers, transfer learning |
| 🌐 Language Support | Tamil, Telugu, Kannada, Marathi TTS |
| 📱 Mobile App | React Native Android/iOS |
| 📊 Monitoring | Grafana dashboards, Prometheus alerts |
| 🧪 Tests | Coverage expansion, edge cases |
| 📖 Documentation | Tutorials, API examples, translations |

---

## Development Setup

### 1. Fork & Clone

```bash
# Fork via GitHub UI, then:
git clone https://github.com/YOUR_USERNAME/AgriSat-Intelligence-Platform-ASIP-.git
cd AgriSat-Intelligence-Platform-ASIP-

# Add upstream remote
git remote add upstream https://github.com/Daksh7785/AgriSat-Intelligence-Platform-ASIP-.git
```

### 2. Create a Feature Branch

```bash
# Always branch from latest main
git fetch upstream
git checkout -b feature/your-feature-name upstream/main
```

### Branch Naming Conventions

| Type | Prefix | Example |
|------|--------|---------|
| Feature | `feature/` | `feature/landsat9-connector` |
| Bug Fix | `fix/` | `fix/spei-nan-handling` |
| Documentation | `docs/` | `docs/api-examples` |
| Refactor | `refactor/` | `refactor/celery-tasks` |
| Tests | `test/` | `test/zonation-edge-cases` |

### 3. Set Up Dev Environment

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 4. Run Tests Before Making Changes

```bash
python -m pytest tests/ -v
# Ensure all 40 tests pass before you start
```

---

## Coding Standards

### Python (Backend)

- **Style**: Follow [PEP 8](https://pep8.org/). Use `black` for formatting.
- **Type Hints**: All functions must have type annotations.
- **Docstrings**: Google-style docstrings for all public functions.
- **Pydantic**: Use Pydantic v2 `model_config = ConfigDict(...)` pattern.
- **Async**: Prefer `async def` for all I/O-bound route handlers.

```python
# ✅ Good
async def get_field_advisory(field_id: int, db: AsyncSession) -> AdvisoryResponse:
    """Compute precision irrigation advisory for a given field.

    Args:
        field_id: Database ID of the agricultural field.
        db: Async database session.

    Returns:
        AdvisoryResponse containing water depth, volume, and savings.
    """
    ...

# ❌ Bad
def advisory(id, db):
    ...
```

### TypeScript (Frontend)

- **Style**: ESLint + Prettier (config already in repo)
- **Components**: Functional components with typed props interfaces
- **State**: Prefer React hooks over class components

```typescript
// ✅ Good
interface FieldCardProps {
  fieldId: number;
  cropType: string;
  stressLevel: 'low' | 'medium' | 'high';
}

const FieldCard: React.FC<FieldCardProps> = ({ fieldId, cropType, stressLevel }) => {
  ...
};
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]
[optional footer]
```

| Type | When to Use |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation changes |
| `test` | Adding or updating tests |
| `refactor` | Code restructuring (no behavior change) |
| `perf` | Performance improvements |
| `ci` | CI/CD pipeline changes |
| `chore` | Dependency updates, build changes |

**Examples:**
```
feat(ml): add RESOURCESAT-2A connector for LISS-III bands
fix(spei): handle NaN values in L-moment parameter fitting
docs(api): add curl examples for all v1 endpoints
test(zonation): add edge case for single-pixel field input
```

---

## Submitting Changes

### 1. Ensure Tests Pass

```bash
# All 40 tests must pass
python -m pytest tests/ -v

# No linting errors
cd backend && python -m black . --check
```

### 2. Add Tests for Your Code

- Every new ML module must have a test in `tests/`
- Every new API route must have a smoke test in `tests/test_apis.py`
- Aim for 80%+ coverage on new code

### 3. Update Documentation

- Update `README.md` if adding new features/endpoints
- Update `docs/DATA_SOURCES.md` if adding a new satellite source
- Update `docs/MODEL_CARDS.md` if adding a new ML model
- Add to `CHANGELOG.md` under `Unreleased`

### 4. Open a Pull Request

- Target branch: `main`
- Fill in the PR template completely
- Link related issues with `Closes #123`
- Request review from at least one maintainer

### PR Checklist

- [ ] Tests pass locally (`pytest tests/ -v`)
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No secrets or API keys committed
- [ ] `.env` changes reflected in `.env.example`

---

## Reporting Issues

### Security Vulnerabilities

**Do NOT open a public issue for security vulnerabilities.**

Email: `security@kisandrishti.gov.in` with:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

You will receive a response within 48 hours.

### General Bugs

Open a GitHub Issue with this template:

```markdown
## Bug Description
A clear description of what the bug is.

## Steps to Reproduce
1. Start Docker Compose with `docker-compose up`
2. Call `GET /api/v1/explain/1/why`
3. See error

## Expected Behavior
SHAP attributions should return in < 500ms

## Actual Behavior
Returns HTTP 500 with: `ValueError: X has NaN values`

## Environment
- OS: Ubuntu 22.04
- Python: 3.11.4
- Docker: 24.0.5
- Branch: main / commit: abc1234

## Logs
```
[paste relevant logs here]
```
```

---

## 🙏 Recognition

All contributors are listed in [CONTRIBUTORS.md](CONTRIBUTORS.md) and credited in release notes.

Thank you for making Kisan Drishti better for Indian farmers! 🌾
