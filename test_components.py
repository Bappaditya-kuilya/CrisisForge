from agents.orchestrator import CrisisOrchestrator
from utils.formatting import build_voice_briefing


def test_orchestrator_returns_plan() -> None:
    orchestrator = CrisisOrchestrator()
    result = orchestrator.run(
        "Severe flood in coastal Mumbai affecting 10000 people with limited rescue boats and incoming cyclone conditions."
    )
    assert result["final_plan"]["title"]
    assert len(result["timeline"]) == 4
    assert result["final_plan"]["expected_people_reached"] > 0


def test_voice_briefing_is_nonempty() -> None:
    orchestrator = CrisisOrchestrator()
    result = orchestrator.run("Cyclone threat near Chennai affecting 7000 people.")
    briefing = build_voice_briefing(result)
    assert "CrisisForge briefing" in briefing


def test_region_name_is_resolved_from_free_text() -> None:
    orchestrator = CrisisOrchestrator()
    result = orchestrator.run(
        "Flash flood in North 24 Parganas affecting 15000 residents with blocked roads and limited shelters."
    )
    assert "Parganas" in result["final_plan"]["location"]
    assert result["final_plan"]["hazard_type"] == "flood"
