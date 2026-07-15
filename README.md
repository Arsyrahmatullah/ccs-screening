# CCS Screening

**Adaptation of regional CO2 storage screening methodologies for priority CCS basins in Indonesia — fully open-source & reproducible.**

> Project status: 🚧 **Prototype (Tier 1 functional, Tier 2 functional)**.
> Most numerical data currently used are **illustrative placeholders** —
> read [`docs/methodology.md`](docs/methodology.md) before citing any figures
> from this repo. See [`docs/data_provenance.md`](docs/data_provenance.md)
> for a full list of planned original data sources.

---

## Why this project exists

Indonesia has recently established its CCS legal framework (Presidential Regulation 14/2024, ESDM Ministerial Regulations 2/2023 & 16/2024) and officially designated the **Sunda-Asri Basin** and **Bintuni Basin** as priority locations for strategic CCS hubs. However, there is no comprehensive and reproducible public screening study for Indonesian basins — a task already completed for the Malay Basin in Malaysia.

This project adapts two frameworks from recent literature:

| Reference | Adapted content |
|---|---|
| de Jonge-Anderson et al. (2025), *Regional screening of saline aquifers in the Malay Basin for CO2 storage*, IJGGC 143 | Technical workflow: grid depth/temperature/pressure → CO2 thermophysical properties (CoolProp) → subsurface cut-offs → clustering (DBSCAN) → volumetric Monte Carlo capacity (Goodman et al., 2011) |
| Nooraiepour et al. (2025), *Geological CO2 storage assessment in emerging CCS regions: ... Poland*, IJGGC 148 | Strategic framework for emerging CCS regions: **resource-reserve pyramid** & **Storage Readiness Level (SRL)**, as well as an open approach to data limitations |

Indonesia is currently in the same "emerging CCS region" position as Poland in the second paper — many potential basins, significant industry interest, but no public well/pressure data available. Therefore, the project strategy is: **use the Poland framework to set realistic ambition levels (SRL 1–2), and use the Malay Basin techniques for parts where data allows.**

---

## Project structure: two tiers

```
Tier 1  National Screening         Tier 2  Sunda-Asri Deep-Dive
────────────────────────────       ──────────────────────────────
Multi-basin (5-8 basins)           Focus on 1 priority basin
Basin-level, public data           Digitized spatial grids
Target SRL 1                       Target SRL 1-2
Style: Table 2 Poland paper        Style: Fig. 5-13 Malay Basin paper
✅ Notebook ready to run           ✅ Notebook ready to run  
```

## Repository structure

```
ccs-screening/
├── config.yaml                 # ALL cut-off parameters & assumptions (single source of truth)
├── src/
│   ├── co2_thermophysics.py    # CO2 density & phase using CoolProp (used in BOTH tiers)
│   ├── optimal_zone_screening.py  # cut-offs + DBSCAN clustering + fault-distance helper
│   ├── montecarlo_capacity.py  # probabilistic volumetric capacity (Goodman et al. 2011)
│   ├── emission_source_proximity.py  # distance basin <-> emission source
│   ├── fetch_open_data.py      # download instructions for real data / generate all sample+illustrative data
│   └── load_config.py
├── notebooks/
│   ├── 00_tier1_national_screening.ipynb   # ✅ ready to run, always prints active data source
│   └── 01_tier2_sunda_asri_workflow.ipynb  # ✅ ready to run, always prints active data source
├── scripts/
│   ├── build_notebook_00.py    # generator for the Tier 1 notebook
│   └── build_notebook_01.py    # generator for the Tier 2 notebook
├── data/
│   ├── raw/         # (gitignored) real GEBCO/GlobSed NetCDF, IHFC heat-flow, GEM trackers go here
│   ├── external/     # sample/illustrative data shipped WITH the repo (always available, no download needed)
│   └── processed/    # (gitignored) derived outputs: QGIS-digitized boundary/faults if you have them, Monte Carlo results CSV
├── docs/
│   ├── methodology.md      # methodology adaptation + limitations (MUST READ)
│   └── data_provenance.md  # data sources, licenses, download status, real-vs-illustrative file map
├── figures/           # all generated PNGs/HTML (Tier 1: tier1_*, Tier 2: tier2_*)
└── app/               # (planned) interactive dashboard
```

---

## How to run

```bash
git clone https://github.com/Arsyrahmatullah/ccs-screening.git
cd ccs-screening

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the full screening & clustering pipelines
# (both work immediately with zero setup — illustrative sample/synthetic
# data ships with the repo in data/external/ as a fallback)
jupyter notebook notebooks/00_tier1_national_screening.ipynb
jupyter notebook notebooks/01_tier2_sunda_asri_workflow.ipynb

# Optional: use REAL data instead of the fallback — see docs/data_provenance.md
# for download links, then place files in data/raw/ or data/processed/.
# Each notebook auto-detects and prints which source it actually used.
```
Quick sanity check for each core module (all modules have `if __name__ == "__main__"` demos):

```bash
python3 src/co2_thermophysics.py     # CO2 density/phase vs depth
python3 src/montecarlo_capacity.py   # validation vs Group I, Malay Basin paper
```

---

## What is in the Tier 1 notebook

`notebooks/00_tier1_national_screening.ipynb` (ready to execute end-to-end
offline, using sample data):

1. Classification of 8 Indonesian basins (Sunda-Asri, South Sumatra, North
   Sumatra, Northwest Java, East Java, Kutai, Bintuni, Natuna/Malay Basin
   Indonesian side) into the **SRL** framework.
2. **Proximity** analysis of basin ↔ CO2 emission source clusters (great-circle
   distance), analogous to Fig. 7 in the Poland paper.
