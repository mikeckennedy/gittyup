# 🔧 Development Guide

This guide covers everything you need to know about developing and contributing to Gitty Up.

> **📦 For End Users:**  
> If you just want to use Gitty Up (not develop it), install from PyPI: `uv tool install gittyup`  
> See the [Installation Guide](../INSTALLATION.md) for details.

---

## 🚀 Development Setup

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/mikeckennedy/gittyup
cd gittyup

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or: venv\Scripts\activate  # Windows

# Install dependencies
uv pip install -e .
uv pip install -r requirements-development.txt
```

### Running Tests

```bash
# Full test suite with coverage
pytest --cov

# Quick test run
pytest -v

# Specific test files
pytest tests/test_scanner.py -v

# Run tests with detailed output
pytest -vv --cov --cov-report=html
```

### Code Quality

```bash
# Format code
ruff format

# Lint check
ruff check

# Auto-fix issues
ruff check --fix
```

**Current Metrics:**
- ✅ 115 tests passing
- ✅ 95.83% coverage
- ✅ Zero linting issues
- ✅ PEP 8 compliant

---

## 🤝 Contributing

We welcome contributions! Here's how to get involved:

### Ways to Contribute

- 🐛 **Report Bugs** - Found an issue? Open a GitHub issue
- 💡 **Suggest Features** - Have an idea? We'd love to hear it
- 📝 **Improve Docs** - Help make the documentation clearer
- 🔧 **Submit PRs** - Fix bugs or add features

### Contribution Guidelines

#### Code Style
- ✅ Follow PEP 8 style guidelines
- ✅ Add type hints to all functions
- ✅ Write comprehensive docstrings  
- ✅ Include tests for new features
- ✅ Maintain >90% test coverage
- ✅ Format with `ruff format`
- ✅ Pass all `ruff check` tests

#### Commit Messages
- Use clear, descriptive commit messages
- Start with a verb in present tense (Add, Fix, Update, etc.)
- Reference issue numbers when applicable

#### Pull Request Process
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure all tests pass and coverage remains high
5. Run code quality checks (`ruff format` and `ruff check`)
6. Commit your changes
7. Push to your fork
8. Open a Pull Request with a clear description

---

## 📊 Project Architecture

### Project Structure

```
gittyup/
├── gittyup/              # Main package
│   ├── __init__.py       # Package initialization
│   ├── cli.py            # Command-line interface
│   ├── scanner.py        # Repository discovery
│   ├── git_operations.py # Git interaction layer
│   ├── models.py         # Data models
│   └── output.py         # Output formatting
├── tests/                # Test suite
│   ├── test_cli.py
│   ├── test_scanner.py
│   ├── test_git_operations.py
│   ├── test_output.py
│   └── test_integration.py
├── docs/                 # Documentation
├── pyproject.toml        # Project metadata
├── requirements.txt      # Runtime dependencies
├── requirements-development.txt  # Dev dependencies
├── pytest.ini            # Test configuration
└── ruff.toml             # Code quality configuration
```

### Key Components

**scanner.py**
- Repository discovery and traversal
- Directory filtering and exclusion logic
- Smart detection of `.git` directories

**git_operations.py**
- Git command execution
- Safety checks (uncommitted changes, detached HEAD, etc.)
- Pull operations and error handling

**cli.py**
- Command-line argument parsing
- Orchestration of scanning and updating
- User interaction and feedback

**output.py**
- Colored, formatted console output
- Progress indicators and summary reporting
- Cross-platform terminal support

**models.py**
- Data structures for repository state
- Result types and status enums
- Type definitions for better IDE support

---

## 🧪 Testing Strategy

### Test Coverage

The project maintains >95% test coverage across all modules:

- **Unit Tests**: Test individual functions and methods
- **Integration Tests**: Test component interactions
- **Edge Cases**: Test error conditions and boundary cases
- **Mocking**: Use mocks for Git operations to avoid real filesystem changes

### Writing Tests

Example test structure:

```python
def test_feature_name():
    """Test description explaining what's being tested."""
    # Arrange - set up test data
    test_data = create_test_data()
    
    # Act - perform the operation
    result = function_under_test(test_data)
    
    # Assert - verify the results
    assert result.status == expected_status
    assert result.message == expected_message
