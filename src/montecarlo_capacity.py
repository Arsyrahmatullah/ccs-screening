"""
montecarlo_capacity.py
========================
Probabilistic CO2 storage capacity estimation (Monte Carlo) using the equation
from Goodman et al. (2011), which is used in both de Jonge-Anderson et al.
(2025) — Malay Basin, Eq. (2) — and Nooraiepour et al. (2025) — Poland,
Eq. (2) "effective storage capacity":

    M_CO2 = A * h * NTG * phi * (1 - Swirr) * E * rho_CO2

Each parameter is sampled from a normal distribution (truncated to physically
sensible ranges, e.g., porosity 0-100%) for `n_iterations`, following the
approach in [MB] §4.5.2.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class NormalParam:
    """Normal distribution parameters (mean, std), with optional physical bounds."""

    mean: float
    std: float
    lower_bound: float = 0.0
    upper_bound: float = np.inf

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        draws = rng.normal(self.mean, self.std, size=n)
        return np.clip(draws, self.lower_bound, self.upper_bound)


def monte_carlo_capacity(
    area_km2: float,
    thickness_m: NormalParam,
    ntg_fraction: NormalParam,
    porosity_fraction: NormalParam,
    swirr_fraction: NormalParam,
    efficiency_fraction: NormalParam,
    co2_density_kgm3: NormalParam,
    n_iterations: int = 1000,
    random_seed: int | None = 42,
) -> np.ndarray:
    """
    Run the Monte Carlo simulation and return an array of `n_iterations` values 
    of M_CO2 in units of **Gigatons (Gt)**.

    area_km2 is considered fixed/deterministic (derived from DBSCAN clustering), 
    consistent with the [MB] approach — only h, NTG, phi, Swirr, E, and rho_CO2 
    are sampled.
    """
    rng = np.random.default_rng(random_seed)
    n = n_iterations

    area_m2 = area_km2 * 1e6  # km2 -> m2
    h = thickness_m.sample(n, rng)                      # m
    ntg = ntg_fraction.sample(n, rng)                    # fraction 0-1
    phi = porosity_fraction.sample(n, rng)               # fraction 0-1
    swirr = swirr_fraction.sample(n, rng)                # fraction 0-1
    eff = efficiency_fraction.sample(n, rng)             # fraction 0-1
    rho = co2_density_kgm3.sample(n, rng)                # kg/m3

    mass_kg = area_m2 * h * ntg * phi * (1 - swirr) * eff * rho
    mass_gt = mass_kg / 1e12  # kg -> Gt (1 Gt = 1e12 kg)
    return mass_gt


def summarize_capacity(mass_gt: np.ndarray) -> dict:
    """P10/P50/P90 summary — same format as Table 2 in [MB]."""
    p10, p50, p90 = np.percentile(mass_gt, [90, 50, 10])
    # Note: P10 in oil & gas convention = "90% exceedance percentile" (higher value,
    # more conservative regarding probability of occurrence), following [MB] Table 2 
    # convention (P10 > P50 > P90 in their capacity columns).
    return {
        "mean_Gt": float(np.mean(mass_gt)),
        "std_Gt": float(np.std(mass_gt)),
        "P10_Gt": float(p10),
        "P50_Gt": float(p50),
        "P90_Gt": float(p90),
    }


if __name__ == "__main__":
    # Sanity check with figures similar to Group I in [MB] Table 2
    # (large area, thick layer, low NTG, high density)
    demo = monte_carlo_capacity(
        area_km2=24_924,
        thickness_m=NormalParam(mean=610, std=264, lower_bound=0),
        ntg_fraction=NormalParam(mean=0.13, std=0.08, lower_bound=0, upper_bound=1),
        porosity_fraction=NormalParam(mean=0.20, std=0.03, lower_bound=0, upper_bound=1),
        swirr_fraction=NormalParam(mean=0.27, std=0.05, lower_bound=0, upper_bound=1),
        efficiency_fraction=NormalParam(mean=0.02, std=0.005, lower_bound=0, upper_bound=1),
        co2_density_kgm3=NormalParam(mean=362, std=37, lower_bound=0),
        n_iterations=1000,
    )
    print("Sanity check (similar to Group I parameters, Malay Basin paper):")
    print(summarize_capacity(demo))
    print("(Paper reference values: P10=5.22, P50=1.67, P90=0.33 Gt)")