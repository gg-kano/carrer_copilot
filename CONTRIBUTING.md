# Contributing to Career Copilot

Thank you for your interest in contributing to Career Copilot! We welcome contributions from the community.

## Code of Conduct

Be respectful, inclusive, and professional in all interactions.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates.

When reporting bugs, include:
- Detailed description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Screenshots (if applicable)
- Environment details (OS, Python version, etc.)

**Bug Report Template:**

```markdown
**Description:**
A clear description of the bug.

**Steps to Reproduce:**
1. Go to '...'
2. Click on '...'
3. See error

**Expected Behavior:**
What you expected to happen.

**Actual Behavior:**
What actually happened.

**Environment:**
- OS: [e.g., Windows 11, macOS 14, Ubuntu 22.04]
- Python Version: [e.g., 3.12.1]
- Career Copilot Version: [commit hash or release]

**Screenshots:**
If applicable, add screenshots.
```

### Suggesting Features

We love new ideas! To suggest a feature:

1. Check if it's already been suggested
2. Open a new issue with the `enhancement` label
3. Describe the feature and why it would be useful
4. Provide examples of how it would work

### Pull Requests

#### Before Starting

1. Check existing issues and PRs
2. For major changes, open an issue first to discuss
3. Fork the repository
4. Create a new branch from `main`

#### Development Process

1. **Set up your environment:**
   ```bash
   git clone https://github.com/YOUR_USERNAME/carrer_copilot.git
   cd carrer_copilot
   pip install -r requirements.txt
   ```

2. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Make your changes:**
   - Write clean, readable code
   - Add comments for complex logic
   - Update documentation as needed
   - Follow the existing code style

4. **Test your changes:**
   - Run the application locally
   - Test all affected features
   - Ensure no existing functionality breaks

5. **Commit your changes:**
   ```bash
   git add .
   git commit -m "type: brief description"
   ```

   Commit types:
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation changes
   - `style:` Code style changes (formatting)
   - `refactor:` Code refactoring
   - `test:` Adding tests
   - `chore:` Maintenance tasks

6. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then open a Pull Request on GitHub.

#### PR Guidelines

Your PR should:
- Have a clear title and description
- Reference related issues (e.g., "Fixes #123")
- Include screenshots/GIFs for UI changes
- Pass all checks (when CI/CD is set up)
- Be reviewed by maintainers

## Code Style

### Python

- Follow **PEP 8** style guide
- Use **Black** for code formatting (line length: 100)
- Use meaningful variable and function names
- Add type hints where appropriate
- Write docstrings for functions and classes

**Example:**

```python
def process_resume(resume_path: str, use_cache: bool = True) -> dict:
    """
    Process a resume PDF and extract structured information.

    Args:
        resume_path: Path to the PDF resume file
        use_cache: Whether to use cached results if available

    Returns:
        Dictionary containing parsed resume data with keys:
        - name: Candidate name
        - skills: List of skills
        - experience: List of work experiences

    Raises:
        FileNotFoundError: If resume_path doesn't exist
        ValueError: If PDF is invalid or corrupted
    """
    # Implementation here
    pass
```

### File Organization

- Keep files focused and under 500 lines when possible
- Group related functionality together
- Use clear, descriptive file names
- Add `__init__.py` to packages

## Testing

While we don't have automated tests yet, please:

1. Test your changes manually
2. Try edge cases and error scenarios
3. Test on different operating systems if possible
4. Document test cases in your PR description

## Documentation

- Update README.md if you add new features
- Add docstrings to new functions/classes
- Update inline comments for complex logic
- Create examples for new functionality

## Questions?

If you have questions:
- Open a GitHub Discussion
- Comment on the relevant issue
- Reach out to maintainers

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Future CONTRIBUTORS.md file
- Release notes for significant contributions

Thank you for contributing to Career Copilot!