```

### Test Fixtures

Common fixtures are defined in `conftest.py`:
- `tmp_path`: Temporary directory for test repositories
- `mock_git_repo`: Mocked Git repository structure
- `sample_config`: Test configuration data

---

## 📦 Dependencies

### Runtime Dependencies

- **click** (>=8.0): Command-line interface framework
- **colorama** (>=0.4): Cross-platform colored terminal output

### Development Dependencies

- **pytest** (>=7.0): Testing framework
- **pytest-cov**: Test coverage reporting
- **ruff**: Fast Python linter and formatter

### Dependency Management

We use `uv` for fast, reliable dependency management:

```bash
# Update runtime dependencies
uv pip-compile requirements.piptools -o requirements.txt

# Update development dependencies
uv pip-compile requirements-development.piptools -o requirements-development.txt

# Install updated dependencies
uv pip install -r requirements.txt
uv pip install -r requirements-development.txt
```

---

## 🔍 Debugging Tips

### Verbose Output

Use `--verbose` flag to see detailed execution:

```bash
gittyup --verbose --dry-run
```

### Python Debugger

Insert breakpoints in code:

```python
import pdb; pdb.set_trace()
```

### Test Debugging

Run specific tests with detailed output:

```bash
pytest tests/test_scanner.py::test_specific_function -vv -s
```

---

## 📊 Project Metrics

| Metric | Value |
|--------|-------|
| **Test Coverage** | 95.83% |
| **Total Tests** | 115 passing |
| **Code Quality** | Zero linting issues |
| **Python Version** | 3.13+ |
| **Dependencies** | Minimal (2 runtime) |
| **Lines of Code** | ~1,400 |

---

## 🚢 Release Process

### Versioning

We follow [Semantic Versioning](https://semver.org/):
- **MAJOR**: Incompatible API changes
- **MINOR**: New functionality (backwards-compatible)
- **PATCH**: Bug fixes (backwards-compatible)

### Creating a Release

1. Update version in `pyproject.toml`
2. Update `change-log.md` with release notes
3. Run full test suite: `pytest --cov`
4. Run code quality checks: `ruff format && ruff check`
5. Commit changes: `git commit -m "Release vX.Y.Z"`
6. Tag release: `git tag -a vX.Y.Z -m "Version X.Y.Z"`
7. Push changes and tags: `git push && git push --tags`
8. Build and publish to PyPI:
   ```bash
   # Build distribution packages
   uv build
   
   # Publish to PyPI (requires credentials)
   uv publish
   ```

### PyPI Publishing

Gitty Up is available on PyPI at [https://pypi.org/project/gittyup/](https://pypi.org/project/gittyup/).

Publishing requires PyPI credentials and is typically done by maintainers after a release is tagged.

---

## 📝 Documentation Standards

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of function.
    
    More detailed description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    
    Returns:
        Description of return value
    
    Raises:
        ValueError: When and why this is raised
    """
    pass
```

### Code Comments

- Write self-documenting code with clear variable names
- Add comments only when the "why" isn't obvious
- Keep comments up-to-date with code changes

---

## 🐛 Known Issues & Future Enhancements

### Potential Improvements

- **Parallel Processing**: Update multiple repos concurrently
- **Progress Persistence**: Resume interrupted scans
- **Configuration Files**: `.gittyup.yml` for per-directory settings
- **Branch Selection**: Specify which branch to update
- **Stash Support**: Temporarily stash changes before pulling

### Performance Considerations

- Repository scanning is I/O bound
- Git operations can be network bound
- Consider caching repository locations for large directory trees

---

## 💬 Getting Help

- **Issues**: Open a GitHub issue for bugs or questions
- **Discussions**: Use GitHub Discussions for general questions
- **Pull Requests**: Submit PRs for code contributions

---

## 🙏 Acknowledgments

Built with ❤️ for developers who juggle too many projects.

**Powered by:**
- [Click](https://click.palletsprojects.com/) - Command-line interface magic
- [Colorama](https://github.com/tartley/colorama) - Cross-platform colored output
- [Ruff](https://github.com/astral-sh/ruff) - Lightning-fast Python linting

---

<div align="center">

**Made with 🐴 by developers, for developers**

[⬆ Back to Top](#-development-guide)

</div>

