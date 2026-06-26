"""
Safe subprocess execution for external analysis tools.
Preserved from original app.py but with proper error handling and output separation.
"""

import subprocess
import sys
import logging

logger = logging.getLogger(__name__)


def run_tool(command: list[str], timeout: int = 30) -> tuple[str, str, int]:
    """
    Run an external tool safely and return separated stdout/stderr/returncode.

    Returns:
        (stdout, stderr, return_code) tuple.
        Never raises — returns error messages in stderr on failure.
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout or "", result.stderr or "", result.returncode

    except subprocess.TimeoutExpired:
        logger.warning(f"Tool timed out after {timeout}s: {command[0]}")
        return "", f"Tool execution timed out after {timeout}s.", -1

    except FileNotFoundError:
        logger.error(f"Tool not found: {command[0]}")
        return "", f"Tool not found: {command[0]}", -1

    except Exception as e:
        logger.error(f"Error running tool {command[0]}: {e}")
        return "", f"Error running tool: {str(e)}", -1


def run_python_tool(module: str, args: list[str], timeout: int = 30) -> tuple[str, str, int]:
    """
    Run a Python module as a tool (e.g., pylint, flake8).

    Usage:
        stdout, stderr, rc = run_python_tool("pylint", [filepath])
    """
    command = [sys.executable, "-m", module] + args
    return run_tool(command, timeout)


def check_tool_available(module: str) -> bool:
    """Check if a Python tool module is importable."""
    try:
        stdout, stderr, rc = run_python_tool(module, ["--version"], timeout=5)
        return rc == 0 or bool(stdout)  # Some tools return non-zero for --version
    except Exception:
        return False
