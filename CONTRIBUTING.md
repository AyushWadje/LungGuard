# Contributing to LungGuard

Thank you for your interest in contributing to LungGuard! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected behavior vs actual behavior
- Screenshots (if applicable)
- Your environment (OS, Python version, Node.js version)

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

- A clear and descriptive title
- Detailed description of the proposed feature
- Why this enhancement would be useful
- Possible implementation approach (optional)

### Pull Requests

1. Fork the repository
2. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Make your changes following our coding standards
4. Test your changes thoroughly
5. Commit with descriptive messages:
   ```bash
   git commit -m "feat: add new prediction model"
   ```
6. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```
7. Open a Pull Request with a clear description

## Development Setup

### Backend Development

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements_ml.txt

# Run tests
python -m pytest tests/

# Start development server
python main.py
```

### Frontend Development

```bash
cd aerolung-dashboard

# Install dependencies
npm install

# Start dev server
npm run dev

# Run linter
npm run lint
```

## Coding Standards

### Python

- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for all functions and classes
- Maximum line length: 100 characters

```python
def calculate_plsi(aqi: float, spo2: float, age: int) -> float:
    """
    Calculate Personal Lung Stress Index.
    
    Args:
        aqi: Air Quality Index value
        spo2: Blood oxygen saturation percentage
        age: Patient age in years
        
    Returns:
        PLSI score between 0-100
    """
    pass
```

### TypeScript/JavaScript

- Use TypeScript for type safety
- Follow ESLint configuration
- Use functional components with hooks
- Maximum line length: 100 characters

```typescript
interface PredictionRequest {
  aqi: number;
  spo2: number;
  age: number;
}

const fetchPrediction = async (data: PredictionRequest): Promise<Response> => {
  // Implementation
};
```

## Commit Message Guidelines

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Examples:
```
feat: add risk prediction endpoint
fix: correct PLSI calculation for edge cases
docs: update API documentation with new endpoints
```

## Testing

### Backend Tests

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=.
```

### Frontend Tests

```bash
# Run Jest tests
npm test

# Run with coverage
npm test -- --coverage
```

## Documentation

- Update README.md for user-facing changes
- Update API_DOCS.md for API changes
- Add inline comments for complex logic
- Update docstrings when modifying functions

## ML Model Contributions

When contributing ML models:

1. Document model architecture in comments
2. Include training scripts
3. Provide model evaluation metrics
4. Document input/output formats
5. Include sample predictions

## Questions?

Feel free to open an issue with the `question` label or reach out to the maintainers.

Thank you for contributing to LungGuard! 🫁
