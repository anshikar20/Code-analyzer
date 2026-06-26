"""
Safe temporary file management.
Preserved from original app.py but encapsulated properly.
"""

import tempfile
import os
from contextlib import contextmanager


@contextmanager
def temp_code_file(code: str, suffix: str = ".py"):
    """
    Context manager that creates a temp file with source code,
    yields the file path, and guarantees cleanup.

    Usage:
        with temp_code_file(code, ".py") as path:
            result = run_tool(["pylint", path])
    """
    temp = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=suffix,
        delete=False,
        encoding="utf-8",
        prefix="analyzer_"
    )
    try:
        temp.write(code)
        temp.close()
        yield temp.name
    finally:
        try:
            if os.path.exists(temp.name):
                os.remove(temp.name)
        except OSError:
            pass
