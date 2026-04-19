from __future__ import annotations

from typing import Any, Dict


def build_voice_briefing(result: Dict[str, Any]) -> str:
    plan = result["final_plan"]
    location = result["agent_outputs"]["Data Scout"]["details"]["location"]
    return (
        f"CrisisForge briefing for {location}. "
        f"Recommended plan: {plan['title']}. "
        f"Estimated operational risk is {plan['overall_risk']:.0%}. "
        f"Expected reach is {plan['expected_people_reached']} people. "
        f"Overall confidence is {plan['overall_confidence']:.0%}. "
        f"Priority actions: {plan['steps'][0]} Then, {plan['steps'][1]}"
    )


def build_markdown_plan(result: Dict[str, Any]) -> str:
    plan = result["final_plan"]
    steps = "\n".join(f"{idx}. {step}" for idx, step in enumerate(plan["steps"], start=1))
    return (
        f"### Recommended Response Plan\n"
        f"**Plan:** {plan['title']}\n\n"
        f"**Plan Score:** {plan['score']}/100\n\n"
        f"**Operational Risk:** {plan['overall_risk']:.0%}\n\n"
        f"**Expected Reach:** {plan['expected_people_reached']} people\n\n"
        f"**Ethics Review:** {'Approved' if plan['ethics_approved'] else 'Needs revision'}\n\n"
        f"### Action Steps\n{steps}"
    )

