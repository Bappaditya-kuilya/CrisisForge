# CrisisForge

CrisisForge is a professional multi-agent AI decision-support system for crisis response. It transforms a plain-language emergency scenario into a structured action plan by combining situational intelligence, probabilistic forecasting, strategy ranking, and fairness review.

## Features

- Four specialized agents with clear responsibilities
- Probabilistic risk forecasting using Monte Carlo simulation
- Response strategy ranking with transparent scoring
- Fairness and bias review before final recommendation
- Streamlit interface with reasoning traces and voice briefing
- Open-Meteo integration for live weather context when supported locations are detected

## Architecture

The system is organized around a sequential orchestration pipeline:

1. `Data Scout` extracts crisis signals, identifies supported locations, and retrieves live weather data when possible.
2. `Risk Forecaster` runs Monte Carlo simulations to estimate delay, overload, and failure probabilities.
3. `Action Optimizer` evaluates competing response strategies and recommends the highest-value plan.
4. `Ethical Guardian` validates whether the proposed response meets fairness and access criteria.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Vercel

Vercel cannot run `streamlit run app.py` directly as a production entrypoint. This repository now includes a serverless Python API for deployment:

```bash
POST /analyze
Content-Type: application/json

{
  "crisis_text": "Severe flood in coastal Mumbai affecting 10000 people, limited rescue boats, submerged roads, and an incoming cyclone within 8 hours."
}
```

The root route `GET /` returns a small healthcheck payload. The Streamlit interface remains available for local development.

## Project structure

```text
crisisforge/
├── app.py
├── agents/
│   ├── action_optimizer.py
│   ├── base.py
│   ├── data_scout.py
│   ├── ethical_guardian.py
│   ├── orchestrator.py
│   └── risk_forecaster.py
├── utils/
│   ├── formatting.py
│   ├── visualization.py
│   └── voice.py
├── requirements.txt
├── README.md
├── DOCUMENTATION.md
└── test_components.py
```

## Notes

- The app runs without API keys.
- Open-Meteo is used directly for supported city lookups and does not require authentication.
- Voice generation is optional and fails gracefully if the runtime blocks it.
