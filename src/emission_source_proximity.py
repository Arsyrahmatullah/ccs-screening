"""
emission_source_proximity.py
===============================
Calculates the distance from each grid point/basin centroid to the nearest 
CO2 emission source (power plants, cement plants, refineries, etc., from 
Global Energy Monitor trackers) — analogous to the "proximity relationships 
between emission sources and sequestration opportunities" analysis in 
Nooraiepour et al. (2025), Fig. 7.

Used in the context of Tier 1 (national screening): which basins are 
geologically prospective AND close to large emitter clusters, as this 
determines the economic feasibility of CO2 transport (pipeline vs. ship).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Great-circle distance (km) between two lat/lon points (degrees), vectorized."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def nearest_emitter_distance(
    basins: pd.DataFrame,
    emitters: pd.DataFrame,
    basin_lat_col: str = "lat",
    basin_lon_col: str = "lon",
    emitter_lat_col: str = "lat",
    emitter_lon_col: str = "lon",
    emitter_capacity_col: str | None = "capacity_mtpa_co2_est",
) -> pd.DataFrame:
    """
    For each row in `basins`, find the nearest emitter in `emitters` and 
    return the basin data plus columns: `nearest_emitter_name`, 
    `nearest_emitter_km`, and (if available) the estimated emission 
    capacity of that emitter.

    Brute-force implementation (O(n*m)) — sufficient for prototyping with 
    tens of basins x hundreds-to-thousands of emitters. For full national 
    scales (>10k emitters), replace with KDTree (scipy.spatial.cKDTree 
    on planar projection, or sklearn.neighbors.BallTree with metric='haversine').
    """
    result = basins.copy()
    result["nearest_emitter_name"] = None
    result["nearest_emitter_km"] = np.nan
    if emitter_capacity_col and emitter_capacity_col in emitters.columns:
        result["nearest_emitter_capacity"] = np.nan

    for idx, basin_row in basins.iterrows():
        dists = haversine_km(
            basin_row[basin_lat_col],
            basin_row[basin_lon_col],
            emitters[emitter_lat_col].to_numpy(),
            emitters[emitter_lon_col].to_numpy(),
        )
        if len(dists) == 0:
            continue
        nearest_i = int(np.argmin(dists))
        result.loc[idx, "nearest_emitter_km"] = dists[nearest_i]
        result.loc[idx, "nearest_emitter_name"] = emitters.iloc[nearest_i].get("name", "unknown")
        if emitter_capacity_col and emitter_capacity_col in emitters.columns:
            result.loc[idx, "nearest_emitter_capacity"] = emitters.iloc[nearest_i][emitter_capacity_col]

    return result


def emitters_within_radius(
    center_lat: float,
    center_lon: float,
    emitters: pd.DataFrame,
    radius_km: float,
    lat_col: str = "lat",
    lon_col: str = "lon",
) -> pd.DataFrame:
    """Finds all emitters within X km radius of a single point (e.g., basin centroid)."""
    dists = haversine_km(center_lat, center_lon, emitters[lat_col].to_numpy(), emitters[lon_col].to_numpy())
    out = emitters.copy()
    out["distance_km"] = dists
    return out[out["distance_km"] <= radius_km].sort_values("distance_km").reset_index(drop=True)
def basin_accessibility_scores(
    basins: pd.DataFrame,
    emitters: pd.DataFrame,
    radius_km: float,
    min_distance_floor_km: float = 5.0,
    basin_lat_col: str = "lat",
    basin_lon_col: str = "lon",
    emitter_lat_col: str = "lat",
    emitter_lon_col: str = "lon",
    capacity_col: str = "capacity_mtpa_co2_est",
) -> pd.DataFrame:
    """
    Computes a gravity-style accessibility score per basin: for every emitter
    within `radius_km` of the basin centroid, weight its capacity by inverse
    distance and sum. This is a well-established spatial accessibility concept
    (Hansen-style gravity model) and is a more realistic cost proxy than
    "distance to nearest single emitter" — it rewards basins surrounded by
    many emitters, not just basins near one large plant.

        accessibility_index = sum( capacity_i / max(distance_i, min_distance_floor_km) )

    `min_distance_floor_km` prevents division blow-up for emitters extremely
    close to (or co-located with) the basin centroid.

    Returns `basins` with three new columns:
      - n_emitters_within_radius
      - total_capacity_within_radius_mtpa
      - accessibility_index (unnormalized; normalize downstream for scoring)
    """
    results = []
    for _, basin_row in basins.iterrows():
        nearby = emitters_within_radius(
            basin_row[basin_lat_col], basin_row[basin_lon_col], emitters, radius_km,
            lat_col=emitter_lat_col, lon_col=emitter_lon_col,
        )
        if capacity_col in nearby.columns:
            capacity = nearby[capacity_col].fillna(0.0)
        else:
            capacity = pd.Series(1.0, index=nearby.index)  # fallback: count-only weighting

        distance_floored = nearby["distance_km"].clip(lower=min_distance_floor_km)
        accessibility_index = float((capacity / distance_floored).sum())

        results.append(dict(
            n_emitters_within_radius=len(nearby),
            total_capacity_within_radius_mtpa=float(capacity.sum()),
            accessibility_index=accessibility_index,
        ))

    return pd.concat([basins.reset_index(drop=True), pd.DataFrame(results)], axis=1)