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
- **Tectonic setting screening**: Classification of basins based on tectonic styles to infer general reservoir quality, thermal gradients, and structural risk profiles.

### 1.2 Nooraiepour et al. (2025) — Poland ("PL")
> *Geological CO2 storage assessment in emerging CCS regions: Review of
> sequestration potential, policy development, and socio-economic factors
> in Poland.* International Journal of Greenhouse Gas Control, 148, 104524.

Contributions adapted:
- **Resource-reserve pyramid**: theoretical → effective → practical → matched capacity (Fig. 3 in their paper).
- **Storage Readiness Level (SRL)**: a 1-9 scale to honestly state the maturity level of a study/site, rather than letting the reader assume all figures are equivalent.
- Transparent stance on data limitations in countries/regions that have just begun developing CCS (sparse data, limited research access, immature industry-academia collaboration)—precisely the current situation in Indonesia.

---

## 2. Why this project is divided into Tier 1 / Tier 2

| | Tier 1 (national screening) | Tier 2 (Sunda-Asri deep-dive) |
|---|---|---|
| **Analogy** | Poland paper (basin comparison, Table 2) | Malay Basin paper (grid + cut-off + clustering) |
| **Target SRL** | 1 (inventory) / 2 for the quantitative subset — see §2.1 | 1-2 (requires more detailed digitized data) |
| **Data** | Basin-level public metadata, GEBCO bathymetry, tectonic classification (`TEC_EXP`), and emissions data | Spatial grid (depth/temp/pressure) from digitization |
| **Output** | Full SRL 1 inventory + multi-stage filtered quantitative ranking (Top 3 Cost-Effective Elite Basins) + proximity map | Optimal zone map + capacity distribution per cluster |

### 2.1 Note on the maturity pre-filter (SRL 1 inventory vs. SRL 2 quantitative subset)

Tier 1's target SRL is **SRL 1**: a basin-scale inventory built from public metadata, in the spirit of [PL]'s transparent stance on sparse-data regions. `notebooks/00_tier1_national_screening.ipynb` therefore keeps **every** basin in its Section 1 inventory table, labelled SRL 1 ("Unexplored") or SRL 2 ("Producing"/"Discovery"/"Prospect") — no basin is silently dropped from the overall deliverable.

However, Sections 2 onward (geophysical filtering, Monte Carlo capacity, and emitter proximity ranking) operate on a separate, explicit feasibility gate:
1. **SRL 2 Gate**: Assigning a quantitative capacity distribution to a basin with zero subsurface confirmation (no wells, no discovered hydrocarbons) would manufacture false precision. SRL 1 basins are therefore excluded from the quantitative ranking.
2. **Geographical Gate (GEBCO Bathymetry)**: To minimize onshore land-use conflicts and prioritize high-capacity fluid sinks, a digital elevation filter is applied at each basin's geographic centroid. Only basins with an elevation $< 0$ m (Offshore/Coastal) are carried forward; onshore basins ($\ge 0$ m) are excluded.

---

## 3. Tier 1 Screening & Multi-Criteria Ranking Workflow

To transition from the broader offshore SRL 2 subset to a highly qualified recommendation for detailed study, the Tier 1 pipeline uses a multi-stage filtering and scoring mechanism:

```
[Full Basin Inventory (SRL 1 & 2)]
                │
                ▼
      [SRL 2 Feasibility Gate]   ──► (SRL 1 Unexplored Basins Retained in Inventory Only)
                │
                ▼
   [GEBCO Bathymetry Filter]     ──► (Onshore Basins [>= 0m] Filtered Out)
                │
                ▼
     [Geological Hard Filter]    ──► (Fore-Arc, Trench, Active Rifts, & Unconfirmed Prospects Excluded)
                │
                ▼
   [Cost-Effective Scoring Index]
(60% Emitter Proximity / 40% P50 Volume)
                │
                ▼
     [Recommended Top 3 Basins]
```

### 3.1 Tectonic Classification Matrix
We apply a geological suitability scoring framework adapted from tectonic class concepts in **de Jonge-Anderson et al. (2025)**:
*   **High Priority (Score 3): Back-Arc & Passive Margin.** Stable post-rift or passive margin settings. Typically characterized by excellent regional reservoir-seal duos and stable thermal gradients.
*   **Medium Priority (Score 2): Intra-Arc / Rifted Graben / Foreland / Intermontane.** Characterized by higher geothermal gradients (which decrease $CO_2$ density) or complex reservoir compartmentalization.
*   **Low Priority / Disqualified (Score 1): Fore-Arc / Trench / Deep Oceanic.** Subject to active seismicity, major structural fault risks, caprock integrity concerns, and poor reservoir preservation at deep depths.

### 3.2 Elite Hard Filter
The scoring pipeline applies a strict **Hard Filter** to eliminate unconfirmed play elements and elevated structural risks. To qualify for the final ranking:
1. The basin must belong to a **High Priority Tectonic Class** (Back-Arc or Passive Margin).
2. The basin's exploration status must be **Producing** or **Discovery** (eliminating unconfirmed "Prospect" basins that lack robust hydrocarbon or deep well confirmation).

