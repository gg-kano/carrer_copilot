# Career Copilot Tests

This directory contains tests for the Career Copilot application.

## Running Tests

### Install pytest

```bash
pip install pytest pytest-cov
```

### Run all tests

```bash
pytest
```

### Run with coverage report

```bash
pytest --cov=. --cov-report=html
```

### Run specific test file

```bash
pytest tests/test_config.py
```

### Run specific test class

```bash
pytest tests/test_text_utils.py::TestNormalizeText
```

### Run specific test method

```bash
pytest tests/test_text_utils.py::TestNormalizeText::test_remove_html_tags
```

## Test Structure

```
tests/
├── __init__.py                  # Test package initialization
├── README.md                     # This file
├── test_config.py               # Configuration tests
├── test_text_utils.py           # Text utility function tests
├── test_resume_processor.py     # Resume processing tests (TODO)
├── test_jd_processor.py         # JD processing tests (TODO)
├── test_matcher.py              # Matching algorithm tests (TODO)
└── test_database.py             # Database tests (TODO)
```

## Writing Tests

### Test Structure

Follow this pattern for test files:

```python
"""
Description of what this test file tests
"""

import pytest
from module_to_test import function_to_test


class TestFeatureName:
    """Test description"""

    def test_specific_behavior(self):
        """Test that specific thing works"""
        # Arrange
        input_data = "test"

        # Act
        result = function_to_test(input_data)

        # Assert
        assert result == "expected"
```

### Best Practices

1. **One assertion per test** (when possible)
2. **Clear test names** that describe what is being tested
3. **Arrange-Act-Assert** pattern
4. **Test edge cases**: empty strings, None values, very large inputs
5. **Use fixtures** for common setup
6. **Mock external dependencies** (API calls, database access)

## TODO

- [ ] Add tests for ResumePreprocessor
- [ ] Add tests for JDPreprocessor
- [ ] Add tests for ResumeJDMatcher
- [ ] Add tests for ChromaDBStorage
- [ ] Add integration tests
- [ ] Set up CI/CD testing
