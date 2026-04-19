from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class AgentResult:
    agent_name: str
    summary: str
    details: Dict[str, Any]
    confidence: float


class BaseAgent:
    name = "Base Agent"

    def run(self, context: Dict[str, Any]) -> AgentResult:
        raise NotImplementedError

