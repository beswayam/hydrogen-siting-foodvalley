# Case study: Siting green-hydrogen hubs to relieve grid congestion

**Wageningen University Academic Consultancy Training, 2026 — Team 3.695 (7
students), commissioned by Dutch Boosting Group for Regio Foodvalley.
This document covers both the original team project and a personal follow-on
extension I built afterward (this repo).**

## Situation

Regio Foodvalley — eight Dutch municipalities aiming for 0.75 TWh of local
sustainable energy generation by 2030 — was hitting a wall: severe electricity
grid congestion was blocking new renewable-energy connections and slowing
housing and business growth, even though the region was still importing 66% of
the electricity it consumed. A prior internal study had identified hydrogen
storage as a promising tool for absorbing surplus renewable generation, but had
never pinpointed *where*. Our team of seven was commissioned to answer that
question directly: which specific locations should Regio Foodvalley prioritise
for a hydrogen conversion & storage hub?

## Complication

The obvious data source — public grid-operator (Liander/Stedin) electricity
records — has a built-in blind spot: for privacy reasons it only covers small
connections (<3×80A). Large industrial sites, exactly the kind of location a
hydrogen hub needs to be near, are invisible in that data. Relying on it
naively would have ranked the region's biggest industrial energy users as
low-priority. We also had eight weeks, no dedicated GIS budget beyond ArcGIS
Pro's educational license, and a requirement to deliver something a
non-technical commissioner could act on.

## Approach

We combined three things: **11 semi-structured stakeholder interviews** (grid
operators, municipalities, hydrogen producers, industry) to ground-truth the
data and weight criteria realistically; a **two-stage Multi-Criteria Analysis**
— a regional PC4-level scoring pass (energy deficit × grid congestion urgency)
narrowing 57 postcode zones to the 3 most promising municipalities, followed by
a local PC6-level GIS pass in ArcGIS Pro scoring proximity to renewable
generation, grid infrastructure, and industry; and an **industrial-demand
correction model** (building floor area × sector energy-intensity benchmarks)
to fix the public-data blind spot — which turned out to be the single most
consequential modelling decision in the project.

We validated aggressively rather than taking our own numbers on faith:
independently-calculated regional renewable supply matched an official
government progress report to within 0.4%; our bottom-up demand estimates
matched 180 physically-metered substations at R²=0.998; our solar-park
inventory matched an independent prior study's inventory exactly.

## Result

Two locations stood out: **Harselaar (Barneveld)** — adjacent to an existing
solar park, a high-voltage substation, and a planned smart-energy-hub expansion
— and **Kievitsmeent (Ede)**. The industrial-demand correction moved Harselaar's
estimated demand from 34 GWh/yr (visible in public data) to **267 GWh/yr** —
nearly 7x higher — which is what pushed it from a middling ranking to the clear
top recommendation. Both locations were presented to and discussed with
municipal planning officers; Harselaar was validated as genuinely under
consideration, while Ede's site had not yet been discussed with the
municipality at submission time.

## What I built afterward (this repo)

The submitted report explicitly flagged, in its own discussion, that it hadn't
quantified how sensitive the ranking was to the 50/50 weighting choice between
the two MCA1 criteria. I closed that gap and turned the static analysis into
something interactive:

- **Reproduced the regional siting pipeline in open-source Python**
  (`src/pipeline.py`), parsing the raw Liander/Stedin small-connection exports
  directly (267,797 + 147,770 rows, with real formatting quirks — tab-separated,
  Dutch decimal commas, a stray-quote encoding bug in one file) rather than
  starting from a pre-cleaned CSV. It reproduces the report's #1 finding and
  score exactly, and matches 9 of the top 10 ranked sites.
- **Quantified the ranking's robustness** (`src/sensitivity.py`): entropy and
  CRITIC objective weighting for comparison, and an exact algebraic **Weight
  Stability Interval** — the #1 recommendation (Harselaar) holds for any
  deficit-weight between 47% and 100%, but flips to Nijverkamp (Veenendaal,
  officially RED-congested) under a congestion-dominant weighting. That's a
  genuinely useful nuance a static report can't show: the recommendation is
  robust to *moderate* disagreement about priorities, but not to a
  fundamentally different view of what matters most.
- **Turned the static dashboard into an interactive one**
  (`dashboard/index.html`): a live weight slider that recomputes every chart,
  the map, and the ranked table in real time, with a stability badge showing
  whether the current weighting still agrees with the report's recommendation.

## Skills demonstrated

Multi-criteria decision analysis (SAW, AHP, entropy/CRITIC weighting, exact
weight-stability derivation) · GIS siting analysis (ArcGIS Pro; PC4/PC6 spatial
joins) · Python data engineering on real government open data with production
formatting issues · stakeholder interviewing and synthesis · independent
statistical validation (cross-source triangulation, R² substation validation) ·
front-end data visualisation (Chart.js, Leaflet, vanilla JS) · technical writing
for both expert and non-technical audiences.

## What I'd do differently / next steps

- **Rebuild the local (PC6-level) GIS stage in open Python.** The original used
  five ArcGIS-Online-hosted layers (grid infrastructure, industry parks, fuel
  stations, roads, Natura 2000) that were never saved locally — a full
  reproduction needs re-fetching those from their public REST endpoints (listed
  in the report's bibliography) and replacing straight-line distance with real
  road-network distance (e.g. via OSMnx), which the report itself flags as a
  simplification.
- **Add a cost layer.** The current score is purely technical/spatial. A rough
  levelized-cost-of-hydrogen (LCOH) estimate per candidate site would move this
  from "where is it technically sensible" to "where is it fundable" — the
  report explicitly scopes this out, and it's the most obvious next increment
  of value.
- **Automate the pipeline against live data.** The DSO open-data portals and
  the Netbeheer Nederland congestion map update periodically; a scheduled job
  that re-pulls and rescoring would keep the dashboard current rather than a
  one-time snapshot.

---

*Original report: "Relieving grid congestion with hydrogen" — ACT Team 3.695,
Wageningen University, 2026. Co-authors: Swayam Belokar, Ilse Borsje, Jaro van
Hulst, Wytze Renema, Adebayo Salami, Lianne Schotman, Matina Vlachou. This
document and the code in this repository were built independently afterward as
a personal technical extension of that group work.*
