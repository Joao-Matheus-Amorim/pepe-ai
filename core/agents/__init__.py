"""Subagentes especializados do Pepê."""

from core.agents.base_agent import BaseAgent
from core.agents.coder_agent import CoderAgent
from core.agents.researcher_agent import ResearcherAgent
from core.agents.general_agent import GeneralAgent
from core.agents.model_manager import ModelManager

__all__ = [
    "BaseAgent",
    "CoderAgent",
    "ResearcherAgent",
    "GeneralAgent",
    "ModelManager",
]
