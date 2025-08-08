"""Agent generator from YAML templates."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import yaml


class Agent:
    """Simple agent representation.

    Attributes:
        config: Raw template configuration.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def invoke(self, prompt: str) -> str:
        """Invoke the agent with a prompt.

        Args:
            prompt: Input string.

        Returns:
            Dummy response string.
        """
        # TODO: Replace with real OpenAI / tool calling logic.
        return f"TODO: {prompt}"


def load_templates(dir_path: str = "templates") -> Dict[str, Dict[str, Any]]:
    """Load all YAML templates in a directory.

    Args:
        dir_path: Directory containing YAML files.

    Returns:
        Dictionary mapping template ID to configuration.
    """
    templates: Dict[str, Dict[str, Any]] = {}
    for path in Path(dir_path).glob("*.yaml"):
        with open(path, "r", encoding="utf-8") as handle:
            data = yaml.safe_load(handle)
            templates[data["id"]] = data
    return templates


def build_agent(state: Dict[str, Any]) -> Agent:
    """Build an agent based on the provided state.

    Args:
        state: Current workflow state. Must include ``template_id`` key.

    Returns:
        Instantiated :class:`Agent`.
    """
    templates = load_templates()
    template_id = state.get("template_id", "faq_bot_v1")
    config = templates.get(template_id, {})
    return Agent(config)

