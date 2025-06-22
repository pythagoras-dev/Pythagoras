import os
import sys


class OutputSuppressor:
    """A context manager that suppresses stdout and stderr output."""
    def __init__(self):
        pass

    def __enter__(self):
        """Redirect stdout and stderr to os.devnull."""
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        self.devnull = open(os.devnull, 'w')
        sys.stdout = self.devnull
        sys.stderr = self.devnull
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        if self.devnull:
            self.devnull.close()