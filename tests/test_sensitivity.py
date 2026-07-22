"""
Regression tests for the weight-robustness analysis (src/sensitivity.py).

The dashboard's stability badge and the README/CASE_STUDY both make a specific
claim: "PC4 3771 (Harselaar) stays #1 for any deficit weight in [47%, 100%]".
These tests pin that number down so a future change to the canonical dataset
or the scoring logic can't silently drift without being noticed.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from sensitivity import (  # noqa: E402
    DATA,
    critic_weights,
    entropy_weights,
    exact_weight_stability_interval,
    normalize,
)


@pytest.fixture(scope="module")
def canonical():
    return pd.read_csv(DATA, dtype={"PC4": str})


@pytest.fixture(scope="module")
def criteria_matrix(canonical):
    s_deficit = normalize(-canonical["net_balance_p3_gwh"])
    s_congestion = canonical["congestion_score"]
    return np.column_stack([s_deficit.values, s_congestion.values])


def test_wsi_matches_documented_range(criteria_matrix, canonical):
    target_pc4, w_low, w_high = exact_weight_stability_interval(criteria_matrix, canonical, w1_target=0.5)
    assert target_pc4 == "3771"
    assert w_low == pytest.approx(0.4696, abs=1e-3)
    assert w_high == pytest.approx(1.0, abs=1e-6)


def test_weights_sum_to_one(criteria_matrix):
    assert entropy_weights(criteria_matrix).sum() == pytest.approx(1.0, abs=1e-9)
    assert critic_weights(criteria_matrix).sum() == pytest.approx(1.0, abs=1e-9)


def test_critic_weighting_flips_top1(criteria_matrix, canonical):
    """Below the WSI lower bound, the #1 site must actually change (this is the
    dashboard's 'Changed' badge state) -- confirms the flip isn't a rounding
    artefact of the UI but a real property of the underlying scores."""
    w_critic = critic_weights(criteria_matrix)
    critic_scores = criteria_matrix @ w_critic
    top1_critic = canonical.iloc[critic_scores.argmax()]["PC4"]
    assert top1_critic == "3901"
    assert top1_critic != "3771"
