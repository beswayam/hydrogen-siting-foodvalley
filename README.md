# Hydrogen Hub Siting — Regio Foodvalley

Open-source Python reproduction, robustness analysis, and interactive dashboard
for a regional green-hydrogen siting study, extending a Wageningen University
Academic Consultancy Training (ACT) report I co-authored.

**[Read the case study](CASE_STUDY.md)** · **[Open the interactive dashboard](dashboard/index.html)**

## Problem

Regio Foodvalley (eight Dutch municipalities, part of Gelderland/Utrecht) faces
severe electricity grid congestion: renewable generation regularly exceeds what
the grid can carry, while some industrial areas can't get a new connection at
all. Green hydrogen — using surplus electricity to split water, then storing the
hydrogen for later use — is one way to absorb that surplus and relieve pressure
on the grid. The question this project answers: **which specific locations in
the region should be prioritised for a hydrogen conversion & storage hub?**

## Method

A two-criterion Multi-Criteria Analysis (MCA) at four-digit-postcode (PC4) level:

```
composite_siting_score = 0.5 * energy_deficit_score + 0.5 * grid_congestion_score
```

- **Energy deficit score** — min-max normalised gap between local renewable
  electricity supply (rooftop solar feed-in + solar parks + wind) and local
  demand, corrected for the "invisible factory" problem: Dutch privacy law
  excludes large industrial connections from public grid-operator data, so an
  industrial-proxy model (building floor area × sector energy-intensity
  benchmarks) is applied to the region's business parks.
- **Grid congestion score** — official Netbeheer Nederland Capaciteitskaart
  status (RED=1.0 / AMBER=0.5 / GREEN=0.2).

## Key finding

**PC4 3771 (Harselaar business park, Barneveld)** ranks #1, with composite score
**0.75** — driven by a corrected industrial demand of **267 GWh/yr** (vs. 34
GWh/yr visible in public open data alone, a 7x undercount from the privacy-driven
data gap). It's next to an existing solar park, a high-voltage substation, and a
planned smart-energy-hub expansion.

This repo adds a **quantified robustness check** the original report didn't
include: an exact **Weight Stability Interval** shows Harselaar remains #1 for
any energy-deficit weighting between **47% and 100%** — but a congestion-dominant
weighting (e.g. an objectively-derived CRITIC weighting, 28%/72%) flips the #1
recommendation to **PC4 3901 (Nijverkamp, Veenendaal)**, the only officially
RED-congested top candidate. See [`figures/sensitivity_weight_stability.png`](figures/sensitivity_weight_stability.png)
or explore it live in the [dashboard](dashboard/index.html).

## What's in this repo

| Path | What it is |
|---|---|
| [`dashboard/index.html`](dashboard/index.html) | Interactive dashboard — filters, KPIs, map, and a **live weight-sensitivity slider** that re-ranks every site in real time |
| [`src/pipeline.py`](src/pipeline.py) | MCA1 pipeline, reproduced from the raw Liander/Stedin open datasets |
| [`src/sensitivity.py`](src/sensitivity.py) | Entropy weighting, CRITIC weighting, and exact Weight Stability Interval analysis |
| [`notebooks/01_pipeline_walkthrough.ipynb`](notebooks/01_pipeline_walkthrough.ipynb) | Executed, narrated walkthrough of the full pipeline |
| [`data/`](data/sources.md) | Raw inputs + provenance for every dataset used |
| [`CASE_STUDY.md`](CASE_STUDY.md) | Portfolio write-up: role, approach, impact, what I'd do differently |

## How to run

```bash
pip install -r requirements.txt
python src/pipeline.py       # rebuilds the siting score from raw data
python src/sensitivity.py    # runs the robustness analysis, writes figures/sensitivity_weight_stability.png
```

Then open `dashboard/index.html` directly in a browser (no server needed), or
open `notebooks/01_pipeline_walkthrough.ipynb` in Jupyter.

## Reproducibility check

`src/pipeline.py` parses the real raw Liander/Stedin small-connection open data
(267,797 + 147,770 rows) rather than starting from a pre-cleaned file. Running it
reproduces the submitted report's #1 site and score **exactly** (PC4 3771,
score 0.7500) and matches **9 of the top 10** ranked sites; the small remaining
differences come from minor vintage differences in the rooftop-solar feed-in
export between when the original ArcGIS-based analysis was run and the raw file
available now. See [`data/sources.md`](data/sources.md) for exactly which inputs
are parsed from raw files vs. reused as small, already-published reference
tables, and why.

## Scope

This repo reproduces the **regional (PC4-level) siting stage** in open-source
Python. The original report's **local (PC6-level) siting stage** used five
additional GIS layers — grid infrastructure, industry parks, fuel stations, roads,
Natura 2000 exclusion zones — pulled live from ArcGIS Online inside ArcGIS Pro;
those layers were never saved as local files, so that stage is summarized in
[`CASE_STUDY.md`](CASE_STUDY.md) rather than rebuilt here. See "Next steps" in
the case study for what a full open-source rebuild of that stage would involve.

## Tech stack

Python (pandas, numpy, matplotlib), Jupyter, vanilla JS + Chart.js + Leaflet for
the dashboard (no build step, opens as a static file). Original analysis used
ArcGIS Pro for the GIS stage this repo doesn't reproduce.

## Source report

*"Relieving grid congestion with hydrogen: Identifying locations for production
and storage of green hydrogen in Regio Foodvalley"* — ACT Team 3.695, Wageningen
University, 2026. Commissioned by Dutch Boosting Group for Regio Foodvalley.
Co-authors: Swayam Belokar, Ilse Borsje, Jaro van Hulst, Wytze Renema, Adebayo
Salami, Lianne Schotman, Matina Vlachou. See `LICENSE` for scope of reuse.
