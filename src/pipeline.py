"""
MCA1 pipeline: regional (PC4-level) hydrogen-hub siting score for Regio Foodvalley.

Reproduces the composite siting score used in Table 4 of the submitted ACT report
("Relieving grid congestion with hydrogen") from public open data:

    composite_siting = 0.5 * energy_deficit_score + 0.5 * grid_congestion_score

Where:
  - energy_deficit_score is the min-max normalised gap between local renewable
    supply and local electricity demand (demand corrected for the "invisible
    factory" problem — large industrial connections excluded from public DSO data
    by Dutch privacy law).
  - grid_congestion_score is the official Netbeheer Nederland Capaciteitskaart
    status, mapped RED=1.0 / AMBER=0.5 / GREEN=0.2.

See data/sources.md for exactly which inputs are raw (parsed here from the real
Liander/Stedin open-data exports) vs. small reference tables reused from the
report's already-published, independently-verified figures.

Run:
    python src/pipeline.py
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

FOODVALLEY_PC4_PREFIXES = {
    "3771", "3772", "3773", "3774", "3775", "3776",
    "3781", "3784", "3785", "3792", "3794",
    "3815", "3821", "3826", "3829",
    "3841", "3842", "3843", "3844", "3846", "3847", "3848", "3849",
    "3851", "3852", "3853",
    "3861", "3862", "3863", "3864", "3871",
    "3881", "3882", "3886", "3891", "3892", "3893", "3894", "3895", "3896", "3898", "3899",
    "3901", "3902", "3903", "3904", "3905", "3906", "3907",
    "3911", "3912",
    "3925",  # excluded later (DSO boundary artefact, see EXCLUDE_ARTEFACT_PC4)
    "3927", "3937",
    "6701", "6702", "6703", "6704", "6705", "6706", "6707", "6708", "6709",
    "6711", "6712", "6713", "6714", "6715", "6716", "6717", "6718",
    "6721", "6731", "6732", "6733",
    "6741", "6744", "6745",
}

# DSO handover artefacts (Liander<->Stedin boundary changes create impossible
# demand/supply ratios). Documented in the report Section 3.3 and
# 05_Analysis/PROJECT_HANDOFF_V3.md Section 8.
EXCLUDE_ARTEFACT_PC4 = {"3905", "3925", "3927"}


def load_demand_by_pc4() -> pd.Series:
    """Real raw data: Liander/Stedin small-connection consumption export.

    Tab-separated, Dutch decimal-comma formatting, PRODUCTSOORT values carry
    trailing whitespace in some years ('ELK     ') — stripped explicitly below.
    """
    df = pd.read_csv(
        RAW / "verbruikdata_kleine_aansluitingen_2026.csv",
        sep="\t",
        decimal=",",
        encoding="utf-8",
        low_memory=False,
    )
    df["PRODUCTSOORT"] = df["PRODUCTSOORT"].astype(str).str.strip().str.upper()
    df["pc4"] = df["POSTCODE"].astype(str).str.strip().str[:4]

    elec = df[(df["PRODUCTSOORT"] == "ELK") & (df["pc4"].isin(FOODVALLEY_PC4_PREFIXES))]
    demand_kwh = elec.groupby("pc4")["SJA_TOTAAL"].sum()
    connections = elec.groupby("pc4")["AANSLUITINGEN_AANTAL"].sum()
    return demand_kwh, connections


def load_feedin_by_pc4() -> pd.Series:
    """Real raw data: Liander/Stedin small-connection feed-in (rooftop PV) export.

    Published with each row wrapped in a stray leading/trailing quote character
    and internally tab-separated -- quoting=3 (QUOTE_NONE) preserves the tabs as
    real delimiters, then the leftover quote characters are stripped by hand.
    """
    df = pd.read_csv(
        RAW / "terugleverdata_kleine_aansluitingen_2026.csv",
        sep="\t",
        encoding="utf-8",
        quoting=3,  # csv.QUOTE_NONE
        low_memory=False,
    )
    df.columns = [c.strip('"').strip() for c in df.columns]
    df["AANSLUITINGEN_AANTAL"] = (
        df["AANSLUITINGEN_AANTAL"].astype(str).str.strip('"').astype(int)
    )
    df["PRODUCTSOORT"] = df["PRODUCTSOORT"].astype(str).str.strip().str.upper()
    df["pc4"] = df["POSTCODE"].astype(str).str.strip().str[:4]

    elec = df[(df["PRODUCTSOORT"] == "ELK") & (df["pc4"].isin(FOODVALLEY_PC4_PREFIXES))]
    feedin_kwh = elec.groupby("pc4")["TOT_E_INV"].sum()
    return feedin_kwh


def load_reference_tables():
    muni = pd.read_csv(RAW / "pc4_municipality_lookup.csv", dtype={"PC4": str})
    renewables = pd.read_csv(RAW / "renewable_supply_by_pc4.csv", dtype={"PC4": str})
    proxy = pd.read_csv(RAW / "industrial_commercial_proxy_by_pc4.csv", dtype={"PC4": str})
    congestion = pd.read_csv(RAW / "congestion_status_by_pc4.csv", dtype={"PC4": str})
    return muni, renewables, proxy, congestion


def normalize(s: pd.Series) -> pd.Series:
    """Min-max normalisation to [0, 1]. Returns 0.0 for a constant column."""
    span = s.max() - s.min()
    if span == 0:
        return pd.Series(0.0, index=s.index)
    return (s - s.min()) / span


def build_pc4_table() -> pd.DataFrame:
    demand_kwh, connections = load_demand_by_pc4()
    feedin_kwh = load_feedin_by_pc4()
    muni, renewables, proxy, congestion = load_reference_tables()

    df = muni.copy()
    df["demand_dso_gwh"] = df["PC4"].map(demand_kwh).fillna(0.0) / 1e6
    df["connections"] = df["PC4"].map(connections).fillna(0.0)
    df["feedin_pv_gwh"] = df["PC4"].map(feedin_kwh).fillna(0.0) / 1e6

    df = df.merge(renewables[["PC4", "solar_park_gwh", "wind_gwh"]], on="PC4", how="left")
    df = df.merge(
        proxy[["PC4", "business_park", "has_biz_park", "biz_gwh", "industrial_proxy_gwh"]],
        on="PC4",
        how="left",
    )
    df = df.merge(congestion[["PC4", "congestion_status", "congestion_score"]], on="PC4", how="left")
    df[["solar_park_gwh", "wind_gwh", "biz_gwh", "industrial_proxy_gwh"]] = df[
        ["solar_park_gwh", "wind_gwh", "biz_gwh", "industrial_proxy_gwh"]
    ].fillna(0.0)

    # Exclude DSO handover artefact PC4s before any scoring.
    before = len(df)
    df = df[~df["PC4"].isin(EXCLUDE_ARTEFACT_PC4)].copy()
    print(f"Excluded {before - len(df)} DSO-boundary-artefact PC4 zones: {sorted(EXCLUDE_ARTEFACT_PC4)}")

    # "Invisible factory" correction: use the industrial proxy where a business
    # park is present, otherwise fall back to the CBS commercial demand proxy.
    df["demand_synthetic_gwh"] = df["demand_dso_gwh"] + np.where(
        df["industrial_proxy_gwh"] > 0, df["industrial_proxy_gwh"], df["biz_gwh"]
    )

    df["total_supply_gwh"] = df["feedin_pv_gwh"] + df["solar_park_gwh"] + df["wind_gwh"]
    df["net_balance_gwh"] = df["total_supply_gwh"] - df["demand_synthetic_gwh"]

    return df


def score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["energy_deficit_score"] = normalize(-df["net_balance_gwh"])
    df["grid_urgency_score"] = df["congestion_score"]
    df["composite_siting"] = (0.5 * df["energy_deficit_score"] + 0.5 * df["grid_urgency_score"]).round(4)
    return df.sort_values("composite_siting", ascending=False).reset_index(drop=True)


def main():
    print(">>> Loading raw Liander/Stedin small-connection data and reference tables...")
    df = build_pc4_table()
    print(f">>> {len(df)} PC4 zones assembled.")

    scored = score(df)

    out_path = PROCESSED / "hydrogen_siting_reproduced.csv"
    scored.to_csv(out_path, index=False)
    print(f">>> Saved: {out_path}")

    print("\nTOP 10 (reproduced from raw data):")
    cols = ["PC4", "municipality", "business_park", "demand_synthetic_gwh", "net_balance_gwh",
            "congestion_status", "composite_siting"]
    print(scored[cols].head(10).to_string(index=False))

    # Cross-check against the canonical, submitted-report-matching dataset.
    canonical = pd.read_csv(PROCESSED / "hydrogen_siting_phase3_v2.csv", dtype={"PC4": str})
    canonical_top10 = canonical.sort_values("composite_siting", ascending=False)["PC4"].head(10).tolist()
    reproduced_top10 = scored["PC4"].head(10).tolist()
    overlap = len(set(canonical_top10) & set(reproduced_top10))
    print(f"\n>>> Top-10 overlap with canonical (submitted-report) ranking: {overlap}/10 PC4 zones")
    print(f">>> Canonical  #1: {canonical.sort_values('composite_siting', ascending=False).iloc[0]['PC4']}")
    print(f">>> Reproduced #1: {scored.iloc[0]['PC4']}")


if __name__ == "__main__":
    main()
