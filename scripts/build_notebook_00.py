"""
build_notebook_00.py
======================
A one-off script to BUILD notebooks/00_tier1_national_screening.ipynb
programmatically (nbformat), ensuring the notebook content is consistent and
easily reproducible. Once built, the notebook should be executed via:

    jupyter nbconvert --to notebook --execute --inplace notebooks/00_tier1_national_screening.ipynb

This is NOT part of the analysis pipeline itself — it is intended to be run once
during setup, or if you want to restructure the notebook from scratch.
"""

import nbformat as nbf

nb = nbf.v4.new_notebook()
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text))


def code(text):
    cells.append(nbf.v4.new_code_cell(text))


# =============================================================================
md(r"""
# Tier 1 — National Screening: CCS Potential in Indonesian Basins

**Status: PROTOTYPE — most data in this notebook are EXAMPLES/PLACEHOLDERS.**

This notebook replicates the *spirit* of two studies:

- **de Jonge-Anderson et al. (2025)** — *Regional screening of saline aquifers
  in the Malay Basin for CO2 storage*, IJGGC 143 — for the technical workflow
  (subsurface cut-offs, CO2 thermophysics, clustering, Monte Carlo capacity).
- **Nooraiepour et al. (2025)** — *Geological CO2 storage assessment in
  emerging CCS regions: ... Poland*, IJGGC 148 — for the strategic framework:
  **resource-reserve pyramid** and **Storage Readiness Level (SRL)**.

The purpose of this notebook (Tier 1) is **not** to generate capacity figures
usable for business/investment decisions — but to build a multi-basin comparison
framework akin to **Table 2 in the Poland paper**, serving as a roadmap for
deeper Tier 2 studies (`01_tier2_sunda_asri_workflow.ipynb`).

> ⚠️ **Read this first**: the capacity columns, precise coordinates, and some
> geological attributes in this notebook use **illustrative data**
> (`src/fetch_open_data.py --mode sample`), not actual digitized/downloaded
> data. See `docs/data_provenance.md` for a list of real data sources and
> `docs/methodology.md` for full limitations.
""")

# =============================================================================
md("## 0. Setup")

code(r"""
import sys
from pathlib import Path

REPO_ROOT = Path.cwd().parent if (Path.cwd() / "notebooks").exists() is False and (Path.cwd().name == "notebooks") else Path.cwd()
# More robust fallback: find the folder containing config.yaml
_p = Path.cwd()
while not (_p / "config.yaml").exists() and _p != _p.parent:
    _p = _p.parent
REPO_ROOT = _p
sys.path.insert(0, str(REPO_ROOT / "src"))

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from load_config import load_config
from emission_source_proximity import nearest_emitter_distance
from montecarlo_capacity import monte_carlo_capacity, summarize_capacity, NormalParam

cfg = load_config(REPO_ROOT / "config.yaml")
pd.set_option("display.max_colwidth", 60)
print("Repo root:", REPO_ROOT)
print("Config loaded, target Tier 1 SRL:", cfg["storage_readiness"]["tier1_target_srl"])
""")

# =============================================================================
md("""## 1. Load basin & emission source data (EXAMPLE data)

If sample files do not exist, generate them first using `fetch_open_data.py`.
""")

code(r"""
import subprocess

basins_path = REPO_ROOT / "data" / "external" / "sample_basins_indonesia.csv"
emitters_path = REPO_ROOT / "data" / "external" / "sample_emitters_indonesia.csv"

if not basins_path.exists() or not emitters_path.exists():
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "src" / "fetch_open_data.py"), "--mode", "sample"],
        check=True,
    )

basins = pd.read_csv(basins_path)
emitters = pd.read_csv(emitters_path)
print(f"{len(basins)} basins, {len(emitters)} emitter points (sample) loaded.")
basins[["basin", "region", "basin_type", "ccs_policy_priority", "srl_placeholder"]]
""")

