"""
co2_thermophysics.py
=====================
Calculation of CO2 thermophysical properties (density & phase) at reservoir 
conditions, replicating the approach by de Jonge-Anderson et al. (2025) — 
Malay Basin paper, §4.4 "Pressure, temperature and fluid modelling" — 
which uses the CoolProp library (Bell et al., 2014).

All functions accept numpy arrays (vectorized) so they can be directly used
over spatial grids (e.g., interpolation results of depth/temperature/pressure).

Reference:
    Bell, I.H., Wronski, J., Quoilin, S., Lemort, V. (2014). Pure and
    pseudo-pure fluid thermophysical property evaluation and the open-source
    thermophysical property library CoolProp. Ind. Eng. Chem. Res. 53(6).
"""

from __future__ import annotations

import numpy as np

try:
    import CoolProp.CoolProp as CP

    _COOLPROP_AVAILABLE = True
except ImportError:  # pragma: no cover
    _COOLPROP_AVAILABLE = False


CO2_CRITICAL_TEMPERATURE_C = 31.1   # CO2 critical point
CO2_CRITICAL_PRESSURE_MPA = 7.38


def _check_coolprop() -> None:
    if not _COOLPROP_AVAILABLE:
        raise ImportError(
            "CoolProp is not installed. Run: "
            "pip install CoolProp --break-system-packages"
        )


def co2_density_kgm3(temperature_c: np.ndarray, pressure_mpa: np.ndarray) -> np.ndarray:
    """
    Calculate CO2 density (kg/m3) at specific temperature (Celsius) & pressure (MPa).

    Accepts scalar or numpy arrays (automatic broadcasting). Points outside the 
    valid CoolProp domain (e.g., negative/extreme pressure or temperature) 
    will return NaN instead of crashing the entire grid.
    """
    _check_coolprop()
    temperature_c = np.atleast_1d(np.asarray(temperature_c, dtype=float))
    pressure_mpa = np.atleast_1d(np.asarray(pressure_mpa, dtype=float))
    temperature_c, pressure_mpa = np.broadcast_arrays(temperature_c, pressure_mpa)

    t_kelvin = temperature_c + 273.15
    p_pascal = pressure_mpa * 1e6

    density = np.full(temperature_c.shape, np.nan)
    flat_t = t_kelvin.ravel()
    flat_p = p_pascal.ravel()
    flat_out = density.ravel()

    for i, (t_val, p_val) in enumerate(zip(flat_t, flat_p)):
        if not np.isfinite(t_val) or not np.isfinite(p_val) or p_val <= 0 or t_val <= 0:
            continue
        try:
            flat_out[i] = CP.PropsSI("D", "T", t_val, "P", p_val, "CO2")
        except ValueError:
            flat_out[i] = np.nan

    return density.reshape(temperature_c.shape)


def co2_phase(temperature_c: np.ndarray, pressure_mpa: np.ndarray) -> np.ndarray:
    """
    Simple CO2 phase classification based on the critical point
    (Tc = 31.1 C, Pc = 7.38 MPa), same as the cut-off approach in [MB].

    Returns string array: "supercritical", "liquid", "gas".
    (For screening cut-off purposes, we only need to know if it is
    "supercritical" or not — see optimal_zone_screening.py)
    """
    temperature_c = np.atleast_1d(np.asarray(temperature_c, dtype=float))
    pressure_mpa = np.atleast_1d(np.asarray(pressure_mpa, dtype=float))
    temperature_c, pressure_mpa = np.broadcast_arrays(temperature_c, pressure_mpa)

    is_supercritical = (temperature_c >= CO2_CRITICAL_TEMPERATURE_C) & (
        pressure_mpa >= CO2_CRITICAL_PRESSURE_MPA
    )
    is_liquid = (~is_supercritical) & (temperature_c < CO2_CRITICAL_TEMPERATURE_C) & (
        pressure_mpa >= CO2_CRITICAL_PRESSURE_MPA
    )

    phase = np.full(temperature_c.shape, "gas", dtype=object)
    phase[is_supercritical] = "supercritical"
    phase[is_liquid] = "liquid"
    return phase


def temperature_from_depth(
    depth_m: np.ndarray,
    geothermal_gradient_c_per_km: np.ndarray | float,
    seabed_temperature_c: float = 26.0,
) -> np.ndarray:
    """
    T(z) = T_seabed + gradient * depth_km
    Following [MB] approach §4.4 (gradient assumed linear with depth).
    """
    depth_m = np.asarray(depth_m, dtype=float)
    return seabed_temperature_c + geothermal_gradient_c_per_km * (depth_m / 1000.0)


def pressure_from_depth(
    depth_m: np.ndarray,
    is_overpressured: np.ndarray | bool,
    hydrostatic_gradient_mpa_per_km: float = 10.0,
    overpressure_gradient_mpa_per_km: float = 20.0,
) -> np.ndarray:
    """
    P(z) = gradient * depth_km, using different gradients for normal 
    vs overpressure zones — following [MB] §4.4 & §5.3.

    `is_overpressured` is a boolean array/scalar with the same shape as depth_m
    (result of the overpressure flag per grid cell, usually from a separate 
    overpressure zone mapping — see docs/methodology.md).
    """
    depth_m = np.asarray(depth_m, dtype=float)
    is_overpressured = np.asarray(is_overpressured, dtype=bool)
    gradient = np.where(
        is_overpressured, overpressure_gradient_mpa_per_km, hydrostatic_gradient_mpa_per_km
    )
    return gradient * (depth_m / 1000.0)


if __name__ == "__main__":
    # Quick sanity check — compare with reference figures in [MB] Fig. 9
    demo_depth = np.array([500, 1500, 2500, 3500])
    demo_temp = temperature_from_depth(demo_depth, geothermal_gradient_c_per_km=35)
    demo_overpressure = np.array([False, False, True, True])
    demo_pressure = pressure_from_depth(demo_depth, demo_overpressure)
    demo_density = co2_density_kgm3(demo_temp, demo_pressure)
    demo_phase = co2_phase(demo_temp, demo_pressure)

    for d, t, p, rho, ph in zip(demo_depth, demo_temp, demo_pressure, demo_density, demo_phase):
        print(f"depth={d:5.0f} m | T={t:5.1f} C | P={p:5.1f} MPa | "
              f"rho_CO2={rho:6.1f} kg/m3 | phase={ph}")