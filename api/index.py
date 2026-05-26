from __future__ import annotations

from flask import Flask, jsonify, request

from agents.orchestrator import CrisisOrchestrator
from utils.formatting import build_markdown_plan, build_voice_briefing


app = Flask(__name__)
orchestrator = CrisisOrchestrator()


@app.get("/")
def healthcheck():
    return jsonify(
        {
            "name": "CrisisForge API",
            "status": "ok",
            "endpoints": {
                "health": "GET /",
                "analyze": "POST /analyze",
            },
        }
    )


@app.post("/analyze")
def analyze():
    payload = request.get_json(silent=True) or {}
    crisis_text = (payload.get("crisis_text") or "").strip()

    if not crisis_text:
        return jsonify({"error": "crisis_text is required"}), 400

    result = orchestrator.run(crisis_text)
    return jsonify(
        {
            "result": result,
            "markdown_plan": build_markdown_plan(result),
            "voice_briefing": build_voice_briefing(result),
        }
    )

