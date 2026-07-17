// ... existing code ...
 │   ├── fetch_open_data.py      # download instructions for real data / generate all sample+illustrative data
 │   ├── ingest_raw_data.py      # converts raw GEM coal/cement/oil&gas trackers -> indonesia_emitters_real.csv
 │   └── load_config.py
 ├── notebooks/
// ... existing code ...
 - [x] Phase 1 — Tier 1 national screening (Complete, now updated with GEBCO bathymetry, tectonic priority matrices, multi-criteria cost-effective ranking, publication-ready Stylers, and 300 DPI charts)
 - [x] Phase 2 — Sunda-Asri boundary & depth structure: **real digitized boundary/fault traces in `data/processed/`**, real GEBCO+GlobSed depth grid in `data/raw/`; illustrative fallback still available for anyone cloning without those files
 - [~] Phase 3 — GEBCO + GlobSed integration: **wired and tested**, notebook uses real grids automatically when present in `data/raw/`, otherwise falls back to a clearly-labelled synthetic depth surface
 - [~] Phase 4 — Global Energy Monitor tracker ingestion: `src/ingest_raw_data.py` implemented in this repo (converts raw Coal/Cement/Oil&Gas GEM trackers into `data/raw/indonesia_emitters_real.csv`, auto-detected by the Tier 1 notebook). Still `[~]` because it requires the trackers to be downloaded manually first (GEM access form) — run `python3 src/fetch_open_data.py --mode real` for instructions, then `python3 src/ingest_raw_data.py`.
 - [x] Phase 5 — Tier 2: full Sunda-Asri workflow (porosity + CO2 density + fault-distance cut-off → DBSCAN with area filter → Monte Carlo), using real `co2_thermophysics.py` (CoolProp) throughout
// ... existing code ...
