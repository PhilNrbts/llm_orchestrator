"""
Base tool interface for the LLM orchestrator.
All tools must inherit from BaseTool to ensure consistent structure.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    """
    Abstract base class for all workflow tools.

    All tools must implement the execute method which takes keyword arguments
    and returns a dictionary containing the tool's output.
    """

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the tool with the given inputs.

        Args:
            **kwargs: Tool-specific input parameters

        Returns:
            Dict[str, Any]: Tool output containing at minimum an 'output' key

        Raises:
            Exception: If tool execution fails
        """
        pass

    @property
    def name(self) -> str:
        """Return the tool name (defaults to class name without 'Tool' suffix)."""
        class_name = self.__class__.__name__
        if class_name.endswith("Tool"):
            return class_name[:-4].lower()
        return class_name.lower()

    def validate_inputs(self, **kwargs) -> None:
        """
        Validate tool inputs before execution.
        Override in subclasses to add specific validation.

        Args:
            **kwargs: Tool inputs to validate

        Raises:
            ValueError: If inputs are invalid
        """
        pass
