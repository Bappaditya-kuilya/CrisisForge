from __future__ import annotations

from typing import Any, Dict, List

from agents.action_optimizer import ActionOptimizerAgent
from agents.data_scout import DataScoutAgent
from agents.ethical_guardian import EthicalGuardianAgent
from agents.risk_forecaster import RiskForecasterAgent


class CrisisOrchestrator:
    def __init__(self) -> None:
        self.pipeline = [
            DataScoutAgent(),
            RiskForecasterAgent(),
            ActionOptimizerAgent(),
            EthicalGuardianAgent(),
        ]

    def run(self, crisis_text: str) -> Dict[str, Any]:
        context: Dict[str, Any] = {
            "crisis_text": crisis_text,
            "agent_outputs": {},
        }
        timeline: List[Dict[str, Any]] = []

        for agent in self.pipeline:
            result = agent.run(context)
            context["agent_outputs"][result.agent_name] = {
                "summary": result.summary,
                "details": result.details,
                "confidence": result.confidence,
            }
            timeline.append(
                {
                    "agent": result.agent_name,
                    "summary": result.summary,
                    "confidence": result.confidence,
                }
            )

        plan = context["agent_outputs"]["Action Optimizer"]["details"]["recommended_plan"]
        ethics = context["agent_outputs"]["Ethical Guardian"]["details"]
        forecast = context["agent_outputs"]["Risk Forecaster"]["details"]
        scout = context["agent_outputs"]["Data Scout"]["details"]
        extracted = scout["extracted_inputs"]
        overall_confidence = round(
            sum(output["confidence"] for output in context["agent_outputs"].values())
            / len(context["agent_outputs"]),
            2,
        )

        return {
            "timeline": timeline,
            "agent_outputs": context["agent_outputs"],
            "final_plan": {
                "title": plan["name"],
                "score": plan["score"],
                "steps": plan["steps"],
                "expected_people_reached": plan["expected_people_reached"],
                "ethics_approved": ethics["approved"],
                "overall_risk": forecast["overall_risk"],
                "overall_confidence": overall_confidence,
                "location": scout["location"],
                "hazard_type": extracted["hazard_type"],
                "urgency_hours": extracted["urgency_hours"],
                "constraints": extracted["constraints"],
            },
        }
