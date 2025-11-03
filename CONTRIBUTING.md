# Contributing to toon-python

Thank you for your interest in contributing to the official Python implementation of TOON!

## Project Setup

This project uses [`uv`](https://github.com/astral-sh/uv) for dependency management.

```bash
# Clone the repository
git clone https://github.com/toon-format/toon-python.git
cd toon-python

# Install dependencies (uv will create a virtual environment automatically)
uv sync

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/toon_format --cov-report=term-missing
```

## Development Workflow

1. **Fork the repository** and create a feature branch
2. **Make your changes** following the coding standards below
3. **Add tests** for any new functionality
4. **Ensure all tests pass** and coverage remains high
5. **Submit a pull request** with a clear description

## Coding Standards

### Python Version Support

We support Python 3.11 through 3.14t (including free-threaded Python).

### Type Safety

- All code must include type hints
- Run `mypy` before committing:
  ```bash
  uv run mypy src/
  ```

### Code Style

- We use `ruff` for linting and formatting
- Run before committing:
  ```bash
  uv run ruff check src/ tests/
  uv run ruff format src/ tests/
  ```

### Testing

- All new features must include tests
- Aim for high test coverage (80%+)
- Tests should cover edge cases and spec compliance
- Run the full test suite:
  ```bash
  uv run pytest tests/
  ```

## SPEC Compliance

All implementations must comply with the [TOON specification](https://github.com/toon-format/spec/blob/main/SPEC.md).

Before submitting changes that affect encoding/decoding behavior:
1. Verify against the official SPEC.md
2. Add tests for the specific spec sections you're implementing
3. Document any spec version requirements

## Pull Request Guidelines

- **Title**: Use a clear, descriptive title (e.g., "Add support for nested arrays", "Fix: Handle edge case in decoder")
- **Description**: Explain what changes you made and why
- **Tests**: Include tests for your changes
- **Documentation**: Update README or docstrings if needed
- **Commits**: Use clear commit messages ([Conventional Commits](https://www.conventionalcommits.org/) preferred)

## Communication

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Pull Requests**: For code reviews and implementation discussion

## Co-Maintainers

This is a collaborative project. Current maintainers:

- @bpradana
- @davidpirogov
- @xaviviro

All maintainers have equal decision-making power. For major architectural decisions, please open a discussion issue first.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