# =============================================================================
md("""## 2. Storage Readiness Level (SRL) framework per basin

Following the SRL definitions in the Poland paper (Akhurst et al., 2019, adapted):

| SRL | Description |
|---|---|
| 1 | First-pass, basin/country-scale assessment using existing geological data |
| 2 | Sites with theoretical capacity mapped systematically |
| 3 | Detailed site-specific screening + preliminary project concept |

All 8 sample basins in this notebook are placed at **SRL 1** — this is honest
given we are only using basin-level public data, with no well data available yet.
""")

code(r"""
srl_labels = {1: "SRL 1 - basin-scale, public data", 2: "SRL 2 - systematically mapped capacity", 3: "SRL 3 - detailed site-specific screening"}
basins["srl_label"] = basins["srl_placeholder"].map(srl_labels)
basins[["basin", "srl_placeholder", "srl_label", "ccs_policy_priority"]]
""")

# =============================================================================
md("""## 3. Proximity to CO2 emission sources

Calculating great-circle distances from each basin centroid to the nearest
emitter (analogous to the analysis in Fig. 7 of the Poland paper: *"spatial analysis
illustrates proximity relationships between emission sources and
sequestration opportunities"*). Emitter data here is synthetic — replace
with genuine Global Energy Monitor tracker data for professional-grade results.
""")

code(r"""
basins_with_proximity = nearest_emitter_distance(
    basins, emitters,
    basin_lat_col="lat", basin_lon_col="lon",
    emitter_lat_col="lat", emitter_lon_col="lon",
    emitter_capacity_col="capacity_mtpa_co2_est",
)
cols = ["basin", "nearest_emitter_name", "nearest_emitter_km", "nearest_emitter_capacity"]
basins_with_proximity[cols].sort_values("nearest_emitter_km")
""")

# =============================================================================
md("""## 4. Illustrative resource-reserve pyramid (Tier reduction)

Demonstration of the **theoretical -> effective capacity** concept (Poland paper,
Fig. 3 & Eq. 1-2) using Monte Carlo, utilizing **illustrative geometries**
(not actual digitized results) for each basin. The efficiency factor E
for saline aquifers is set to 1-2%, consistent with general ranges in
literature (Poland & Malay Basin papers).

> This is purely to demonstrate the *shape* of the P10/P50/P90 distributions
> — do not interpret the absolute figures as real estimates.
""")

code(r"""
rng = np.random.default_rng(7)
illustrative_results = []

for _, row in basins.iterrows():
    # Illustrative basin-scale geometry (NOT from actual digitization)
    area_km2 = rng.uniform(3_000, 25_000)
    mc = monte_carlo_capacity(
        area_km2=area_km2,
        thickness_m=NormalParam(mean=rng.uniform(150, 500), std=100, lower_bound=0),
        ntg_fraction=NormalParam(mean=rng.uniform(0.15, 0.4), std=0.1, lower_bound=0, upper_bound=1),
        porosity_fraction=NormalParam(mean=rng.uniform(0.15, 0.28), std=0.04, lower_bound=0, upper_bound=1),
        swirr_fraction=NormalParam(
            mean=cfg["capacity_equation"]["swirr_mean"],
            std=cfg["capacity_equation"]["swirr_std"],
            lower_bound=0, upper_bound=1,
        ),
        efficiency_fraction=NormalParam(
            mean=cfg["capacity_equation"]["efficiency_factor_percent_mean"] / 100,
            std=cfg["capacity_equation"]["efficiency_factor_percent_std"] / 100,
            lower_bound=0, upper_bound=1,
        ),
        co2_density_kgm3=NormalParam(mean=rng.uniform(300, 450), std=40, lower_bound=0),
        n_iterations=cfg["capacity_equation"]["monte_carlo_iterations"],
        random_seed=int(rng.integers(0, 10_000)),
    )
    stats = summarize_capacity(mc)
    stats["basin"] = row["basin"]
    stats["illustrative_area_km2"] = area_km2
    illustrative_results.append(stats)

illustrative_df = pd.DataFrame(illustrative_results).set_index("basin")
illustrative_df = illustrative_df[["illustrative_area_km2", "P10_Gt", "P50_Gt", "P90_Gt", "mean_Gt", "std_Gt"]]
illustrative_df.round(2)
""")

