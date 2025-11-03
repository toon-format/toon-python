## Description

<!-- Provide a clear and concise description of your changes -->

## Type of Change

<!-- Mark the relevant option with an [x] -->

- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Performance improvement
- [ ] Test coverage improvement

## Related Issues

<!-- Link any related issues using #issue_number -->

Closes #

## Changes Made

<!-- List the main changes in this PR -->

-
-
-

## SPEC Compliance

<!-- If this PR relates to the TOON spec, indicate which sections are affected -->

- [ ] This PR implements/fixes spec compliance
- [ ] Spec section(s) affected:
- [ ] Spec version:

## Testing

<!-- Describe the tests you added or ran -->

- [ ] All existing tests pass
- [ ] Added new tests for changes
- [ ] Tested on Python 3.8
- [ ] Tested on Python 3.9
- [ ] Tested on Python 3.10
- [ ] Tested on Python 3.11
- [ ] Tested on Python 3.12

### Test Output

```bash
# Paste test output here
```

## Code Quality

<!-- Confirm code quality checks -->

- [ ] Ran `ruff check src/toon_format tests` - no issues
- [ ] Ran `ruff format src/toon_format tests` - code formatted
- [ ] Ran `mypy src/toon_format` - no critical errors
- [ ] All tests pass: `pytest tests/ -v`

## Checklist

<!-- Mark completed items with an [x] -->

- [ ] My code follows the project's coding standards (PEP 8, line length 100)
- [ ] I have added type hints to new code
- [ ] I have added tests that prove my fix/feature works
- [ ] New and existing tests pass locally
- [ ] I have updated documentation (README.md, CLAUDE.md if needed)
- [ ] My changes do not introduce new dependencies
- [ ] I have maintained Python 3.8+ compatibility
- [ ] I have reviewed the [TOON specification](https://github.com/toon-format/spec) for relevant sections

## Performance Impact

<!-- If applicable, describe any performance implications -->

- [ ] No performance impact
- [ ] Performance improvement (describe below)
- [ ] Potential performance regression (describe and justify below)

<!-- Details: -->

## Breaking Changes

<!-- If this is a breaking change, describe the migration path for users -->

- [ ] No breaking changes
- [ ] Breaking changes (describe migration path below)

<!-- Migration path: -->

## Screenshots / Examples

<!-- If applicable, add screenshots or example output -->

```python
# Example usage
```

Output:
```
# Example output
```

## Additional Context

<!-- Add any other context about the PR here (optional) -->

## Checklist for Reviewers

<!-- For maintainers reviewing this PR -->

- [ ] Code changes are clear and well-documented
- [ ] Tests adequately cover the changes
- [ ] Documentation is updated
- [ ] No security concerns
- [ ] Follows TOON specification
- [ ] Backward compatible (or breaking changes are justified and documented)
