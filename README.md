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
indonesia-ccs-screening/
├── config.yaml                 # ALL cut-off parameters & assumptions (single source of truth)
├── src/
│   ├── co2_thermophysics.py    # CO2 density & phase using CoolProp
│   ├── optimal_zone_screening.py  # cut-offs + DBSCAN clustering
│   ├── montecarlo_capacity.py  # probabilistic volumetric capacity (Goodman et al. 2011)
│   ├── emission_source_proximity.py  # distance basin <-> emission source
│   ├── fetch_open_data.py      # download original data / generate sample data
│   └── load_config.py
├── notebooks/
│   └── 00_tier1_national_screening.ipynb   # ✅ ready to run, see below
│   └── 01_tier2_sunda_asri_workflow.ipynb  # ✅ ready to run (Sunda-Asri Basin deep-dive)
├── scripts/
│   └── build_notebook_00.py    # generator for the Tier 1 notebook
├── data/
│   ├── raw/         # original global grids (GEBCO NetCDF, GlobSed NetCDF, IHFC text data)
│   ├── external/     # sample/placeholder data + reference tables
│   └── processed/    # sunda_asri_boundary.csv (QGIS) & sunda_asri_capacity_results.csv (Monte Carlo output)
├── docs/
│   ├── methodology.md      # methodology adaptation + limitations (MUST READ)
│   └── data_provenance.md  # data sources, licenses, download status
├── figures/
│   └── real/        # Production-grade 2D maps & stochastic capacity curves (.png)
└── app/               # (planned) interactive dashboard
```

---

## How to run

```bash
git clone <repo-url>
cd indonesia-ccs-screening

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the full screening & clustering pipelines
jupyter notebook notebooks/00_tier1_national_screening.ipynb
jupyter notebook notebooks/01_tier2_sunda_asri_workflow.ipynb
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

The deep-dive workflow inside `notebooks/01_tier2_sunda_asri_workflow.ipynb` performs high-speed matrix masking, thermodynamic gridding, and stochastic resource evaluations, generating the following figures saved to `figures/real/`:

1. `01_sunda_asri_basement_depth.png` — 2D structural framework mapping the absolute basement depth profile, bounded by an **approximate placeholder boundary** (pending official QGIS digitization from Badan Geologi map sheets).
2. `02_sunda_asri_pressure_temperature.png` — Multi-panel side-by-side maps showing hydrostatic pressure (MPa) and geothermal formation temperature (°C) gradients.
3. `03_sunda_asri_co2_density.png` — Dense spatial modeling of supercritical CO₂ density values across the active reservoir grid.
4. `04_sunda_asri_spatial_screening.png` — Traffic-light style screening categorization separating Optimal, Sub-Optimal, and Non-Viable target zones.
5. `05_sunda_asri_dbscan_clusters.png` — Spatially contiguous reservoir storage blocks isolated via density-based clustering (DBSCAN), ignoring pixel noise.
6. `06_sunda_asri_monte_carlo_capacity.png` — Probability distribution / frequency histograms representing stochastic volumetric capacity limits (P90, P50, P10 resource estimates).

Tabular simulation parameters and resource numbers are exported automatically to `data/processed/sunda_asri_capacity_results.csv` for downstream framework/dashboard integrations.

## Roadmap

- [x] Phase 0 — Scaffold repo, config parameters, core module validation
- [x] Phase 1 — Tier 1 national screening (sample data)
- [X] Phase 2 — Digitization of Sunda-Asri boundary & depth structure from official Badan Geologi QGIS maps *(currently using an approximate placeholder boundary, see Limitations)*
- [x] Phase 3 — Integration of GEBCO + GlobSed for depth & structural grids
- [X] Phase 4 — Integration of original Global Energy Monitor tracker for emitters
- [x] Phase 5 — Tier 2: full Sunda-Asri workflow (cut-off → DBSCAN → Monte Carlo)
- [ ] Phase 6 — Benchmarking vs Hedriana et al. (2017) & Iskandar et al. (2013)
- [ ] Phase 7 — Interactive dashboard + poster + short paper

## Limitations (read before citing)

This project does not yet have access to confidential proprietary well data (stratigraphic tops, core/wireline logs, drill-stem formation pressure tests). The Sunda-Asri basin boundary used for spatial masking is an **approximate polygon reconstructed from published literature**, not a digitization of official Badan Geologi map sheets. Reservoir thickness ($h$), net-to-gross (NTG), and effective porosity ($\phi$) are governed by global analog proxies calibrated for regional Eocene–Miocene syn-rift systems. Results are capped at SRL 1–2 compliance. Full details are in `docs/methodology.md` §4.

## Citation

If using/developing this repo, please also cite the two main reference papers:

- de Jonge-Anderson, I. et al. (2025). *International Journal of Greenhouse Gas Control*, 143, 104347.
- Nooraiepour, M. et al. (2025). *International Journal of Greenhouse Gas Control*, 148, 104524.

## License

Code: MIT (see `LICENSE`). Third-party data follow their respective publisher licenses — see `docs/data_provenance.md`.