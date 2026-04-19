from __future__ import annotations

import random
from statistics import mean
from typing import Any, Dict, List

from agents.base import AgentResult, BaseAgent


class RiskForecasterAgent(BaseAgent):
    name = "Risk Forecaster"

    def run(self, context: Dict[str, Any]) -> AgentResult:
        scout = context["agent_outputs"]["Data Scout"]["details"]
        extracted = scout["extracted_inputs"]
        severity = extracted["severity"]
        population = extracted["estimated_population"]
        weather = scout.get("weather") or {}

        wind_factor = min((weather.get("wind_speed_kmh") or 20) / 120, 1.0)
        rain_factor = min((weather.get("precipitation_mm") or 2) / 25, 1.0)

        outcomes = self._simulate(population, severity, wind_factor, rain_factor)
        overall_risk = min(
            0.35 + (severity * 0.35) + (wind_factor * 0.15) + (rain_factor * 0.15),
            0.99,
        )
        summary = (
            f"Ran {len(outcomes)} probabilistic simulations. Estimated operational risk is "
            f"{overall_risk:.0%} with evacuation delay and shelter overload as the main failure modes."
        )

        return AgentResult(
            agent_name=self.name,
            summary=summary,
            details={
                "simulation_runs": len(outcomes),
                "average_people_at_risk": round(mean(item["people_at_risk"] for item in outcomes)),
                "average_delay_hours": round(mean(item["delay_hours"] for item in outcomes), 1),
                "overload_probability": round(
                    sum(1 for item in outcomes if item["shelter_overload"]) / len(outcomes), 2
                ),
                "critical_failure_probability": round(
                    sum(1 for item in outcomes if item["critical_failure"]) / len(outcomes), 2
                ),
                "overall_risk": round(overall_risk, 2),
                "sample_outcomes": outcomes[:5],
            },
            confidence=0.87,
        )

    def _simulate(
        self,
        population: int,
        severity: float,
        wind_factor: float,
        rain_factor: float,
        runs: int = 1200,
    ) -> List[Dict[str, Any]]:
        seeded = random.Random(42)
        outcomes: List[Dict[str, Any]] = []
        for _ in range(runs):
            disruption = severity * seeded.uniform(0.85, 1.25)
            weather_stress = (wind_factor * 0.55) + (rain_factor * 0.45)
            people_at_risk = int(population * min(0.95, 0.22 + disruption * 0.5 + weather_stress * 0.25))
            delay_hours = round(0.8 + seeded.uniform(0.4, 3.8) + (severity * 2.5) + (wind_factor * 1.3), 2)
            shelter_overload = seeded.random() < min(0.92, 0.18 + severity * 0.45 + rain_factor * 0.35)
            critical_failure = seeded.random() < min(0.85, 0.08 + severity * 0.3 + weather_stress * 0.3)
            outcomes.append(
                {
                    "people_at_risk": people_at_risk,
                    "delay_hours": delay_hours,
                    "shelter_overload": shelter_overload,
                    "critical_failure": critical_failure,
                }
            )
        return outcomes
