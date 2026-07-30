"""FastAPI server for the interactive CCS screening application."""

from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.emission_source_proximity import basin_accessibility_scores, nearest_emitter_distance
from src.montecarlo_capacity import NormalParam, monte_carlo_capacity, summarize_capacity
from src.co2_thermophysics import co2_density_kgm3, pressure_from_depth, temperature_from_depth
from src.optimal_zone_screening import ScreeningCutoffs, classify_zones, cluster_optimal_zones, summarize_zones


app = FastAPI(title="CCS-Screening: Indonesia", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")
app.mount("/figures", StaticFiles(directory=ROOT / "figures"), name="figures")


def load_config() -> dict:
    with (ROOT / "config.yaml").open(encoding="utf-8") as file:
        return yaml.safe_load(file)


CONFIG = load_config()


def read_csv(file: UploadFile) -> pd.DataFrame:
    """Parse a UTF-8 CSV upload and surface a useful client error."""
    try:
        return pd.read_csv(io.BytesIO(file.file.read()))
    except (UnicodeDecodeError, pd.errors.ParserError) as error:
        raise HTTPException(status_code=422, detail=f"Could not read {file.filename} as a CSV file: {error}") from error


def require_columns(frame: pd.DataFrame, columns: set[str], label: str) -> None:
    missing = columns - set(frame.columns)
    if missing:
        raise HTTPException(status_code=422, detail=f"{label} is missing required columns: {', '.join(sorted(missing))}.")


def records(frame: pd.DataFrame) -> list[dict]:
    """Return JSON-safe dataframe records."""
    clean = frame.replace([np.inf, -np.inf], np.nan).where(pd.notnull(frame), None)
    return clean.to_dict(orient="records")


def normalize(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").fillna(0.0)
    maximum = values.max()
    return pd.Series(0.0, index=values.index) if maximum <= 0 else values / maximum * 100


def finite_std(series: pd.Series, fallback: float) -> float:
    """Return a usable standard deviation for small or uniform clusters."""
    value = float(pd.to_numeric(series, errors="coerce").std())
    return value if np.isfinite(value) and value > 0 else fallback


def derive_grid_properties(grid: pd.DataFrame, fault_traces: UploadFile | None) -> tuple[pd.DataFrame, list[dict]]:
    """Fill optional Tier 2 screening fields from depth and fault data when possible."""
    result = grid.copy()
    sources: list[dict] = [{"layer": "Reservoir grid", "status": "used", "detail": "Spatial screening cells"}]
    reservoir = CONFIG["tier2_reservoir_proxy"]
    thermo = CONFIG["thermodynamics"]
    if "porosity_percent" not in result.columns:
        if "depth_m" not in result.columns:
            raise HTTPException(status_code=422, detail="Provide porosity_percent directly or include depth_m to derive it from the project proxy.")
        result["porosity_percent"] = reservoir["porosity_surface_fraction"] * np.exp(
            -reservoir["porosity_depth_decay_per_km"] * pd.to_numeric(result["depth_m"], errors="coerce") / 1000
        ) * 100
        sources.append({"layer": "Porosity", "status": "derived", "detail": "Depth-decay proxy from config.yaml"})
    if "co2_density_kgm3" not in result.columns:
        if "depth_m" not in result.columns:
            raise HTTPException(status_code=422, detail="Provide co2_density_kgm3 directly or include depth_m to compute CO2 properties.")
        depth = pd.to_numeric(result["depth_m"], errors="coerce").to_numpy()
        temperature = result["temperature_c"].to_numpy() if "temperature_c" in result.columns else temperature_from_depth(
            depth, thermo["geothermal_gradient_C_per_km_default"], thermo["seabed_temperature_C"]
        )
        pressure = result["pressure_mpa"].to_numpy() if "pressure_mpa" in result.columns else pressure_from_depth(
            depth, False, thermo["hydrostatic_gradient_MPa_per_km"], thermo["overpressure_gradient_MPa_per_km"]
        )
        try:
            result["co2_density_kgm3"] = co2_density_kgm3(temperature, pressure)
        except ImportError as error:
            raise HTTPException(status_code=422, detail="CoolProp is needed to derive CO2 density. Provide co2_density_kgm3 directly or install all project requirements.") from error
        sources.append({"layer": "CO2 density", "status": "derived", "detail": "CoolProp equation of state from depth, temperature, and pressure"})
    if "fault_distance_km" not in result.columns:
        if fault_traces is None or not {"lon", "lat"}.issubset(result.columns):
            raise HTTPException(status_code=422, detail="Provide fault_distance_km directly, or upload fault traces and include lon and lat in the reservoir grid.")
        faults = read_csv(fault_traces)
        require_columns(faults, {"fault_id", "lon", "lat"}, "Fault-trace CSV")
        from src.optimal_zone_screening import distance_to_nearest_fault_km
        result["fault_distance_km"] = distance_to_nearest_fault_km(result["lon"].to_numpy(), result["lat"].to_numpy(), faults)
        sources.append({"layer": "Fault distance", "status": "derived", "detail": "Calculated from uploaded fault traces"})
    return result, sources


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(ROOT / "app" / "templates" / "index.html")


@app.post("/api/tier1")
def run_tier1(
    basins: UploadFile = File(...),
    emitters: UploadFile = File(...),
    radius_km: float = Form(200),
    capacity_weight: float = Form(0.4),
) -> dict:
    """Rank user-supplied basin candidates against nearby CO2 emitters."""
    basin_frame = read_csv(basins)
    emitter_frame = read_csv(emitters)
    require_columns(basin_frame, {"basin", "lat", "lon"}, "Basin CSV")
    require_columns(emitter_frame, {"name", "lat", "lon"}, "Emitter CSV")
    if not 0 <= capacity_weight <= 1 or radius_km <= 0:
        raise HTTPException(status_code=422, detail="The radius must be positive and capacity weight must be between 0 and 1.")
    try:
        scored = basin_accessibility_scores(basin_frame, emitter_frame, radius_km)
        scored = nearest_emitter_distance(scored, emitter_frame)
        
        # Scientific Filtering Gate (Methodology §3)
        if "basin_type" in scored.columns:
            scored["tectonic_score"] = scored["basin_type"].apply(lambda x: 3 if any(k in str(x).lower() for k in ["back arc", "back-arc", "passive", "margin"]) else 1)
        else:
            scored["tectonic_score"] = 2  # default medium
            
        if "status" in scored.columns:
            scored["srl"] = scored["status"].apply(lambda x: 2 if any(k in str(x).lower() for k in ["producing", "discovery", "prospect"]) else 1)
        else:
            scored["srl"] = 1
            
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=f"Tier 1 screening could not process the uploaded data: {error}") from error
    scored["accessibility_score"] = normalize(scored["accessibility_index"])
    if "storage_capacity_gt" in scored.columns:
        scored["storage_score"] = normalize(scored["storage_capacity_gt"])
        # Incorporate tectonic suitability into final score
        base_score = (1 - capacity_weight) * scored["accessibility_score"] + capacity_weight * scored["storage_score"]
        scored["screening_score"] = base_score * (scored["tectonic_score"] / 3.0)
    else:
        scored["storage_score"] = np.nan
        scored["screening_score"] = scored["accessibility_score"] * (scored["tectonic_score"] / 3.0)
    scored = scored.sort_values("screening_score", ascending=False).reset_index(drop=True)
    leader = scored.iloc[0]
    return {
        "summary": {
            "basin_count": int(len(scored)),
            "leading_basin": str(leader["basin"]),
            "leading_score": round(float(leader["screening_score"]), 1),
            "nearest_emitter_km": round(float(leader["nearest_emitter_km"]), 1),
        },
        "results": records(scored),
        "caveat": "Tier 1 is a regional screening result. It does not establish storage reserves or project viability.",
    }


@app.post("/api/tier2")
def run_tier2(
    grid: UploadFile = File(...),
    fault_traces: UploadFile | None = File(None),
    basin_boundary: UploadFile | None = File(None),
    depth_surface: UploadFile | None = File(None),
    sediment_thickness: UploadFile | None = File(None),
    heat_flow: UploadFile | None = File(None),
    optimal_porosity: float = Form(10),
    optimal_density: float = Form(300),
    optimal_fault_buffer: float = Form(2),
    cell_area_km2: float = Form(1),
    minimum_cluster_area_km2: float = Form(100),
    dbscan_eps: float = Form(2),
    dbscan_min_samples: int = Form(5),
) -> dict:
    """Classify and cluster a reservoir grid, then quantify retained zones."""
    frame = read_csv(grid)
    require_columns(frame, {"x_km", "y_km"}, "Reservoir-grid CSV")
    if min(optimal_porosity, optimal_density, optimal_fault_buffer, cell_area_km2, minimum_cluster_area_km2, dbscan_eps) < 0 or dbscan_min_samples < 1:
        raise HTTPException(status_code=422, detail="Screening settings must be non-negative, with at least one DBSCAN sample.")
    sub = CONFIG["screening_cutoffs"]["sub_optimal"]
    frame, data_sources = derive_grid_properties(frame, fault_traces)
    if basin_boundary is not None:
        data_sources.append({"layer": "Basin boundary", "status": "attached", "detail": basin_boundary.filename or "Boundary file"})
    if depth_surface is not None:
        data_sources.append({"layer": "Depth surface", "status": "attached", "detail": f"{depth_surface.filename} (raw reference layer)"})
    if sediment_thickness is not None:
        data_sources.append({"layer": "Sediment thickness", "status": "attached", "detail": f"{sediment_thickness.filename} (raw reference layer)"})
    if heat_flow is not None:
        data_sources.append({"layer": "Heat-flow data", "status": "attached", "detail": f"{heat_flow.filename} (raw reference layer)"})
    optimal = ScreeningCutoffs(optimal_porosity, optimal_density, optimal_fault_buffer, minimum_cluster_area_km2)
    suboptimal = ScreeningCutoffs(sub["porosity_min_percent"], sub["co2_density_min_kgm3"], sub["fault_buffer_km"], minimum_cluster_area_km2)
    try:
        screened = frame.copy()
        screened["zone_class"] = classify_zones(screened, optimal, suboptimal)
        screened = cluster_optimal_zones(screened, "zone_class", "x_km", "y_km", dbscan_eps, dbscan_min_samples, cell_area_km2, minimum_cluster_area_km2)
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=f"Tier 2 screening could not process the uploaded grid: {error}") from error
    cluster_summary = summarize_zones(screened)
    reservoir = CONFIG["tier2_reservoir_proxy"]
    capacity_config = CONFIG["capacity_equation"]
    capacities: list[dict] = []
    for _, row in cluster_summary.iterrows():
        cluster = screened[screened["cluster_id"] == row["cluster_id"]]
        distribution = monte_carlo_capacity(
            area_km2=float(row["cluster_area_km2"]),
            thickness_m=NormalParam(reservoir["thickness_m_mean"], reservoir["thickness_m_std"], 0),
            ntg_fraction=NormalParam(reservoir["ntg_mean"], reservoir["ntg_std"], 0, 1),
            porosity_fraction=NormalParam(float(cluster["porosity_percent"].mean()) / 100, max(finite_std(cluster["porosity_percent"], 1.0) / 100, 0.01), 0, 1),
            swirr_fraction=NormalParam(capacity_config["swirr_mean"], capacity_config["swirr_std"], 0, 1),
            efficiency_fraction=NormalParam(capacity_config["efficiency_factor_percent_mean"] / 100, capacity_config["efficiency_factor_percent_std"] / 100, 0, 1),
            co2_density_kgm3=NormalParam(float(cluster["co2_density_kgm3"].mean()), max(finite_std(cluster["co2_density_kgm3"], 1.0), 1), 0),
            n_iterations=capacity_config["monte_carlo_iterations"],
        )
        capacities.append({"cluster_id": int(row["cluster_id"]), "area_km2": float(row["cluster_area_km2"]), **summarize_capacity(distribution)})
    capacity_frame = pd.DataFrame(capacities)
    zone_counts = screened["zone_class"].value_counts()
    return {
        "summary": {
            "optimal_cells": int(zone_counts.get("optimal", 0)),
            "connected_clusters": int(len(capacity_frame)),
            "connected_area_km2": round(float(capacity_frame["area_km2"].sum()), 2) if not capacity_frame.empty else 0,
        },
        "grid": records(screened),
        "capacities": records(capacity_frame),
        "data_sources": data_sources,
        "caveat": "Capacity uses the Goodman volumetric equation and project proxy parameters. Replace proxies with validated local data before site-level interpretation.",
    }
