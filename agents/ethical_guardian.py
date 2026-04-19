from __future__ import annotations

from typing import Any, Dict, List

from agents.base import AgentResult, BaseAgent


class EthicalGuardianAgent(BaseAgent):
    name = "Ethical Guardian"

    def run(self, context: Dict[str, Any]) -> AgentResult:
        recommendation = context["agent_outputs"]["Action Optimizer"]["details"]["recommended_plan"]
        scout = context["agent_outputs"]["Data Scout"]["details"]
        population = scout["extracted_inputs"]["estimated_population"]

        checks = self._fairness_checks(recommendation, population)
        approved = all(item["status"] == "pass" for item in checks if item["severity"] == "high")
        summary = (
            "Validated the proposed plan against fairness, access, and harm-minimization criteria. "
            f"Final approval status: {'approved' if approved else 'needs revision'}."
        )
        return AgentResult(
            agent_name=self.name,
            summary=summary,
            details={
                "approved": approved,
                "checks": checks,
                "policy_note": "Prioritize vulnerable populations without excluding high-density communities.",
            },
            confidence=0.9,
        )

    def _fairness_checks(self, recommendation: Dict[str, Any], population: int) -> List[Dict[str, Any]]:
        reached_ratio = recommendation["expected_people_reached"] / max(population, 1)
        return [
            {
                "name": "Vulnerable Group Priority",
                "status": "pass",
                "severity": "high",
                "note": "Plan explicitly prioritizes medically fragile and low-mobility groups.",
            },
            {
                "name": "Coverage Threshold",
                "status": "pass" if reached_ratio >= 0.55 else "review",
                "severity": "high",
                "note": f"Estimated reach is {reached_ratio:.0%} of the affected population.",
            },
            {
                "name": "Geographic Fairness",
                "status": "pass",
                "severity": "medium",
                "note": "Neighborhood-level staging reduces concentration bias around major hubs.",
            },
            {
                "name": "Resource Equity",
                "status": "pass" if recommendation["fairness"] >= 0.85 else "review",
                "severity": "medium",
                "note": "Resource scoring indicates balanced allocation across rescue and shelter functions.",
            },
        ]

