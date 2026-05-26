from __future__ import annotations

from flask import Flask, jsonify, render_template_string, request

from agents.orchestrator import CrisisOrchestrator
from utils.formatting import build_markdown_plan, build_voice_briefing


app = Flask(__name__)
orchestrator = CrisisOrchestrator()
PRESETS = {
    "Coastal Flood": "Severe flood in coastal Mumbai affecting 10000 people, limited rescue boats, submerged roads, and an incoming cyclone within 8 hours.",
    "Cyclone Landfall": "A cyclone is expected to make landfall near Chennai. 7000 people are at risk, shelters are partially full, and hospital access is constrained.",
    "Urban Heatwave": "A severe urban heatwave in Delhi is affecting low-income neighborhoods, straining hospitals, and causing power outages across critical facilities.",
}
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>CrisisForge</title>
  <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Instrument+Sans:wght@400;500;600;700&display=swap');

    :root {
      --bg: #f4efe7;
      --surface: rgba(255,255,255,0.72);
      --surface-strong: #fffaf2;
      --ink: #132238;
      --muted: #5f6f82;
      --accent: #b1422e;
      --accent-2: #1f6a5c;
      --line: rgba(19,34,56,0.12);
      --shadow: 0 18px 60px rgba(24,31,43,0.08);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      font-family: "Instrument Sans", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(177,66,46,0.16), transparent 26%),
        radial-gradient(circle at top right, rgba(31,106,92,0.14), transparent 28%),
        linear-gradient(180deg, #f8f3ec 0%, #f3ede4 100%);
      min-height: 100vh;
    }

    .mono, code, pre { font-family: "IBM Plex Mono", monospace; }

    .shell {
      width: min(1200px, calc(100% - 32px));
      margin: 24px auto;
      display: grid;
      grid-template-columns: 340px 1fr;
      gap: 20px;
    }

    .panel, .hero, .card {
      border: 1px solid var(--line);
      border-radius: 24px;
      background: linear-gradient(135deg, rgba(255,250,242,0.92), rgba(255,255,255,0.6));
      backdrop-filter: blur(8px);
      box-shadow: var(--shadow);
    }

    .panel {
      padding: 20px;
      position: sticky;
      top: 24px;
      height: fit-content;
    }

    .hero {
      padding: 26px 28px;
      margin-bottom: 18px;
    }

    .hero h1 {
      margin: 0;
      font-size: clamp(2rem, 4vw, 3.6rem);
      letter-spacing: -0.03em;
    }

    .eyebrow, .label {
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      font-size: 0.78rem;
    }

    .eyebrow { color: var(--accent); }

    .hero p {
      color: #4c5d70;
      max-width: 840px;
      line-height: 1.55;
    }

    .pill-row {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 14px;
    }

    .pill {
      display: inline-block;
      padding: 0.32rem 0.7rem;
      border-radius: 999px;
      background: rgba(177,66,46,0.10);
      color: var(--accent);
      border: 1px solid rgba(177,66,46,0.15);
      font-size: 0.8rem;
    }

    .content {
      display: flex;
      flex-direction: column;
      gap: 18px;
    }

    .input-block {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    select, textarea, button {
      width: 100%;
      border-radius: 16px;
      border: 1px solid var(--line);
      font: inherit;
    }

    select, textarea {
      background: rgba(255,255,255,0.8);
      color: var(--ink);
      padding: 14px 16px;
    }

    textarea {
      min-height: 220px;
      resize: vertical;
      line-height: 1.45;
    }

    button {
      background: linear-gradient(135deg, var(--accent), #8e3424);
      color: white;
      padding: 14px 18px;
      font-weight: 700;
      cursor: pointer;
    }

    button:disabled {
      opacity: 0.7;
      cursor: wait;
    }

    .hint {
      color: var(--muted);
      font-size: 0.92rem;
      line-height: 1.45;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 14px;
    }

    .card {
      padding: 18px;
    }

    .metric {
      font-size: 1.85rem;
      font-weight: 700;
      margin: 6px 0;
    }

    .muted {
      color: var(--muted);
      font-size: 0.94rem;
    }

    .section-title {
      margin: 0 0 12px 0;
      font-size: 1.1rem;
    }

    .plan {
      white-space: pre-wrap;
      line-height: 1.55;
    }

    .table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.95rem;
    }

    .table th, .table td {
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }

    .trace {
      display: grid;
      gap: 12px;
    }

    .trace-item {
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 14px;
      background: rgba(255,255,255,0.56);
    }

    .empty {
      padding: 26px;
      text-align: center;
      color: var(--muted);
    }

    .error {
      color: #8e3424;
      background: rgba(177,66,46,0.08);
      border: 1px solid rgba(177,66,46,0.16);
      border-radius: 16px;
      padding: 14px 16px;
    }

    @media (max-width: 980px) {
      .shell {
        grid-template-columns: 1fr;
      }

      .panel {
        position: static;
      }

      .grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <aside class="panel">
      <div class="input-block">
        <div>
          <div class="label">Scenario Input</div>
          <h2 style="margin:8px 0 0 0;">Run Crisis Analysis</h2>
        </div>
        <label class="label" for="preset">Crisis Template</label>
        <select id="preset">
          <option value="">Custom</option>
          {% for name in presets %}
          <option value="{{ name }}">{{ name }}</option>
          {% endfor %}
        </select>
        <label class="label" for="crisisText">Describe the crisis</label>
        <textarea id="crisisText" placeholder="Describe the location, people affected, available resources, and immediate risks."></textarea>
        <button id="runButton">Run Crisis Analysis</button>
        <div class="hint">Open-Meteo is used when a supported city is detected. Voice generation is optional and may be unavailable in some runtimes.</div>
      </div>
    </aside>

    <main class="content">
      <section class="hero">
        <div class="mono eyebrow">MULTI-AGENT CRISIS DECISION INTELLIGENCE</div>
        <h1>CrisisForge</h1>
        <p>A professional decision-support workspace for disaster response. CrisisForge gathers situational data, forecasts operational risk, ranks response strategies, and validates fairness before issuing a clear action plan.</p>
        <div class="pill-row">
          <span class="pill">Data Scout</span>
          <span class="pill">Risk Forecaster</span>
          <span class="pill">Action Optimizer</span>
          <span class="pill">Ethical Guardian</span>
        </div>
      </section>

      <div id="status" class="card empty">Enter a scenario and run the analysis to generate the multi-agent response plan.</div>
      <div id="results" style="display:none;">
        <section class="grid" id="metrics"></section>
        <section class="card">
          <h3 class="section-title">Action Plan</h3>
          <div id="plan" class="plan"></div>
        </section>
        <section class="grid">
          <div class="card">
            <h3 class="section-title">Agent Timeline</h3>
            <div id="timeline"></div>
          </div>
          <div class="card">
            <h3 class="section-title">Voice Briefing</h3>
            <pre id="voice" class="plan mono"></pre>
          </div>
        </section>
        <section class="grid">
          <div class="card">
            <h3 class="section-title">Strategy Ranking</h3>
            <div id="ranking"></div>
          </div>
          <div class="card">
            <h3 class="section-title">Fairness Review</h3>
            <div id="fairness"></div>
          </div>
        </section>
        <section class="card">
          <h3 class="section-title">Agent Trace</h3>
          <div id="trace" class="trace"></div>
        </section>
      </div>
    </main>
  </div>

  <script>
    const presets = {{ presets_json | safe }};
    const presetEl = document.getElementById("preset");
    const crisisTextEl = document.getElementById("crisisText");
    const runButton = document.getElementById("runButton");
    const statusEl = document.getElementById("status");
    const resultsEl = document.getElementById("results");

    presetEl.addEventListener("change", () => {
      crisisTextEl.value = presets[presetEl.value] || "";
    });

    const escapeHtml = (value) =>
      String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");

    const renderTable = (columns, rows) => {
      const head = columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join("");
      const body = rows.map((row) => {
        const cells = columns.map((column) => `<td>${escapeHtml(column.value(row))}</td>`).join("");
        return `<tr>${cells}</tr>`;
      }).join("");
      return `<table class="table"><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
    };

    const renderResults = (payload) => {
      const result = payload.result;
      const plan = result.final_plan;
      const scout = result.agent_outputs["Data Scout"].details;
      const ranking = result.agent_outputs["Action Optimizer"].details.ranking_table;
      const fairness = result.agent_outputs["Ethical Guardian"].details.checks;

      document.getElementById("metrics").innerHTML = [
        ["Location", scout.location, "Primary crisis region"],
        ["Hazard", plan.hazard_type, "Detected crisis type"],
        ["Confidence", `${Math.round(plan.overall_confidence * 100)}%`, "Cross-agent confidence"],
        ["Risk Level", `${Math.round(plan.overall_risk * 100)}%`, "Forecast operational risk"],
      ].map(([label, value, sub]) => `
        <article class="card">
          <div class="label">${escapeHtml(label)}</div>
          <div class="metric">${escapeHtml(value)}</div>
          <div class="muted">${escapeHtml(sub)}</div>
        </article>
      `).join("");

      document.getElementById("plan").textContent = payload.markdown_plan;
      document.getElementById("voice").textContent = payload.voice_briefing;

      document.getElementById("timeline").innerHTML = renderTable(
        [
          { label: "Agent", value: (row) => row.agent },
          { label: "Summary", value: (row) => row.summary },
          { label: "Confidence", value: (row) => `${Math.round(row.confidence * 100)}%` },
        ],
        result.timeline
      );

      document.getElementById("ranking").innerHTML = renderTable(
        [
          { label: "Plan", value: (row) => row.name },
          { label: "Score", value: (row) => row.score },
          { label: "Expected Reach", value: (row) => row.expected_people_reached },
        ],
        ranking
      );

      document.getElementById("fairness").innerHTML = renderTable(
        [
          { label: "Check", value: (row) => row.name },
          { label: "Status", value: (row) => row.status },
          { label: "Note", value: (row) => row.note },
        ],
        fairness
      );

      document.getElementById("trace").innerHTML = Object.entries(result.agent_outputs).map(([name, payload]) => `
        <section class="trace-item">
          <div class="label">${escapeHtml(name)} | confidence ${Math.round(payload.confidence * 100)}%</div>
          <p>${escapeHtml(payload.summary)}</p>
          <pre class="mono plan">${escapeHtml(JSON.stringify(payload.details, null, 2))}</pre>
        </section>
      `).join("");
    };

    runButton.addEventListener("click", async () => {
      const crisisText = crisisTextEl.value.trim();
      if (!crisisText) {
        statusEl.className = "error";
        statusEl.textContent = "Please enter a crisis scenario before running the analysis.";
        resultsEl.style.display = "none";
        return;
      }

      runButton.disabled = true;
      statusEl.className = "card empty";
      statusEl.textContent = "Running agent collaboration and synthesizing the response plan...";

      try {
        const response = await fetch("/analyze", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ crisis_text: crisisText }),
        });
        const payload = await response.json();

        if (!response.ok) {
          throw new Error(payload.error || "Analysis request failed.");
        }

        renderResults(payload);
        statusEl.style.display = "none";
        resultsEl.style.display = "block";
      } catch (error) {
        statusEl.style.display = "block";
        statusEl.className = "error";
        statusEl.textContent = error.message || "Analysis request failed.";
        resultsEl.style.display = "none";
      } finally {
        runButton.disabled = false;
      }
    });
  </script>
</body>
</html>
"""


@app.get("/")
def index():
    return render_template_string(
        INDEX_HTML,
        presets=PRESETS.keys(),
        presets_json=jsonify(PRESETS).get_data(as_text=True),
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
