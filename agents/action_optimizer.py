from __future__ import annotations

from typing import Any, Dict, List

from agents.base import AgentResult, BaseAgent


class ActionOptimizerAgent(BaseAgent):
    name = "Action Optimizer"

    def run(self, context: Dict[str, Any]) -> AgentResult:
        scout = context["agent_outputs"]["Data Scout"]["details"]
        forecast = context["agent_outputs"]["Risk Forecaster"]["details"]
        extracted = scout["extracted_inputs"]
        resources = extracted["resources"]
        population = extracted["estimated_population"]
        overall_risk = forecast["overall_risk"]
        hazard_type = extracted["hazard_type"]
        urgency_hours = extracted["urgency_hours"]
        constraints = extracted["constraints"]

        plans = self._build_plans(
            population,
            resources,
            overall_risk,
            hazard_type,
            urgency_hours,
            constraints,
        )
        ranked = sorted(plans, key=lambda item: item["score"], reverse=True)
        best = ranked[0]

        summary = (
            f"Evaluated {len(ranked)} response strategies and selected "
            f"'{best['name']}' as the highest-value option."
        )
        return AgentResult(
            agent_name=self.name,
            summary=summary,
            details={
                "recommended_plan": best,
                "alternatives": ranked[1:],
                "ranking_table": ranked,
            },
            confidence=0.89,
        )

    def _build_plans(
        self,
        population: int,
        resources: Dict[str, Any],
        overall_risk: float,
        hazard_type: str,
        urgency_hours: int | None,
        constraints: List[str],
    ) -> List[Dict[str, Any]]:
        boats = resources["boats"]
        medical_teams = resources["medical_teams"]
        shelter_capacity = resources["shelter_capacity"]
        evacuation_bias = 0.08 if hazard_type in {"flood", "cyclone", "wildfire"} else 0.02
        stabilization_bias = 0.08 if hazard_type in {"heatwave", "earthquake"} else 0.02
        time_pressure = 0.06 if urgency_hours and urgency_hours <= 8 else 0.0
        access_penalty = 0.04 if any("Road access" in item or "boat" in item.lower() for item in constraints) else 0.0

        candidates = [
            {
                "name": "Phased Evacuation With Medical Triage",
                "speed": min(0.96, 0.82 + time_pressure),
                "coverage": min(1.0, (boats * 120 + shelter_capacity * 0.75) / max(population, 1)),
                "fairness": 0.91,
                "resource_fit": min(1.0, (medical_teams * 120 + shelter_capacity) / max(population, 1)),
                "hazard_fit": min(1.0, 0.82 + evacuation_bias),
                "steps": [
                    "Evacuate low-lying and medically fragile groups first.",
                    "Stage mobile medical triage at two transport hubs.",
                    "Convert schools and civic buildings into overflow shelters.",
                    "Refresh route assignments every 30 minutes as conditions change.",
                ],
            },
            {
                "name": "Centralized Shelter Stabilization",
                "speed": 0.64,
                "coverage": min(1.0, max(0.05, (shelter_capacity / max(population, 1)) - access_penalty)),
                "fairness": 0.86,
                "resource_fit": min(1.0, (medical_teams * 90 + shelter_capacity * 1.1) / max(population, 1)),
                "hazard_fit": min(1.0, 0.74 + stabilization_bias),
                "steps": [
                    "Hold position and strengthen large shelter sites.",
                    "Concentrate food, water, and medical support in central hubs.",
                    "Defer movement until route confidence improves.",
                    "Use local transport only for high-risk households.",
                ],
            },
            {
                "name": "Distributed Neighborhood Extraction",
                "speed": 0.78,
                "coverage": min(1.0, (boats * 95 + shelter_capacity * 0.48) / max(population, 1)),
                "fairness": 0.89,
                "resource_fit": min(1.0, (medical_teams * 100 + shelter_capacity * 0.8) / max(population, 1)),
                "hazard_fit": min(1.0, 0.78 + evacuation_bias * 0.8),
                "steps": [
                    "Split response into neighborhood-level rescue cells.",
                    "Assign boats to routes with the highest density and lowest elevation.",
                    "Open micro-shelters closer to affected communities.",
                    "Reserve medical teams for injury clusters and waterborne disease risk.",
                ],
            },
        ]

        ranked: List[Dict[str, Any]] = []
        for plan in candidates:
            score = (
                (plan["speed"] * 0.24)
                + (plan["coverage"] * 0.32)
                + (plan["fairness"] * 0.18)
                + (plan["resource_fit"] * 0.16)
                + (plan["hazard_fit"] * 0.10)
            )
            ranked.append(
                {
                    **plan,
                    "score": round(score * 100, 1),
                    "expected_people_reached": int(population * min(0.98, plan["coverage"] + 0.18)),
                }
            )
        return ranked
