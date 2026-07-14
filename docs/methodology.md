# Methodology

This document explains how this project's workflow adapts two reference studies, the design decisions made, and—most importantly—the **limitations that must be understood before using any results from this repository outside of educational/portfolio contexts.**

## 1. Two reference frameworks
### 1.1 de Jonge-Anderson et al. (2025) — Malay Basin ("MB")
> *Regional screening of saline aquifers in the Malay Basin for CO2 storage.*
> International Journal of Greenhouse Gas Control, 143, 104347.

Contributions adapted:
- Step-by-step workflow: depth structure → porosity-depth trend → temperature (geothermal gradient) → pressure (hydrostatic/overpressure) → CO2 thermophysical properties (CoolProp) → cut-offs → clustering (DBSCAN) → Monte Carlo volumetric capacity.
- Definition of "optimal" vs. "sub-optimal" vs. "non-viable" zones based on dual cut-offs (porosity, CO2 density, distance to faults).
- Goodman et al. (2011) capacity equation:
  `M_CO2 = A * h * NTG * phi * (1 - Swirr) * E * rho_CO2`

### 1.2 Nooraiepour et al. (2025) — Poland ("PL")
> *Geological CO2 storage assessment in emerging CCS regions: Review of
> sequestration potential, policy development, and socio-economic factors
> in Poland.* International Journal of Greenhouse Gas Control, 148, 104524.

Contributions adapted:
- **Resource-reserve pyramid**: theoretical → effective → practical → matched capacity (Fig. 3 in their paper).
- **Storage Readiness Level (SRL)**: a 1-9 scale to honestly state the maturity level of a study/site, rather than letting the reader assume all figures are equivalent.
- Transparent stance on data limitations in countries/regions that have just begun developing CCS (sparse data, limited research access, immature industry-academia collaboration)—precisely the current situation in Indonesia.

## 2. Why this project is divided into Tier 1 / Tier 2
| | Tier 1 (national screening) | Tier 2 (Sunda-Asri deep-dive) |
|---|---|---|
| Analogy | Poland paper (basin comparison, Table 2) | Malay Basin paper (grid + cut-off + clustering) |
| Target SRL | 1 | 1-2 (requires more detailed digitized data) |
| Data | Basin-level, public metadata | Spatial grid (depth/temp/pressure) from digitization |
| Output | Comparison table + proximity map | Optimal zone map + capacity distribution per cluster |

## 3. Basins selected for Tier 2

**Sunda-Asri Basin** was chosen for three mutually reinforcing reasons:

1. **Policy**: designated by the Indonesian government (along with Bintuni Basin) as a strategic CCS hub priority location.
2. **Structural analogy**: it is part of the same Sundaland rift basin system as the Malay Basin (Eocene-Oligocene syn-rift, Miocene post-rift), making the conceptual framework of [MB] the most relevant to transfer here compared to other basins in Indonesia.
3. **Existing baseline comparisons**: rough capacity estimates already exist in the literature (Hedriana et al., 2017; Iskandar et al., 2013) which can be used as a sanity check—precisely the pattern [MB] used to compare their results against Hasbollah et al. (2020) and Zhang & Lau (2022).

## 4. Limitations (read before using any numbers in this repo)

This project **does not** have access to:
- Well data (stratigraphic tops, wireline logs, formation pressure tests) which were the backbone of [MB]—they gained access through a partnership with PETRONAS.
- Local porosity-depth data calibrated per Indonesian basin—currently, `config.yaml` uses a generic proxy (25-35°C/km band from global literature, following [PL]'s assumption for Poland).
- Seismic-validated depth structure maps.

Consequences:
- All capacity figures in `notebooks/00_tier1_national_screening.ipynb` use **random illustrative geometry**, not measurement/digitization results. This is explicitly noted in every relevant cell.
- This project is realistically capped at **SRL 1-2**, not SRL 3+ like [MB].
- Any claim of "X Gt potential in Y basin" from external sources (e.g., claims of >400 Gt CO2-eq nationally in depleted reservoirs according to Presidential Regulation 14/2024, or ~14.8 Gt of saline formation in South Sumatra + Java from Hedriana et al., 2017) is cited as **context/benchmark**, not as calculation results from this project.

## 5. Roadmap for SRL improvement (technical)

1. Digitize boundary & depth structure of Sunda-Asri from Geological Agency maps (georeferencing in QGIS) → elevate Tier 2 from "illustrative points" to "actual spatial grids."
2. Replace geothermal gradient proxy with points from the 2024 Global Heat Flow Database that fall within Indonesian territory + interpolation (kriging/IDW).
3. Replace synthetic emitter data with actual Global Energy Monitor trackers.
4. Recalibrate cut-offs (`config.yaml`) once local porosity data is available from Indonesian reports/papers that can be cited openly (e.g., open-access IPA proceedings).

