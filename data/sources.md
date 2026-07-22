# Data sources

This repo reproduces the **regional (PC4-level) siting stage ("MCA1")** of the
Foodvalley hydrogen-siting analysis in open-source Python. Two kinds of input are
used, kept in separate files below so it's clear what's raw vs. already-published.

## Raw, unprocessed inputs (real data engineering happens on these)

| File | Source | What it is | Rows |
|---|---|---|---|
| `raw/verbruikdata_kleine_aansluitingen_2026.csv` | Liander & Stedin open data portals (`Open Data \| Liander`, `Open Data \| Stedin`) | Small-connection (<3×80A) annual electricity **consumption** per 6-digit postcode pair, tab-separated, Dutch decimal-comma formatting | 267,797 |
| `raw/terugleverdata_kleine_aansluitingen_2026.csv` | Liander & Stedin open data portals | Small-connection annual electricity **feed-in** (rooftop solar exported to grid) per postcode pair. Note: each row is wrapped in stray quote characters and internally tab-separated — a real formatting quirk of the published file, handled explicitly in `src/pipeline.py` | 147,770 |

Both files are the official small-connection open datasets published by the two
grid operators covering Regio Foodvalley. They only cover connections up to
3×80A — large industrial ("grootverbruik") connections are excluded from these
files by Dutch privacy law, which is exactly the gap the industrial proxy model
(below) corrects for.

## Small reference tables (already-published/verified figures, not re-scraped)

These are intentionally *not* re-derived from scratch. Re-fetching them would mean
re-implementing an ArcGIS Online REST client or scraping a live web map for
figures that are already public and already independently verified in the
submitted report (see `Foodvalley_Analysis_Summary_Report.md`, Tables 1–4).
Reusing them here keeps this repo honest about scope: the raw-data engineering
effort goes into the two large Liander/Stedin files above.

| File | Derived from / equivalent to report source | Notes |
|---|---|---|
| `raw/pc4_municipality_lookup.csv` | CBS PC4 register / Esri Nederland PC4 (2026a) | PC4 → municipality assignment, matches report Tables 1, 2, 4 |
| `raw/renewable_supply_by_pc4.csv` | RVO SDE++ register (solar) + RIVM/Esri wind turbine register | Solar park & wind generation (GWh/yr) per PC4, matches report Table 3 |
| `raw/industrial_commercial_proxy_by_pc4.csv` | BAG floor areas × ECN-E–15-068 sector benchmarks (642/150/76 kWh/m²) + CBS commercial demand proxy | Corrects for the "invisible factory" problem — large industrial demand not present in the DSO open data. Harselaar: 34 GWh (DSO-only) → 267 GWh (corrected) |
| `raw/congestion_status_by_pc4.csv` | Netbeheer Nederland Capaciteitskaart (official public grid congestion map) | RED / AMBER / GREEN status per PC4, matches report Table 2 |

## Canonical output

`processed/hydrogen_siting_phase3_v2.csv` is the scored, ranked result exactly as
used in the submitted report (Table 4): 73 PC4 candidates, composite siting score
= 50% energy-deficit + 50% grid-congestion-urgency. `src/pipeline.py` recomputes
this from the raw/reference inputs above; see the README for how the two compare.

## Not reproduced in this repo (see README "Scope" section)

The local (PC6-level) siting stage ("MCA2" in the report) used five additional
GIS layers — grid infrastructure points, industry park polygons, fuel stations,
road/rail network, Natura 2000 exclusion zones — pulled live from ArcGIS Online
REST services inside ArcGIS Pro. Those layers were never saved as local files, so
that stage isn't reproduced here.
