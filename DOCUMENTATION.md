# CrisisForge Technical Documentation

## Overview

CrisisForge is a modular crisis decision-support application built for rapid prototyping and hackathon deployment. The current implementation focuses on deterministic orchestration, reproducible risk modeling, and a professional operator-facing interface.

## Agent design

### Data Scout

- Infers a supported city from the free-text scenario
- Extracts estimated population, baseline severity, and available resources
- Calls Open-Meteo for live weather context when a matching city is found
- Produces lightweight situation headlines for operator review

### Risk Forecaster

- Consumes extracted crisis severity and weather stress
- Runs 1,200 seeded Monte Carlo simulations
- Estimates operational delay, shelter overload probability, and critical failure probability

### Action Optimizer

- Builds a shortlist of candidate response strategies
- Scores each strategy across speed, coverage, fairness, resource fit, and risk resistance
- Recommends the highest-ranked plan and preserves alternatives for auditability

### Ethical Guardian

- Applies simple policy checks for vulnerable-group prioritization, coverage threshold, geographic fairness, and resource equity
- Flags recommendations that do not meet high-severity fairness criteria

## UI design

The Streamlit interface is designed to look formal and submission-ready rather than experimental. It includes:

- A restrained editorial visual style
- Crisis templates for fast demos
- A prominent recommended-plan section
- Agent-by-agent reasoning traces
- Tabular ranking and fairness outputs
- Optional generated audio briefing

## Extensibility

The current architecture is intentionally simple to keep the project hackathon-friendly. It can be extended with:

- Real geocoding instead of a fixed location map
- Additional data providers such as traffic, tides, and river-level feeds
- LLM-backed reasoning layers for narrative synthesis
- More advanced fairness policies and protected-group auditing
- Exportable incident reports and PDF briefings
