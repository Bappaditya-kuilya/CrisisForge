from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def build_timeline_frame(result: Dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(result["timeline"])


def build_plan_frame(result: Dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(result["agent_outputs"]["Action Optimizer"]["details"]["ranking_table"])


def build_fairness_frame(result: Dict[str, Any]) -> pd.DataFrame:
    return pd.DataFrame(result["agent_outputs"]["Ethical Guardian"]["details"]["checks"])

