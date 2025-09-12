# Contributing to Pythagoras

Thank you for your interest in contributing to `Pythagoras`! 
Your help is greatly appreciated. These guidelines will help you get started.

## Getting Started

1.  **Fork and Clone:**
    ```bash
    git clone https://github.com/your-username/Pythagoras.git
    cd parameterizable
    ```

2.  **Install Dependencies:**
    We use `uv` for package management.
    ```bash
    uv pip install -e ".[dev]"
    ```

3.  **Run Tests:**
    Make sure the test suite passes before making changes.
    ```bash
    pytest
    ```

## How to Contribute

*   **Report Bugs:** Use the GitHub issue tracker to report bugs. 
Please provide a clear description, steps to reproduce, and your Python version.
*   **Suggest Enhancements:** Open an issue to discuss new features or improvements.

### Submitting Pull Requests

1.  **Create a Branch:**
    ```bash
    git checkout -b your-feature-name
    ```
2.  **Make Changes:** Write your code and add corresponding tests in the `tests/` directory.
3.  **Follow Code Style:**
    *   Adhere to PEP 8 guidelines.
    *   Write clear, Google-style docstrings for public functions and classes.
    *   Add type hints where appropriate.
4.  **Write Commit Messages:** Follow the conventions below.
5.  **Push and Open a Pull Request:** Push your branch to your fork and open a pull request.

### Commit Message Prefixes

Use these prefixes for your commit messages:

| Prefix | Description                      |
| :----- | :------------------------------- |
| `ENH:` | Enhancement, new functionality   |
| `BUG:` | Bug fix                          |
| `DOC:` | Additions/updates to documentation |
| `TST:` | Additions/updates to tests       |
| `BLD:` | Build process/script updates     |
| `PERF:`| Performance improvement          |
| `TYP:` | Type annotations                 |
| `CLN:` | Code cleanup                     |

*Example: `ENH: Add support for nested parameter validation`*

## License

By contributing, you confirm that your contributions are an original work,
or you have permission to use it, and agree that it will be 
licensed under the MIT License.

## Questions?

Feel free to open an issue or contact the maintainer, Vlad (Volodymyr) Pavlov.