import os
from contextlib import ExitStack, redirect_stderr, redirect_stdout



class OutputSuppressor:
    """A context manager that suppresses stdout and stderr output."""

    def __enter__(self):
        """Redirect stdout and stderr to os.devnull."""
        self._stack = ExitStack()
        devnull = self._stack.enter_context(open(os.devnull, "w"))
        self._stack.enter_context(redirect_stdout(devnull))
        self._stack.enter_context(redirect_stderr(devnull))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._stack.__exit__(exc_type, exc_val, exc_tb)