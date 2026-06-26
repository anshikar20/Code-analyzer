"""
Abstract base for language analyzers.
Defines the interface all analyzers must implement.
"""

from abc import ABC, abstractmethod
from ..models.responses import Finding


class BaseAnalyzer(ABC):
    """
    Abstract base class for language-specific code analyzers.

    Each analyzer wraps one or more external tools and returns
    structured Finding objects (never raw text).
    """

    @abstractmethod
    def quick_analyze(self, code: str) -> list[Finding]:
        """Run fast, lightweight checks suitable for real-time feedback."""
        ...

    @abstractmethod
    def full_analyze(self, code: str) -> list[Finding]:
        """Run comprehensive analysis with all available tools."""
        ...

    @abstractmethod
    def get_tools_used(self) -> list[str]:
        """Return list of tool names used by this analyzer."""
        ...
