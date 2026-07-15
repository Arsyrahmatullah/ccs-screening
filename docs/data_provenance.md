# Data Provenance

Log all data sources planned/used by this project, their status, and the license/attribution requirements for each. **Update this table every time a new data source is added** — this is part of the reproducibility discipline exemplified in both reference papers (they published their supporting datasets separately on Zenodo).
## Status legend
- ✅ **Used (sample/placeholder)** — present in the repo, but not actual data
- 📋 **Planned** — source identified, not yet downloaded
- 🔒 **Manual download required** — portal does not provide a public API

## Data source table

| Dataset | Purpose | Source | License/Requirements | Status |
|---|---|---|---|---|
| Indonesian Sedimentary Basin Map (128 basins) | Boundary & tectonic basin classification | Geological Agency of ESDM — [geology.esdm.go.id/geomigas](https://geology.esdm.go.id/geomigas) | Free, must cite source (Geological Survey Center) | 📋 |
| Bouguer anomaly map, seismotectonic, basin (1:5,000,000) | Trend surface for structure digitization | ESDM Geomap — [geologi.esdm.go.id/geomap](https://geology.esdm.go.id/geomap) | Free | 📋 |
| Oil and gas working area boundaries | Exploration license context vs CCS area | ESDM One Map — [geoportal.esdm.go.id](https://geoportal.esdm.go.id) | Free, web-GIS | 📋 |
| GlobSed — total sediment thickness (5 arc-min, global) | Initial proxy depth structure | Straume et al. (2019); archive [data.caltech.edu/records/k4070-ngc79](https://data.caltech.edu/records/k4070-ngc79) (NOAA retired 12 May 2025) | Free, mandatory citation (Straume et al., 2019, G-cubed) | 📋 |
| Global Heat Flow Database, 2024 release | Proxy geothermal gradient | IHFC / GFZ Potsdam data services | Free, mandatory citation | 📋 |
| GEBCO bathymetry | Sea depth for offshore areas | [gebco.net](https://www.gebco.net/data_and_products/gridded_bathymetry_data/) | Free | 📋 |
| Global Coal Plant Tracker | CO2 emission source (coal power plants) | Global Energy Monitor | Free, citation: "Global Coal Plant Tracker, Global Energy Monitor, [release]" | 📋 |
| Global Cement and Concrete Tracker | CO2 emission source (cement plants) | Global Energy Monitor | Free, mandatory citation | 📋 |
| Global Oil and Gas Plant Tracker | CO2 emission source (refineries/processing) | Global Energy Monitor | Free, mandatory citation | 📋 |
| `sample_basins_indonesia.csv` | Tier 1 demo notebook | Internal creation (`src/fetch_open_data.py --mode sample`) | N/A — **not actual geological data** | ✅ (placeholder) |
| `sample_emitters_indonesia.csv` | Tier 1 demo notebook | Internal creation, synthetic around publicly known industrial clusters | N/A — **not actual emission data** | ✅ (placeholder) |
| `sunda_asri_boundary_illustrative.csv` | Tier 2 fallback basin polygon | Internal creation, hand-drawn (`src/fetch_open_data.py --mode sample`) — **NOT digitized from an official map** | N/A — placeholder | ✅ (fallback, always available) |
| `sunda_asri_faults_illustrative.csv` | Tier 2 fallback fault traces | Internal creation, hand-drawn — **NOT digitized from seismic/structural maps** | N/A — placeholder | ✅ (fallback, always available) |
| `sunda_asri_boundary_digitized.csv` (`data/processed/`) | Tier 2 REAL basin polygon | To be created via QGIS georeferencing of [geology.esdm.go.id/geomigas](https://geology.esdm.go.id/geomigas) | Cite Badan Geologi per their terms | 📋 (planned — highest-priority next step) |
| `sunda_asri_faults_digitized.csv` (`data/processed/`) | Tier 2 REAL fault traces | To be created via QGIS georeferencing / seismic interpretation | Internal derived product | 📋 (planned) |
| `gebco_2026_*.nc`, `GlobSed-v3.nc` (`data/raw/`) | Tier 2 REAL depth surface | GEBCO + GlobSed (see rows above) | Free, mandatory citation | 📋 (Tier 2 notebook auto-detects and uses these the moment they're placed in `data/raw/`) |

> **How Tier 2 decides real vs. illustrative**: `notebooks/01_tier2_sunda_asri_workflow.ipynb`
> checks `data/processed/sunda_asri_boundary_digitized.csv` and the GEBCO/GlobSed
> paths in `config.yaml` first. If any are missing, it falls back to the
> illustrative files above and a synthetic depth surface — and prints exactly
> which source was used in Section 1 of the notebook. There is never a silent
> mix of real and fake data.

## Literature benchmark (not raw data, but comparison figures)

| Source | Figure | Scope | Note |
|---|---|---|---|
| Iskandar et al. (2013) | ~600 Mt | Indonesia (oil & gas fields) | cited in ASEAN CO2-EOR study |
| Hedriana et al. (2017) | ~1.2 Gt (oil & gas fields) + ~14.8 Gt (saline) | South Sumatra + Java | requires verification of access to original paper before citing in more detail |
| Presidential Regulation 14/2024 (government claim) | >400 Gt CO2-eq | Depleted oil & gas reservoirs, national | policy headline figure, not an independent technical study result |

## License note: code vs data

- **Code** in this repo: MIT License (see `LICENSE`).
- **Derived data** (results of digitized public maps, etc.): must include the original source according to the requirements of each data publisher (see table above). Do not re-upload third-party raw data that has a "no redistribution" clause — simply store the download script + instructions (`src/fetch_open_data.py --mode real`).
- **Two reference papers** (de Jonge-Anderson et al., 2025; Nooraiepour et al., 2025) are licensed under CC BY 4.0 (open access) — may be cited/paraphrased freely with attribution, but do not reproduce figures/text verbatim in large quantities.