# =============================================================================
md("""## 5. Summary visualization (style of Table 2 / Fig. 7 Poland paper)""")

code(r"""
fig, ax = plt.subplots(figsize=(9, 5))
plot_df = illustrative_df.sort_values("P50_Gt", ascending=True)
ax.barh(plot_df.index, plot_df["P50_Gt"], color="#2c7a7b")
ax.errorbar(
    plot_df["P50_Gt"], plot_df.index,
    xerr=[plot_df["P50_Gt"] - plot_df["P90_Gt"], plot_df["P10_Gt"] - plot_df["P50_Gt"]],
    fmt="none", ecolor="black", capsize=3,
)
ax.set_xlabel("ILLUSTRATIVE Capacity (Gt CO2), P90-P50-P10")
ax.set_title("Comparison of illustrative capacity between basins (PLACEHOLDER DATA)\n"
              "-- not official estimates, see docs/methodology.md --")
plt.tight_layout()
plt.savefig(REPO_ROOT / "figures" / "tier1_illustrative_capacity_comparison.png", dpi=150)
plt.show()
""")

code(r"""
try:
    import folium

    m = folium.Map(location=[-2.5, 113], zoom_start=5, tiles="cartodbpositron")

    for _, row in basins.iterrows():
        color = "crimson" if row["ccs_policy_priority"] else "steelblue"
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=9,
            color=color,
            fill=True,
            fill_opacity=0.85,
            popup=f"<b>{row['basin']}</b><br>{row['region']}<br>{row['note']}",
        ).add_to(m)

    for _, row in emitters.iterrows():
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=3,
            color="gray",
            fill=True,
            fill_opacity=0.5,
            popup=f"{row['name']} ({row['sector']})",
        ).add_to(m)

    legend_html = (
        '<div style="position: fixed; bottom: 30px; left: 30px; z-index:9999; '
        'background: white; padding: 10px; border: 1px solid #999; font-size: 13px;">'
        '<b>Legend</b><br>'
        '<span style="color:crimson;">&#9679;</span> CCS priority basin (official policy)<br>'
        '<span style="color:steelblue;">&#9679;</span> Other basins<br>'
        '<span style="color:gray;">&#9679;</span> Emission sources (EXAMPLE/SYNTHETIC)'
        '</div>'
    )
    m.get_root().html.add_child(folium.Element(legend_html))

    map_path = REPO_ROOT / "figures" / "tier1_indonesia_basins_map.html"
    m.save(str(map_path))
    print("Interactive map saved to:", map_path)
    m
except ImportError:
    print("folium is not installed - skipping map visualization.")
""")

# =============================================================================
md("""## 6. Summary & next steps

**What has been demonstrated in this notebook:**
1. SRL framework per basin (Poland paper style §3.2)
2. Basin <-> emitter proximity analysis (Poland paper style Fig. 7)
3. Example resource-reserve pyramid workflow with Monte Carlo (Poland Eq. 1-2
   & Malay Basin Eq. 2), using illustrative geometries

**What has NOT been done (honest limitations for this prototype):**
- Actual basin boundaries (still rough centroids, not polygons from Geological Agency maps)
- Actual Global Energy Monitor emitter data (still synthetic)
- Local Indonesian geothermal gradient & porosity-depth trends (still using generic proxies in `config.yaml`)

**Next steps**: `01_tier2_sunda_asri_workflow.ipynb` — full replication of
the workflow: grid depth/temperature/pressure -> CO2 thermophysics ->
cut-off -> DBSCAN -> Monte Carlo for the Sunda-Asri Basin specifically, once
digitized data becomes available (see `docs/data_provenance.md` for download
checklist).
""")

nb["cells"] = cells
nb["metadata"] = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12"},
}

out_path = "notebooks/00_tier1_national_screening.ipynb"
with open(out_path, "w", encoding="utf-8") as f:
    nbf.write(nb, f)
print(f"Notebook written to {out_path} ({len(cells)} cells)")