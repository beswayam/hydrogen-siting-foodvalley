"""
Regression tests: the open-source pipeline (src/pipeline.py), run against the
real raw Liander/Stedin data in data/raw/, must keep reproducing the
submitted report's #1 finding and stay close to its full top-10 ranking.

These exist because README.md and CASE_STUDY.md make specific, checkable
claims ("reproduces PC4 3771 as #1 with score 0.7500", "9/10 top-10 overlap")
-- this file is what keeps those claims honest as the code changes.
"""

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pipeline import PROCESSED, build_pc4_table, score  # noqa: E402


@pytest.fixture(scope="module")
def scored():
    return score(build_pc4_table())


@pytest.fixture(scope="module")
def canonical():
    return pd.read_csv(PROCESSED / "hydrogen_siting_phase3_v2.csv", dtype={"PC4": str})


def test_top1_matches_canonical_exactly(scored):
    top1 = scored.iloc[0]
    assert top1["PC4"] == "3771"
    assert top1["composite_siting"] == pytest.approx(0.7500, abs=1e-4)


def test_top10_overlap_with_canonical_at_least_nine(scored, canonical):
    canonical_top10 = set(
        canonical.sort_values("composite_siting", ascending=False)["PC4"].head(10)
    )
    reproduced_top10 = set(scored["PC4"].head(10))
    overlap = len(canonical_top10 & reproduced_top10)
    assert overlap >= 9, f"expected >=9/10 overlap, got {overlap}/10"


def test_artefact_pc4s_excluded(scored):
    excluded = {"3905", "3925", "3927"}
    assert excluded.isdisjoint(set(scored["PC4"]))


def test_composite_score_bounded(scored):
    assert scored["composite_siting"].between(0, 1).all()
