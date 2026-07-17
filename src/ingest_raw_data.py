"""
ingest_raw_data.py
====================
Converts RAW Global Energy Monitor (GEM) tracker exports — Global Coal Plant
Tracker, Global Cement and Concrete Tracker, Global Oil and Gas Plant Tracker
(each downloaded manually as .xlsx per docs/data_provenance.md, since GEM
requires filling out a free access form) — into the single standardized
emitter table consumed by src/emission_source_proximity.py.

This closes the "Phase 4 — Global Energy Monitor tracker ingestion" gap noted
in the README roadmap: a version of this pipeline existed in the predecessor
repo (indonesia-ccs-screening) but had not yet been ported here. This is a
fresh implementation against the current repo's schema (not a copy), since
the predecessor repo is not accessible from this environment.

Output schema (matches data/external/sample_emitters_indonesia.csv so both
real and sample paths are interchangeable — see config.yaml -> paths.real.emitters):
    name, cluster, sector, lat, lon, capacity_mtpa_co2_est, data_status

Usage:
    python3 src/ingest_raw_data.py
    # Reads whichever of the 3 tracker files (config.yaml -> paths.real.*)
    # are present in data/raw/, skips the rest with a warning, and writes
    # data/raw/indonesia_emitters_real.csv. Missing all three -> prints
    # download instructions and exits without writing (never crashes the
    # pipeline; notebooks/00 falls back to sample data automatically).

Each raw tracker's column names/units are documented at
https://globalenergymonitor.org/download-data-success/ and vary slightly by
release, so column matching below is done by candidate-name search rather
than a fixed index, and every conversion assumption lives in config.yaml's
`emission_factors` section (single source of truth, per project convention).
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from load_config import load_config

REPO_ROOT = Path(__file__).resolve().parent.parent

# GEM tracker -> (config path key, sector label, capacity-unit kind)
TRACKERS = {
    "gem_coal_tracker": ("coal_power", "mw"),
    "gem_cement_tracker": ("cement", "mt_cement_per_year"),
    "gem_oil_gas_tracker": ("oil_gas_processing", "mw"),
}

# Column-name candidates seen across GEM tracker releases (lowercased match).
NAME_CANDIDATES = ["plant name", "unit name", "project name", "name"]
COUNTRY_CANDIDATES = ["country/area", "country", "country_area"]
LAT_CANDIDATES = ["latitude", "lat"]
LON_CANDIDATES = ["longitude", "lon", "long"]
STATUS_CANDIDATES = ["status", "plant status", "unit status"]
CAPACITY_CANDIDATES = [
    "capacity (mw)", "capacity (mt cement/y)", "capacity (mtpa)",
    "capacity", "nameplate capacity (mw)",
]
REPORTED_CO2_CANDIDATES = [
    "annual co2 (million tonnes)", "annual co2 emissions (mt/y)",
    "co2 emissions (mtpa)", "annual_co2_mtpa",
]

# Statuses kept by default -- excludes retired/cancelled/mothballed/shelved,
# which are not active CO2 sources for a source-sink transport analysis.
DEFAULT_KEEP_STATUSES = [
    "operating", "construction", "announced", "permitted", "pre-permit",
]


def _find_column(columns: list[str], candidates: list[str]) -> str | None:
    lower_map = {c.lower().strip(): c for c in columns}
    for cand in candidates:
        if cand in lower_map:
            return lower_map[cand]
    return None


def _read_tracker(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path)
    return pd.read_csv(path)


def standardize_tracker(
    raw: pd.DataFrame,
    sector: str,
    capacity_unit: str,
    emission_factors: dict,
    keep_statuses: list[str],
) -> pd.DataFrame:
    """
    Maps one raw GEM tracker dataframe (arbitrary column names) onto the
    standardized emitter schema, filtered to Indonesia and active statuses,
    with capacity_mtpa_co2_est estimated from config.yaml emission_factors
    when the tracker doesn't already report actual CO2 emissions.
    """
    cols = list(raw.columns)
    name_col = _find_column(cols, NAME_CANDIDATES)
    country_col = _find_column(cols, COUNTRY_CANDIDATES)
    lat_col = _find_column(cols, LAT_CANDIDATES)
    lon_col = _find_column(cols, LON_CANDIDATES)
    status_col = _find_column(cols, STATUS_CANDIDATES)
    capacity_col = _find_column(cols, CAPACITY_CANDIDATES)
    reported_co2_col = _find_column(cols, REPORTED_CO2_CANDIDATES)

    missing = [n for n, c in [("name", name_col), ("lat", lat_col), ("lon", lon_col)] if c is None]
    if missing:
        raise ValueError(
            f"[{sector}] Could not find required column(s) {missing} in tracker "
            f"(columns present: {cols[:15]}...). GEM likely changed its export "
            f"format -- add the new header text to the *_CANDIDATES lists above."
        )

    df = raw.copy()

    if country_col is not None:
        df = df[df[country_col].astype(str).str.strip().str.lower() == "indonesia"]
    if status_col is not None:
        df = df[df[status_col].astype(str).str.strip().str.lower().isin(keep_statuses)]

    out = pd.DataFrame()
    out["name"] = df[name_col]
    out["cluster"] = sector  # coarse grouping; refine later with a real spatial clustering pass if needed
    out["sector"] = sector
    out["lat"] = pd.to_numeric(df[lat_col], errors="coerce")
    out["lon"] = pd.to_numeric(df[lon_col], errors="coerce")

    reported = (
        pd.to_numeric(df[reported_co2_col], errors="coerce")
        if reported_co2_col is not None
        else pd.Series(np.nan, index=df.index)
    )
    capacity_raw = (
        pd.to_numeric(df[capacity_col], errors="coerce")
        if capacity_col is not None
        else pd.Series(np.nan, index=df.index)
    )

    estimated = _estimate_mtpa_co2(capacity_raw, capacity_unit, sector, emission_factors)
    out["capacity_mtpa_co2_est"] = reported.combine_first(estimated)
    out["data_status"] = np.where(
        reported.notna(),
        "REAL - GEM tracker, reported CO2 figure",
        "REAL - GEM tracker, CO2 estimated from capacity (see config.yaml emission_factors)",
    )

    out = out.dropna(subset=["lat", "lon"])
    return out.reset_index(drop=True)


def _estimate_mtpa_co2(
    capacity_raw: pd.Series, capacity_unit: str, sector: str, emission_factors: dict
) -> pd.Series:
    factors = emission_factors[sector]
    if sector == "coal_power":
        # MW * capacity_factor * hours/year * tCO2/MWh, converted t -> Mt
        return (
            capacity_raw
            * factors["capacity_factor"]
            * 8760
            * factors["tco2_per_mwh"]
            / 1e6
        )
    if sector == "cement":
        # Mt cement/y * tCO2 per t cement -- dimensionally already Mt CO2/y
        return capacity_raw * factors["tco2_per_t_cement"]
    if sector == "oil_gas_processing":
        # MW * tCO2/MW/year, converted t -> Mt
        return capacity_raw * factors["tco2_per_mw_year"] / 1e6
    raise ValueError(f"Unknown sector for emission estimation: {sector}")


def ingest_all(cfg: dict) -> pd.DataFrame | None:
    """
    Reads every GEM tracker present in data/raw/ (per config.yaml paths.real),
    standardizes and concatenates them. Returns None (and prints instructions)
    if none of the three tracker files are present.
    """
    emission_factors = cfg["emission_factors"]
    frames = []
    any_found = False

    for path_key, (sector, capacity_unit) in TRACKERS.items():
        rel_path = cfg["paths"]["real"].get(path_key)
        if not rel_path:
            continue
        tracker_path = REPO_ROOT / rel_path
        if not tracker_path.exists():
            print(f"[skip] {sector}: not found at {tracker_path} (see docs/data_provenance.md to download)")
            continue

        any_found = True
        print(f"[read] {sector}: {tracker_path.name}")
        raw = _read_tracker(tracker_path)
        standardized = standardize_tracker(
            raw, sector, capacity_unit, emission_factors, DEFAULT_KEEP_STATUSES
        )
        print(f"       -> {len(standardized)} Indonesia facilities kept "
              f"(statuses: {', '.join(DEFAULT_KEEP_STATUSES)})")
        frames.append(standardized)

    if not any_found:
        print("=" * 78)
        print("No GEM tracker files found in data/raw/. Download them manually first:")
        print("  python3 src/fetch_open_data.py --mode real")
        print("(GEM requires a free access-request form -- see docs/data_provenance.md)")
        print("=" * 78)
        return None

    combined = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    return combined


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", default=None,
        help="Override output path (default: config.yaml -> paths.real.emitters)",
    )
    args = parser.parse_args()

    cfg = load_config(REPO_ROOT / "config.yaml")
    combined = ingest_all(cfg)
    if combined is None:
        return

    output_path = Path(args.output) if args.output else REPO_ROOT / cfg["paths"]["real"]["emitters"]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output_path, index=False)

    print(f"\n{len(combined)} total Indonesia emitters written to {output_path}")
    print("notebooks/00_tier1_national_screening.ipynb will now auto-detect this file "
          "and print 'REAL' as the active emitter data source.")


if __name__ == "__main__":
    main()