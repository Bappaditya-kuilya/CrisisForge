from __future__ import annotations

from typing import Any, Dict


def build_voice_briefing(result: Dict[str, Any]) -> str:
    plan = result["final_plan"]
    location = plan["location"]
    return (
        f"CrisisForge briefing for {location}. "
        f"Primary hazard: {plan['hazard_type']}. "
        f"Recommended plan: {plan['title']}. "
        f"Estimated operational risk is {plan['overall_risk']:.0%}. "
        f"Expected reach is {plan['expected_people_reached']} people. "
        f"Overall confidence is {plan['overall_confidence']:.0%}. "
        f"Priority actions: {plan['steps'][0]} Then, {plan['steps'][1]}"
    )


def build_markdown_plan(result: Dict[str, Any]) -> str:
    plan = result["final_plan"]
    steps = "\n".join(f"{idx}. {step}" for idx, step in enumerate(plan["steps"], start=1))
    urgency_line = (
        f"**Critical Window:** {plan['urgency_hours']} hours\n\n"
        if plan["urgency_hours"]
        else ""
    )
    constraint_line = (
        f"**Primary Constraint:** {plan['constraints'][0]}\n\n"
        if plan["constraints"]
        else ""
    )
    return (
        f"### Recommended Response Plan\n"
        f"**Location:** {plan['location']}\n\n"
        f"**Primary Hazard:** {plan['hazard_type']}\n\n"
        f"**Plan:** {plan['title']}\n\n"
        f"**Plan Score:** {plan['score']}/100\n\n"
        f"**Operational Risk:** {plan['overall_risk']:.0%}\n\n"
        f"**Expected Reach:** {plan['expected_people_reached']} people\n\n"
        f"{urgency_line}"
        f"{constraint_line}"
        f"**Ethics Review:** {'Approved' if plan['ethics_approved'] else 'Needs revision'}\n\n"
        f"### Action Steps\n{steps}"
    )
