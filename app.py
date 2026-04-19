from __future__ import annotations

import streamlit as st

from agents.orchestrator import CrisisOrchestrator
from utils.formatting import build_markdown_plan, build_voice_briefing
from utils.visualization import build_fairness_frame, build_plan_frame, build_timeline_frame
from utils.voice import synthesize_briefing


st.set_page_config(
    page_title="CrisisForge",
    page_icon="CF",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        """
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
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(177,66,46,0.16), transparent 26%),
                radial-gradient(circle at top right, rgba(31,106,92,0.14), transparent 28%),
                linear-gradient(180deg, #f8f3ec 0%, #f3ede4 100%);
            color: var(--ink);
        }

        html, body, [class*="css"] {
            font-family: "Instrument Sans", sans-serif;
        }

        h1, h2, h3 {
            letter-spacing: -0.02em;
            color: var(--ink);
        }

        .mono, code, pre {
            font-family: "IBM Plex Mono", monospace;
        }

        .hero {
            padding: 1.6rem 1.8rem;
            border: 1px solid var(--line);
            border-radius: 24px;
            background: linear-gradient(135deg, rgba(255,250,242,0.92), rgba(255,255,255,0.6));
            backdrop-filter: blur(8px);
            box-shadow: 0 18px 60px rgba(24,31,43,0.08);
            margin-bottom: 1rem;
        }

        .metric-card {
            padding: 1rem 1.1rem;
            border-radius: 18px;
            background: var(--surface);
            border: 1px solid var(--line);
            min-height: 112px;
        }

        .metric-label {
            font-size: 0.78rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: var(--muted);
            margin-bottom: 0.45rem;
        }

        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--ink);
        }

        .metric-sub {
            color: var(--muted);
            font-size: 0.92rem;
        }

        .section-card {
            padding: 1.1rem 1.2rem;
            border-radius: 20px;
            background: rgba(255,255,255,0.68);
            border: 1px solid var(--line);
        }

        .agent-pill {
            display: inline-block;
            padding: 0.25rem 0.55rem;
            border-radius: 999px;
            background: rgba(177,66,46,0.10);
            color: var(--accent);
            font-size: 0.78rem;
            margin-right: 0.35rem;
            border: 1px solid rgba(177,66,46,0.15);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def template_prompts() -> dict[str, str]:
    return {
        "Coastal Flood": "Severe flood in coastal Mumbai affecting 10000 people, limited rescue boats, submerged roads, and an incoming cyclone within 8 hours.",
        "Cyclone Landfall": "A cyclone is expected to make landfall near Chennai. 7000 people are at risk, shelters are partially full, and hospital access is constrained.",
        "Urban Heatwave": "A severe urban heatwave in Delhi is affecting low-income neighborhoods, straining hospitals, and causing power outages across critical facilities.",
    }


def main() -> None:
    inject_styles()
    orchestrator = CrisisOrchestrator()
    presets = template_prompts()

    st.markdown(
        """
        <div class="hero">
            <div class="mono" style="font-size:0.82rem; color:#b1422e; margin-bottom:0.7rem;">MULTI-AGENT CRISIS DECISION INTELLIGENCE</div>
            <h1 style="margin:0;">CrisisForge</h1>
            <p style="max-width:840px; color:#4c5d70; font-size:1.05rem; margin-top:0.8rem;">
                A professional decision-support workspace for disaster response. CrisisForge gathers situational data,
                forecasts operational risk, ranks response strategies, and validates fairness before issuing a clear action plan.
            </p>
            <div style="margin-top:0.8rem;">
                <span class="agent-pill">Data Scout</span>
                <span class="agent-pill">Risk Forecaster</span>
                <span class="agent-pill">Action Optimizer</span>
                <span class="agent-pill">Ethical Guardian</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.sidebar:
        st.header("Scenario Input")
        selected_template = st.selectbox("Crisis Template", ["Custom"] + list(presets.keys()))
        default_prompt = presets.get(selected_template, "")
        crisis_text = st.text_area(
            "Describe the crisis",
            value=default_prompt,
            height=180,
            placeholder="Describe the location, people affected, available resources, and immediate risks.",
        )
        run_analysis = st.button("Run Crisis Analysis", type="primary", use_container_width=True)
        st.caption("Open-Meteo is used when a supported city is detected. Voice generation is optional and handled gracefully if unavailable.")

    if not run_analysis:
        st.info("Enter a scenario and run the analysis to generate the multi-agent response plan.")
        return

    if not crisis_text.strip():
        st.warning("Please enter a crisis scenario before running the analysis.")
        return

    with st.spinner("Running agent collaboration and synthesizing the response plan..."):
        result = orchestrator.run(crisis_text)
        voice_text = build_voice_briefing(result)
        audio_bytes = synthesize_briefing(voice_text)

    final_plan = result["final_plan"]
    location = result["agent_outputs"]["Data Scout"]["details"]["location"]

    metric_cols = st.columns(4)
    metrics = [
        ("Location", location, "Primary crisis region"),
        ("Confidence", f"{final_plan['overall_confidence']:.0%}", "Cross-agent confidence"),
        ("Risk Level", f"{final_plan['overall_risk']:.0%}", "Forecast operational risk"),
        ("Reach", str(final_plan["expected_people_reached"]), "Estimated people reached"),
    ]
    for col, metric in zip(metric_cols, metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{metric[0]}</div>
                    <div class="metric-value">{metric[1]}</div>
                    <div class="metric-sub">{metric[2]}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    left, right = st.columns([1.2, 0.8], gap="large")
    with left:
        st.markdown('<div class="section-card">', unsafe_allow_html=True)
        st.markdown(build_markdown_plan(result))
        st.markdown("</div>", unsafe_allow_html=True)
        st.subheader("Agent Timeline")
        st.dataframe(build_timeline_frame(result), use_container_width=True, hide_index=True)
        st.subheader("Strategy Ranking")
        st.dataframe(build_plan_frame(result), use_container_width=True, hide_index=True)

    with right:
        st.subheader("Reasoning Trace")
        for agent_name, payload in result["agent_outputs"].items():
            with st.expander(f"{agent_name} | confidence {payload['confidence']:.0%}", expanded=agent_name == "Data Scout"):
                st.write(payload["summary"])
                st.json(payload["details"])

        st.subheader("Fairness Review")
        st.dataframe(build_fairness_frame(result), use_container_width=True, hide_index=True)

        st.subheader("Voice Briefing")
        st.code(voice_text)
        if audio_bytes:
            st.audio(audio_bytes, format="audio/mp3")
        else:
            st.caption("Voice synthesis is unavailable in the current environment, but the text briefing has been generated.")


if __name__ == "__main__":
    main()