3. Demonstration of the **resource-reserve pyramid** using Monte Carlo
   simulation (1000 iterations, P10/P50/P90 distributions) using illustrative geometry.
4. Interactive map (`figures/tier1_indonesia_basins_map.html`) & comparison
   bar chart (`figures/tier1_illustrative_capacity_comparison.png`).

All numbers in this notebook are explicitly marked as **PLACEHOLDERS** —
see the limitations section below.

---
## Technical Outputs Generated (Tier 2 Workflow)

The deep-dive workflow inside `notebooks/01_tier2_sunda_asri_workflow.ipynb` runs the full [MB]-style pipeline (depth grid → CoolProp thermophysics → triple cut-off → DBSCAN → Monte Carlo) and saves the following figures to `figures/`:

1. `tier2_01_depth_surface.png` — depth-to-reservoir-top map (real GEBCO+GlobSed if present in `data/raw/`, otherwise a clearly-labelled synthetic bowl-shaped proxy), with basin boundary and fault traces overlaid.
2. `tier2_02_thermophysics.png` — temperature, pressure, and **CoolProp-derived** CO2 density (equation-of-state based, not an empirical approximation).
3. `tier2_03_porosity.png` — modelled porosity from the depth-decay trend in `config.yaml`.
4. `tier2_04_fault_distance.png` — distance-to-nearest-fault grid, computed with Shapely from the fault trace file.
5. `tier2_05_screening_classification.png` — Optimal / Sub-optimal / Non-viable zones from **all three** [MB] cut-off criteria (porosity + CO2 density + fault distance).
6. `tier2_06_clusters.png` — DBSCAN-connected optimal zones, filtered by `min_connected_area_km2` from `config.yaml`.
7. `tier2_07_capacity_by_cluster.png` — Monte Carlo P10/P50/P90 capacity per connected cluster, computed via `montecarlo_capacity.py`.

Tabular results are exported to `data/processed/sunda_asri_capacity_results.csv`.

> Every figure title/print statement in the notebook explicitly states whether it used real or illustrative/synthetic input data — check the Section 1 output before citing any number.

## Roadmap

- [x] Phase 0 — Scaffold repo, config parameters, core module validation
- [x] Phase 1 — Tier 1 national screening (runs on real emitter data when
      `data/raw/` is populated, illustrative sample data otherwise — always
      prints which source is active)
- [~] Phase 2 — Sunda-Asri boundary & depth structure: **illustrative
      fallback shipped and working**; official QGIS digitization from Badan
      Geologi map sheets still pending (see Limitations)
- [~] Phase 3 — GEBCO + GlobSed integration: **wired and tested**, notebook
      uses real grids automatically when present in `data/raw/`, otherwise
      falls back to a clearly-labelled synthetic depth surface
- [~] Phase 4 — Global Energy Monitor tracker ingestion: pipeline exists
      (`src/ingest_raw_data.py` in the `indonesia-ccs-screening` predecessor
      repo — being ported here), not yet wired into this repo's Tier 1 notebook
- [x] Phase 5 — Tier 2: full Sunda-Asri workflow (porosity + CO2 density +
      fault-distance cut-off → DBSCAN with area filter → Monte Carlo),
      using real `co2_thermophysics.py` (CoolProp) throughout
- [ ] Phase 6 — Benchmarking vs Hedriana et al. (2017) & Iskandar et al. (2013)
- [ ] Phase 7 — Interactive dashboard + poster + short paper

`[~]` = functional with a working fallback, but not yet using fully real,
digitized/downloaded data end-to-end. This distinction matters — see
`docs/data_provenance.md` for exactly which files are real vs. illustrative
in any given run (every notebook prints its active data source explicitly).

## Limitations (read before citing)

This project does not yet have access to confidential proprietary well data (stratigraphic tops, core/wireline logs, drill-stem formation pressure tests). Results are capped at SRL 1–2 compliance. Specifically, unless you have supplied your own real files in `data/raw/` and `data/processed/` (see `docs/data_provenance.md`):

- The Sunda-Asri basin boundary and fault traces are **hand-drawn illustrative placeholders**, not digitizations of official Badan Geologi map sheets.
- The depth surface is a **synthetic bowl-shaped proxy** (deepens toward the basin centroid within a plausible depth range), not a real depth-structure map — used only when GEBCO/GlobSed NetCDF grids are absent from `data/raw/`.
- Reservoir thickness ($h$), net-to-gross (NTG), and the porosity-depth decay rate are generic proxies (`config.yaml` §`tier2_reservoir_proxy`), not calibrated to local well/core data.
- No mapped overpressure zones for Sunda-Asri yet — hydrostatic pressure gradient assumed everywhere.

What **is** real physics regardless of data availability: CO2 density and phase are computed from the actual CoolProp equation of state (`src/co2_thermophysics.py`), not an empirical approximation, and the Monte Carlo capacity calculation follows Goodman et al. (2011) exactly as implemented and unit-tested in `src/montecarlo_capacity.py`. Every notebook explicitly prints which inputs were real vs. illustrative for a given run — always check that output before citing a number. Full details are in `docs/methodology.md` §4.

## Citation

If using/developing this repo, please also cite the two main reference papers:

- de Jonge-Anderson, I. et al. (2025). *International Journal of Greenhouse Gas Control*, 143, 104347.
- Nooraiepour, M. et al. (2025). *International Journal of Greenhouse Gas Control*, 148, 104524.

## License

Code: MIT (see `LICENSE`). Third-party data follow their respective publisher licenses — see `docs/data_provenance.md`.