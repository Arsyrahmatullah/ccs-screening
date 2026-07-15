"""
optimal_zone_screening.py
==========================
Implements subsurface cut-offs (porosity, CO2 density, distance to faults) to
determine "optimal" / "sub-optimal" / "non-viable" zones, then clusters
connected optimal zones using DBSCAN and removes clusters smaller than a 
minimum area — replicating de Jonge-Anderson et al. (2025) §4.5.1 
"Defining optimal zones" and Fig. 5.

Designed to work on point data (point cloud grid: x, y, porosity,
co2_density, fault_distance) — rather than a full GIS raster — to remain 
independent of GDAL/geopandas and lightweight for prototyping.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN


@dataclass
class ScreeningCutoffs:
    """Bundles cut-off parameters. Default values are from config.yaml (see
    src/load_config.py) — do not hardcode here; load from config.yaml
    to keep sensitivity analysis consistent with a single source of truth."""

    porosity_min_percent: float
    co2_density_min_kgm3: float
    fault_buffer_km: float
    min_connected_area_km2: float


def classify_zones(
    grid: pd.DataFrame,
    optimal: ScreeningCutoffs,
    sub_optimal: ScreeningCutoffs,
    porosity_col: str = "porosity_percent",
    density_col: str = "co2_density_kgm3",
    fault_dist_col: str = "fault_distance_km",
) -> pd.Series:
    """
    Classify each grid row as "optimal", "sub_optimal", or "non_viable", 
    following the double cut-off logic in [MB] §4.5.1.

    Returns: pd.Series of categories matching the grid index.
    """
    is_optimal = (
        (grid[porosity_col] >= optimal.porosity_min_percent)
        & (grid[density_col] >= optimal.co2_density_min_kgm3)
        & (grid[fault_dist_col] >= optimal.fault_buffer_km)
    )
    is_sub_optimal = (
        (~is_optimal)
        & (grid[porosity_col] >= sub_optimal.porosity_min_percent)
        & (grid[density_col] >= sub_optimal.co2_density_min_kgm3)
        & (grid[fault_dist_col] >= sub_optimal.fault_buffer_km)
    )

    category = pd.Series("non_viable", index=grid.index, dtype=object)
    category[is_sub_optimal] = "sub_optimal"
    category[is_optimal] = "optimal"
    return category


def cluster_optimal_zones(
    grid: pd.DataFrame,
    category_col: str,
    x_col: str,
    y_col: str,
    eps: float,
    min_samples: int,
    cell_area_km2: float,
    min_connected_area_km2: float,
) -> pd.DataFrame:
    """
    Cluster grid points categorized as "optimal" using DBSCAN (replicating
    the role of DBSCAN in scikit-learn used in [MB] §4.5.1),
    then discard clusters with area < min_connected_area_km2.

    `cell_area_km2` = area represented by a single grid point (e.g., if 
    grid spacing is 1 km x 1 km, then cell_area_km2 = 1.0).

    Returns: original grid + new columns `cluster_id` (-1 for noise/discarded) 
    and `cluster_area_km2`.
    """
    result = grid.copy()
    result["cluster_id"] = -1
    result["cluster_area_km2"] = np.nan

    optimal_mask = result[category_col] == "optimal"
    if optimal_mask.sum() == 0:
        return result

    coords = result.loc[optimal_mask, [x_col, y_col]].to_numpy()
    labels = DBSCAN(eps=eps, min_samples=min_samples).fit_predict(coords)
    result.loc[optimal_mask, "cluster_id"] = labels

    areas = (
        result.loc[optimal_mask]
        .groupby("cluster_id")
        .size()
        .mul(cell_area_km2)
        .rename("cluster_area_km2")
    )
    result = result.drop(columns=["cluster_area_km2"]).merge(
        areas, how="left", left_on="cluster_id", right_index=True
    )

    # Discard clusters that are too small OR noise (-1) from "connected optimal" status
    too_small_or_noise = (result["cluster_id"] == -1) | (
        result["cluster_area_km2"] < min_connected_area_km2
    )
    result["is_connected_optimal_zone"] = optimal_mask & (~too_small_or_noise)

    return result


def summarize_zones(screened_grid: pd.DataFrame) -> pd.DataFrame:
    """Quick summary: number of valid clusters & their total area (analogous to Fig. 5b [MB])."""
    valid = screened_grid[screened_grid["is_connected_optimal_zone"]]
    if valid.empty:
        return pd.DataFrame(columns=["cluster_id", "cluster_area_km2"])
    summary = (
        valid[["cluster_id", "cluster_area_km2"]]
        .drop_duplicates()
        .sort_values("cluster_area_km2", ascending=False)
        .reset_index(drop=True)
    )
    return summary

def distance_to_nearest_fault_km(
    lon: np.ndarray,
    lat: np.ndarray,
    fault_lines_df: pd.DataFrame,
    fault_id_col: str = "fault_id",
    lon_col: str = "lon",
    lat_col: str = "lat",
) -> np.ndarray:
    """
    Distance (km) from each (lon, lat) grid point to the nearest fault trace,
    using Shapely LineStrings built from `fault_lines_df` (grouped by
    `fault_id_col`). Distances are computed in decimal-degree space and
    converted to km via a flat ~111 km/degree approximation — adequate at
    the scale of a single sedimentary basin (a few hundred km), analogous to
    the fault setback approach in [MB] §4.5.1, but NOT geodesically exact.

    Returns an array the same shape as `lon`/`lat`.
    """
    from shapely.geometry import LineString, Point

    faults = []
    for _, group in fault_lines_df.groupby(fault_id_col):
        coords = list(zip(group[lon_col], group[lat_col]))
        if len(coords) >= 2:
            faults.append(LineString(coords))

    if not faults:
        return np.full(np.asarray(lon).shape, np.inf)

    lon_flat = np.asarray(lon).ravel()
    lat_flat = np.asarray(lat).ravel()
    distances_deg = np.empty(lon_flat.shape, dtype=float)

    for i, (x, y) in enumerate(zip(lon_flat, lat_flat)):
        point = Point(x, y)
        distances_deg[i] = min(f.distance(point) for f in faults)

    distances_km = distances_deg * 111.0  # rough flat-earth approximation
    return distances_km.reshape(np.asarray(lon).shape)
