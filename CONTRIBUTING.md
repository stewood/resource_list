# Contributing to Community Resource Directory

Thank you for your interest in contributing to the Community Resource Directory project! This document provides guidelines for contributing to the project.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** for your changes
4. **Make your changes** following the coding standards
5. **Test your changes** thoroughly
6. **Submit a pull request**

## 🏗️ Development Setup

### Prerequisites
- Python 3.8+
- Git
- Virtual environment (recommended)

### Local Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/homeless-resource-directory.git
cd homeless-resource-directory

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Setup database with WAL mode
python manage.py setup_wal

# Create superuser
python manage.py createsuperuser

# Run tests
./run_tests.py
```

## 📝 Coding Standards

### Python Code
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Write comprehensive docstrings (Google style)
- Keep files under 600 lines (preferably 400-500 lines)
- Use meaningful variable and function names

### Django Best Practices
- Use Django's built-in validation and forms
- Follow Django's app structure conventions
- Use Django's ORM efficiently
- Implement proper error handling

### Testing
- Write tests for all new functionality
- Maintain test coverage above 90%
- Use the modular test structure:
  - `test_models.py` - Model validation and workflow tests
  - `test_views.py` - HTTP views and permissions
  - `test_forms.py` - Form validation and status transitions
  - `test_search.py` - Search and filtering functionality
  - `test_permissions.py` - Role-based access control
  - `test_versions.py` - Version control and audit trails
  - `test_integration.py` - End-to-end workflows

### Running Tests
```bash
# Run all tests with optimizations
./run_tests.py

# Run specific test categories
./run_tests.py models
./run_tests.py views
./run_tests.py search

# Run with coverage report
./run_tests.py --coverage

# Run tests sequentially (for debugging)
./run_tests.py --no-parallel
```

## 🔄 Workflow

### Branch Naming
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring

### Commit Messages
Use conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes
- `refactor` - Code refactoring
- `test` - Test changes
- `chore` - Maintenance tasks

### Pull Request Process
1. **Create a descriptive PR title**
2. **Fill out the PR template** completely
3. **Reference related issues** using keywords
4. **Ensure all tests pass**
5. **Update documentation** as needed
6. **Request review** from maintainers

## 🐛 Bug Reports

When reporting bugs, please include:
- **Clear description** of the issue
- **Steps to reproduce** the problem
- **Expected vs actual behavior**
- **Environment details** (OS, Python version, etc.)
- **Screenshots** if applicable

## 💡 Feature Requests

When requesting features, please include:
- **Clear description** of the feature
- **Use case** and benefits
- **Implementation suggestions** (if any)
- **Mockups or examples** (if applicable)

## 📚 Documentation

- Update README.md for user-facing changes
- Update docstrings for code changes
- Add examples and usage instructions
- Keep documentation in sync with code

## 🔒 Security

- Report security vulnerabilities privately
- Don't commit sensitive information
- Follow security best practices
- Use environment variables for secrets

## 📞 Getting Help

- **Issues**: Use GitHub issues for bugs and feature requests
- **Discussions**: Use GitHub discussions for questions and ideas
- **Documentation**: Check the README.md and docs/ directory

## 🎉 Recognition

Contributors will be recognized in:
- Project README.md
- Release notes
- Contributor statistics

Thank you for contributing to making this project better! 🚀
