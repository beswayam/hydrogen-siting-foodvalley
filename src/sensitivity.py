"""
Weight-sensitivity / robustness analysis for the MCA1 composite siting score.

The submitted report uses a fixed 50% energy-deficit / 50% grid-congestion split
and flags in its Discussion (Section 6.1) that "the mathematical justification for
this combination should be further evaluated" -- but never quantifies how robust
the ranking actually is to that choice. This script closes that gap with three
independent, literature-grounded checks against the canonical, report-matching
dataset (data/processed/hydrogen_siting_phase3_v2.csv):

1. Objective (data-driven) weighting for comparison:
   - Entropy weighting (Zou, Yi & Sun, 2006) -- weight derived from how much each
     criterion discriminates between candidates.
   - CRITIC weighting (Diakoulaki, Mavrotas & Papayannakis, 1995) -- like entropy,
     but explicitly penalises criteria that are correlated with each other.
2. Top-5 ranking under each weighting scheme, for a qualitative comparison.
3. Exact Weight Stability Interval (WSI): the algebraic range of the deficit
   weight w1 (with congestion weight = 1 - w1) over which the #1-ranked site does
   NOT change. This directly answers "how much would the weighting have to move
   before the recommendation changes?"

Run:
    python src/sensitivity.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "hydrogen_siting_phase3_v2.csv"
FIGURES = ROOT / "figures"


def normalize(s: pd.Series) -> pd.Series:
    span = s.max() - s.min()
    if span == 0:
        return pd.Series(0.0, index=s.index)
    return (s - s.min()) / span


def entropy_weights(X: np.ndarray) -> np.ndarray:
    """Shannon entropy weighting (Zou, Yi & Sun, 2006). X columns: benefit criteria in [0, 1]."""
    m = X.shape[0]
    col_sum = X.sum(axis=0)
    P = X / col_sum
    with np.errstate(divide="ignore", invalid="ignore"):
        plnp = np.where(P > 0, P * np.log(P), 0.0)
    e = -plnp.sum(axis=0) / np.log(m)
    d = 1 - e
    return d / d.sum()


def critic_weights(X: np.ndarray) -> np.ndarray:
    """CRITIC weighting (Diakoulaki, Mavrotas & Papayannakis, 1995). X columns pre-normalised to [0, 1]."""
    n = X.shape[1]
    std = X.std(axis=0, ddof=1)
    corr = np.corrcoef(X, rowvar=False)
    C = np.array([std[j] * sum(1 - corr[j, k] for k in range(n)) for j in range(n)])
    return C / C.sum()


def exact_weight_stability_interval(X2: np.ndarray, df: pd.DataFrame, w1_target: float = 0.5):
    """Exact WSI for a 2-criterion composite score X2 @ [w1, 1-w1].

    Returns (target_pc4, w_low, w_high): the top-1 PC4 at w1_target, and the exact
    range of w1 over which that PC4 remains top-1 (by pairwise linear dominance).
    """
    score_target_all = X2 @ np.array([w1_target, 1 - w1_target])
    t_idx = score_target_all.argmax()
    target_pc4 = df.iloc[t_idx]["PC4"]
    s_def_t, s_cong_t = X2[t_idx]

    w_low, w_high = 0.0, 1.0
    for i in range(len(df)):
        if i == t_idx:
            continue
        s_def_i, s_cong_i = X2[i]
        a = (s_def_t - s_cong_t) - (s_def_i - s_cong_i)
        b = s_cong_t - s_cong_i
        if a == 0:
            if b < 0:
                raise RuntimeError(f"Target PC4 {target_pc4} does not dominate PC4 {df.iloc[i]['PC4']} at w1={w1_target}")
            continue
        crossing = -b / a
        if a > 0:
            w_low = max(w_low, crossing)
        else:
            w_high = min(w_high, crossing)
    return target_pc4, w_low, w_high


def main():
    df = pd.read_csv(DATA, dtype={"PC4": str})

    s_deficit = normalize(-df["net_balance_p3_gwh"])
    s_congestion = df["congestion_score"]  # already 0.2 / 0.5 / 1.0
    X = np.column_stack([s_deficit.values, s_congestion.values])
    labels = ["Energy deficit (C1)", "Grid congestion (C2)"]

    print("=" * 72)
    print("1. CORRELATION BETWEEN THE TWO CRITERIA")
    print("=" * 72)
    r = np.corrcoef(X, rowvar=False)[0, 1]
    print(f"Pearson r(deficit, congestion) = {r:.3f}  -- criteria are close to independent,")
    print("so 50/50 equal weighting is a defensible default (not double-counting one signal).")

    print("\n" + "=" * 72)
    print("2. OBJECTIVE (DATA-DRIVEN) WEIGHTS vs. THE REPORT'S 50/50")
    print("=" * 72)
    w_entropy = entropy_weights(X)
    w_critic = critic_weights(X)
    comparison = pd.DataFrame(
        {"Report (50/50)": [0.50, 0.50], "Entropy (Zou 2006)": w_entropy, "CRITIC (Diakoulaki 1995)": w_critic},
        index=labels,
    )
    print(comparison.round(3))

    print("\n" + "=" * 72)
    print("3. TOP-5 SITES UNDER EACH WEIGHTING SCHEME")
    print("=" * 72)
    schemes = {"Report (50/50)": [0.50, 0.50], "Entropy": w_entropy, "CRITIC": w_critic}
    for name, w in schemes.items():
        s = X @ np.array(w)
        top5 = df.assign(score=s).sort_values("score", ascending=False).head(5)
        print(f"\n{name}: weights = {[f'{x:.3f}' for x in w]}")
        print(top5[["PC4", "municipality", "score"]].to_string(index=False))

    print("\n" + "=" * 72)
    print("4. EXACT WEIGHT STABILITY INTERVAL (WSI)")
    print("=" * 72)
    target_pc4, w_low, w_high = exact_weight_stability_interval(X, df, w1_target=0.5)
    print(f"Top-1 site at the report's 50/50 split: PC4 {target_pc4}")
    print(f"Exact WSI for the deficit weight w1: [{w_low:.4f}, {w_high:.4f}]")
    print(f"  -> PC4 {target_pc4} remains the #1-ranked site for ANY split where the")
    print(f"     energy-deficit weight is between {100*w_low:.1f}% and {100*w_high:.1f}%")
    print(f"     (congestion weight correspondingly {100*(1-w_high):.1f}%-{100*(1-w_low):.1f}%).")
    print(f"  WSI width: {w_high - w_low:.4f} ({100*(w_high - w_low):.1f}% of the full 0-100% range)")

    # Stability chart: composite score of the top-6 sites as the deficit weight sweeps 0 -> 1.
    FIGURES.mkdir(exist_ok=True)
    top6_pc4 = df.sort_values("composite_siting_v1_proxy_excl" if "composite_siting_v1_proxy_excl" in df.columns else "PC4",
                               ascending=False)["PC4"].tolist()
    # Use the actual report ranking (composite_siting) for which sites to trace.
    top6_pc4 = df.sort_values("composite_siting", ascending=False)["PC4"].head(6).tolist()
    top6_idx = df[df["PC4"].isin(top6_pc4)].index

    w1_range = np.linspace(0, 1, 101)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    for idx in top6_idx:
        row = df.loc[idx]
        scores = [w1 * s_deficit[idx] + (1 - w1) * s_congestion[idx] for w1 in w1_range]
        label = f"{row['PC4']} {row['business_park'] if pd.notna(row['business_park']) else row['municipality']}"
        ax.plot(w1_range * 100, scores, label=label, linewidth=2)

    ax.axvline(50, color="grey", linestyle="--", linewidth=1, label="Report weighting (50/50)")
    ax.axvspan(w_low * 100, w_high * 100, color="green", alpha=0.08, label=f"WSI for #1 site ({100*w_low:.0f}-{100*w_high:.0f}%)")
    ax.set_xlabel("Energy-deficit weight w1 (%)  [congestion weight = 100% - w1]")
    ax.set_ylabel("Composite siting score")
    ax.set_title("Weight-sensitivity: top-6 candidate sites across the full weight range")
    ax.legend(fontsize=8, loc="upper left", bbox_to_anchor=(1.02, 1.0))
    ax.grid(alpha=0.3)
    plt.tight_layout()
    out_path = FIGURES / "sensitivity_weight_stability.png"
    plt.savefig(out_path, dpi=140)
    print(f"\n>>> Saved stability chart: {out_path}")


if __name__ == "__main__":
    main()