### 3.3 Cost-Effective Scoring Formula
Basins that pass the elite hard filter are locally normalized (scaled $0$ to $1$) and ranked using a weighted multi-criteria index designed to balance engineering feasibility with resource size:

$$\text{Cost-Effective Score} = 0.6 \times \text{Norm(Proximity)} + 0.4 \times \text{Norm(Volume)}$$

Where:
*   **$\text{Norm(Proximity)}$** is based on the total annual emission volume (Mtpa) of industrial sources located within a 200 km search radius of the basin centroid.
*   **$\text{Norm(Volume)}$** is based on the median P50 physical storage capacity (Gt) derived from basin-scale Monte Carlo volumetric simulations.

The output ranks the top 3 recommended basins for potential Tier 2 selection.

---

## 4. Basins selected for Tier 2

**Sunda-Asri Basin** was chosen for three mutually reinforcing reasons:

1. **Policy**: Designated by the Indonesian government (along with Bintuni Basin) as a strategic CCS hub priority location.
2. **Structural analogy**: It is part of the same Sundaland rift basin system as the Malay Basin (Eocene-Oligocene syn-rift, Miocene post-rift), making the conceptual framework of [MB] the most relevant to transfer here compared to other basins in Indonesia.
3. **Existing baseline comparisons**: Rough capacity estimates already exist in the literature (Hedriana et al., 2017; Iskandar et al., 2013) which can be used as a sanity check—precisely the pattern [MB] used to compare their results against Hasbollah et al. (2020) and Zhang & Lau (2022).

### 4.1 Relationship to the Tier 1 notebook's automated ranking

These three qualitative criteria — not the Tier 1 notebook's automated ranking (`robust_picks` or `cost_effective_score` in Section 4b of `00_tier1_national_screening.ipynb`) — are the primary basis for choosing Sunda-Asri. 

The notebook's ranking functions as a **complementary sanity check**: it reports where Sunda-Asri falls on the dimensions Tier 1 can actively measure (illustrative volumetric capacity, elevation, tectonic classification, and emitter proximity within 200 km) so a reader can see whether the qualitative selection is also reasonable computationally. It is not itself the sole selection mechanism—if a future run using different sample data places Sunda-Asri outside the computational top picks (for example, if it is filtered out due to its "Rifted Graben" status falling outside the strict Back-Arc filter), that does not overturn the choice, as the choice was never derived from that automated ranking in the first place.

---

## 5. Limitations (read before using any numbers in this repo)

This project **does not** have access to:
- Well data (stratigraphic tops, wireline logs, formation pressure tests) which were the backbone of [MB]—they gained access through a partnership with PETRONAS.
- Local porosity-depth data calibrated per Indonesian basin—currently, `config.yaml` uses a generic proxy for both the porosity-depth decay trend (§`tier2_reservoir_proxy`) and the geothermal gradient (25-35°C/km band from global literature, following [PL]'s assumption for Poland).
- Seismic-validated depth structure maps, or an official digitization of the Sunda-Asri basin boundary/fault network.

Consequences:
- All capacity figures in `notebooks/00_tier1_national_screening.ipynb` use **illustrative basin-scale geometry**, not measurement/digitization results, and are computed only for the SRL 2 subset described in §2.1. This is explicitly noted in every relevant cell and printed at runtime.
- `notebooks/01_tier2_sunda_asri_workflow.ipynb` uses an **illustrative hand-drawn boundary/fault network** and a **synthetic bowl-shaped depth surface** unless you supply real GEBCO/GlobSed grids and a QGIS-digitized boundary (see `docs/data_provenance.md`). The notebook always prints which inputs were real vs. illustrative for a given run — check that output before citing a number.
- This project is realistically capped at **SRL 1-2**, not SRL 3+ like [MB].
- Any claim of "X Gt potential in Y basin" from external sources (e.g., claims of >400 Gt CO2-eq nationally in depleted reservoirs according to Presidential Regulation 14/2024, or ~14.8 Gt of saline formation in South Sumatra + Java from Hedriana et al., 2017) is cited as **context/benchmark**, not as calculation results from this project.

What is **not** a limitation: CO2 density and phase in both tiers are computed from the real CoolProp equation of state (`src/co2_thermophysics.py`), and all three [MB] cut-off criteria (porosity, CO2 density, fault distance) are applied together in Tier 2 — these parts of the methodology are implemented as designed, independent of whether the underlying geometry is real or illustrative.

---

## 6. Roadmap for SRL improvement (technical)

1. Digitize boundary & depth structure of Sunda-Asri from Geological Agency maps (georeferencing in QGIS) → elevate Tier 2 from "illustrative points" to "actual spatial grids."
2. Replace geothermal gradient proxy with points from the 2024 Global Heat Flow Database that fall within Indonesian territory + interpolation (kriging/IDW).
3. Replace synthetic emitter data with actual Global Energy Monitor trackers.
4. Recalibrate cut-offs (`config.yaml`) once local porosity data is available from Indonesian reports/papers that can be cited openly (e.g., open-access IPA proceedings).