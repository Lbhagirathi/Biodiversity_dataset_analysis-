"""
Denmark Biodiversity Monitoring Dashboard
==========================================
Interactive Plotly Dash app showing species observations on a gridded Denmark map.
Uses simulated GBIF-style occurrence data. Replace `generate_sample_data()` with
real data loading (e.g. from a CSV or API) when available.

Requirements:
    pip install dash plotly pandas numpy
    
Run:
    python denmark_biodiversity_dashboard.py
Then open http://127.0.0.1:8050 in your browser.
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# ---------------------------------------------------------------------------
# 1. SAMPLE DATA GENERATION
#    Replace this section with your real dataset.
#    Expected columns: species, year, lat, lon, count
# ---------------------------------------------------------------------------

np.random.seed(42)

SPECIES_LIST = [
    "White Stork (Ciconia ciconia)",
    "Common Swift (Apus apus)",
    "Red Kite (Milvus milvus)",
    "Eurasian Curlew (Numenius arquata)",
    "Northern Lapwing (Vanellus vanellus)",
    "Atlantic Puffin (Fratercula arctica)",
    "Common Crane (Grus grus)",
    "Barn Swallow (Hirundo rustica)",
    "European Hedgehog (Erinaceus europaeus)",
    "Eurasian Otter (Lutra lutra)",
]

# Denmark approximate bounding box
DK_LAT_MIN, DK_LAT_MAX = 54.5, 57.8
DK_LON_MIN, DK_LON_MAX = 8.0, 15.2
YEARS = list(range(2010, 2024))

# Grid resolution in degrees (~10 km cells over Denmark)
GRID_RES = 0.25


def generate_sample_data():
    """
    Generates realistic-looking species observation records for Denmark.
    Each species has a 'preferred region' to make spatial patterns meaningful.
    """
    records = []
    species_centers = {
        "White Stork (Ciconia ciconia)":         (55.4, 9.5),
        "Common Swift (Apus apus)":              (55.7, 12.5),
        "Red Kite (Milvus milvus)":              (56.2, 10.0),
        "Eurasian Curlew (Numenius arquata)":    (57.0, 9.0),
        "Northern Lapwing (Vanellus vanellus)":  (55.5, 11.8),
        "Atlantic Puffin (Fratercula arctica)":  (57.5, 10.5),
        "Common Crane (Grus grus)":              (56.5, 9.3),
        "Barn Swallow (Hirundo rustica)":        (55.9, 12.0),
        "European Hedgehog (Erinaceus europaeus)": (55.6, 10.8),
        "Eurasian Otter (Lutra lutra)":          (56.8, 8.8),
    }

    for species in SPECIES_LIST:
        center_lat, center_lon = species_centers[species]
        for year in YEARS:
            n_records = np.random.randint(40, 120)
            lats = np.clip(
                np.random.normal(center_lat, 0.8, n_records),
                DK_LAT_MIN, DK_LAT_MAX
            )
            lons = np.clip(
                np.random.normal(center_lon, 1.2, n_records),
                DK_LON_MIN, DK_LON_MAX
            )
            counts = np.random.randint(1, 30, n_records)
            # Add a mild positive trend over years to simulate real-world dynamics
            trend_factor = 1 + 0.03 * (year - 2010)
            counts = np.clip((counts * trend_factor).astype(int), 1, 50)
            for lat, lon, count in zip(lats, lons, counts):
                records.append({
                    "species": species,
                    "year": year,
                    "lat": round(lat, 4),
                    "lon": round(lon, 4),
                    "count": int(count),
                })

    return pd.DataFrame(records)


def snap_to_grid(df, res=GRID_RES):
    """
    Snaps raw observation points to a regular grid and aggregates counts.
    This is the spatial aggregation step — crucial for principled analysis.
    """
    df = df.copy()
    df["grid_lat"] = (np.floor(df["lat"] / res) * res + res / 2).round(4)
    df["grid_lon"] = (np.floor(df["lon"] / res) * res + res / 2).round(4)
    grouped = (
        df.groupby(["grid_lat", "grid_lon"])
        .agg(total_count=("count", "sum"), n_records=("count", "count"))
        .reset_index()
    )
    return grouped


def build_grid_lines(lat_min, lat_max, lon_min, lon_max, res):
    """
    Returns Plotly Scattermapbox traces for horizontal and vertical grid lines
    over Denmark, drawn as thin dashed lines.
    """
    traces = []
    # Horizontal lines (constant latitude)
    lats = np.arange(lat_min, lat_max + res, res)
    for lat in lats:
        traces.append(go.Scattermapbox(
            lat=[lat, lat],
            lon=[lon_min, lon_max],
            mode="lines",
            line=dict(width=0.4, color="rgba(180,180,180,0.5)"),
            hoverinfo="skip",
            showlegend=False,
        ))
    # Vertical lines (constant longitude)
    lons = np.arange(lon_min, lon_max + res, res)
    for lon in lons:
        traces.append(go.Scattermapbox(
            lat=[lat_min, lat_max],
            lon=[lon, lon],
            mode="lines",
            line=dict(width=0.4, color="rgba(180,180,180,0.5)"),
            hoverinfo="skip",
            showlegend=False,
        ))
    return traces


# ---------------------------------------------------------------------------
# 2. LOAD & PREP DATA
# ---------------------------------------------------------------------------

RAW_DATA = generate_sample_data()

# Pre-compute yearly totals per species for trend chart
YEARLY_TOTALS = (
    RAW_DATA.groupby(["species", "year"])["count"]
    .sum()
    .reset_index()
    .rename(columns={"count": "total"})
)

# Pre-compute per-species totals across all years for bar chart
SPECIES_TOTALS = (
    RAW_DATA.groupby("species")["count"]
    .sum()
    .reset_index()
    .rename(columns={"count": "total"})
    .sort_values("total", ascending=False)
)

# ---------------------------------------------------------------------------
# 3. APP LAYOUT
# ---------------------------------------------------------------------------

MAPBOX_STYLE = "carto-positron"  # Free tile — no token required

app = dash.Dash(__name__, title="Denmark Biodiversity Monitor")

app.layout = html.Div(
    style={
        "fontFamily": "Inter, sans-serif",
        "backgroundColor": "#f5f6fa",
        "minHeight": "100vh",
        "padding": "0",
    },
    children=[

        # ── Header ──────────────────────────────────────────────────────────
        html.Div(
            style={
                "background": "#1b4332",
                "color": "#ffffff",
                "padding": "18px 32px",
                "display": "flex",
                "alignItems": "center",
                "gap": "16px",
            },
            children=[
                html.Div("🦅", style={"fontSize": "28px"}),
                html.Div([
                    html.H1(
                        "Denmark Biodiversity Monitoring Dashboard",
                        style={"margin": "0", "fontSize": "20px", "fontWeight": "600"},
                    ),
                    html.P(
                        "Gridded species observations · 2010–2023 · Simulated GBIF-style data",
                        style={"margin": "2px 0 0", "fontSize": "13px", "opacity": "0.75"},
                    ),
                ]),
            ],
        ),

        # ── Controls bar ────────────────────────────────────────────────────
        html.Div(
            style={
                "background": "#ffffff",
                "borderBottom": "1px solid #e0e0e0",
                "padding": "16px 32px",
                "display": "flex",
                "alignItems": "center",
                "gap": "40px",
                "flexWrap": "wrap",
            },
            children=[
                html.Div([
                    html.Label(
                        "Species",
                        style={"fontSize": "12px", "fontWeight": "600",
                               "color": "#555", "marginBottom": "6px", "display": "block"},
                    ),
                    dcc.Dropdown(
                        id="species-dropdown",
                        options=[{"label": s, "value": s} for s in SPECIES_LIST],
                        value=SPECIES_LIST[0],
                        clearable=False,
                        style={"width": "320px", "fontSize": "14px"},
                    ),
                ]),
                html.Div([
                    html.Label(
                        "Year",
                        style={"fontSize": "12px", "fontWeight": "600",
                               "color": "#555", "marginBottom": "6px", "display": "block"},
                    ),
                    html.Div(
                        style={"paddingTop": "4px"},
                        children=[
                            dcc.Slider(
                                id="year-slider",
                                min=min(YEARS),
                                max=max(YEARS),
                                step=1,
                                value=2020,
                                marks={y: str(y) for y in YEARS if y % 2 == 0},
                                tooltip={"placement": "bottom", "always_visible": True},
                            ),
                        ],
                    ),
                ], style={"flex": "1", "minWidth": "320px"}),
            ],
        ),

        # ── Main content ────────────────────────────────────────────────────
        html.Div(
            style={"padding": "20px 32px", "display": "flex", "flexDirection": "column", "gap": "20px"},
            children=[

                # Row 1: Map + KPI strip
                html.Div(
                    style={"display": "flex", "gap": "20px", "alignItems": "flex-start"},
                    children=[

                        # Map panel
                        html.Div(
                            style={
                                "flex": "2",
                                "background": "#fff",
                                "borderRadius": "10px",
                                "boxShadow": "0 1px 4px rgba(0,0,0,0.08)",
                                "overflow": "hidden",
                            },
                            children=[
                                html.Div(
                                    id="map-header",
                                    style={"padding": "14px 18px 0",
                                           "fontSize": "14px", "fontWeight": "600", "color": "#222"},
                                ),
                                html.P(
                                    "Dot size ∝ observation count · Grid resolution 0.25°",
                                    style={"padding": "0 18px", "fontSize": "11px",
                                           "color": "#888", "margin": "2px 0 0"},
                                ),
                                dcc.Graph(
                                    id="map-graph",
                                    config={"displayModeBar": False},
                                    style={"height": "460px"},
                                ),
                            ],
                        ),

                        # KPI sidebar
                        html.Div(
                            id="kpi-panel",
                            style={
                                "flex": "0 0 200px",
                                "display": "flex",
                                "flexDirection": "column",
                                "gap": "14px",
                            },
                        ),
                    ],
                ),

                # Row 2: Trend + bar chart
                html.Div(
                    style={"display": "flex", "gap": "20px"},
                    children=[
                        html.Div(
                            style={
                                "flex": "1",
                                "background": "#fff",
                                "borderRadius": "10px",
                                "boxShadow": "0 1px 4px rgba(0,0,0,0.08)",
                                "padding": "4px",
                            },
                            children=[dcc.Graph(id="trend-graph", config={"displayModeBar": False})],
                        ),
                        html.Div(
                            style={
                                "flex": "1",
                                "background": "#fff",
                                "borderRadius": "10px",
                                "boxShadow": "0 1px 4px rgba(0,0,0,0.08)",
                                "padding": "4px",
                            },
                            children=[dcc.Graph(id="bar-graph", config={"displayModeBar": False})],
                        ),
                    ],
                ),

                # Row 3: Monthly distribution (within the selected year)
                html.Div(
                    style={
                        "background": "#fff",
                        "borderRadius": "10px",
                        "boxShadow": "0 1px 4px rgba(0,0,0,0.08)",
                        "padding": "4px",
                    },
                    children=[dcc.Graph(id="heatmap-graph", config={"displayModeBar": False})],
                ),

                # Data constraint note
                html.Div(
                    style={
                        "background": "#fffbea",
                        "border": "1px solid #f0c36d",
                        "borderRadius": "8px",
                        "padding": "12px 18px",
                        "fontSize": "12px",
                        "color": "#7a5a00",
                        "lineHeight": "1.6",
                    },
                    children=[
                        html.Strong("Data constraints: "),
                        "Observation counts reflect citizen-science detection effort, not true population abundance. "
                        "Grid cells with zero dots may indicate unsampled areas rather than species absence. "
                        "Dot size encodes aggregated count within each 0.25° grid cell — interpret spatial "
                        "clusters cautiously where sampling intensity is unknown.",
                    ],
                ),
            ],
        ),
    ],
)

# ---------------------------------------------------------------------------
# 4. CALLBACKS
# ---------------------------------------------------------------------------

@app.callback(
    Output("map-graph",   "figure"),
    Output("map-header",  "children"),
    Output("kpi-panel",   "children"),
    Output("trend-graph", "figure"),
    Output("bar-graph",   "figure"),
    Output("heatmap-graph", "figure"),
    Input("species-dropdown", "value"),
    Input("year-slider",      "value"),
)
def update_dashboard(selected_species, selected_year):
    """
    Master callback: filters data and rebuilds all six outputs simultaneously.
    """

    # ── Filter data ─────────────────────────────────────────────────────────
    filtered = RAW_DATA[
        (RAW_DATA["species"] == selected_species) &
        (RAW_DATA["year"] == selected_year)
    ]
    gridded = snap_to_grid(filtered)

    # ── 4a. MAP ─────────────────────────────────────────────────────────────
    grid_traces = build_grid_lines(
        DK_LAT_MIN, DK_LAT_MAX, DK_LON_MIN, DK_LON_MAX, GRID_RES
    )

    # Scale dot size logarithmically so sparse areas remain visible
    if not gridded.empty:
        sizes = 6 + 22 * (
            np.log1p(gridded["total_count"]) /
            np.log1p(gridded["total_count"].max())
        )
    else:
        sizes = []

    obs_trace = go.Scattermapbox(
        lat=gridded["grid_lat"],
        lon=gridded["grid_lon"],
        mode="markers",
        marker=dict(
            size=sizes,
            color=gridded["total_count"],
            colorscale="YlOrRd",
            cmin=0,
            cmax=gridded["total_count"].max() if not gridded.empty else 1,
            showscale=True,
            colorbar=dict(
                title=dict(text="Observations", side="right"),
                thickness=12,
                len=0.6,
                tickfont=dict(size=10),
            ),
            opacity=0.85,
        ),
        customdata=np.stack([gridded["total_count"], gridded["n_records"]], axis=-1)
        if not gridded.empty else [],
        hovertemplate=(
            "<b>Grid cell</b><br>"
            "Lat: %{lat:.2f}°, Lon: %{lon:.2f}°<br>"
            "Total observations: %{customdata[0]}<br>"
            "No. of records: %{customdata[1]}"
            "<extra></extra>"
        ),
        name="Observations",
        showlegend=False,
    )

    map_fig = go.Figure(data=grid_traces + [obs_trace])
    map_fig.update_layout(
        mapbox=dict(
            style=MAPBOX_STYLE,
            center=dict(lat=56.0, lon=10.5),
            zoom=5.6,
        ),
        margin=dict(l=0, r=0, t=8, b=0),
        paper_bgcolor="white",
    )

    map_header = f"Spatial Distribution — {selected_year}"

    # ── 4b. KPI CARDS ───────────────────────────────────────────────────────
    total_obs  = int(gridded["total_count"].sum()) if not gridded.empty else 0
    n_cells    = len(gridded)
    max_count  = int(gridded["total_count"].max()) if not gridded.empty else 0
    prev_year_df = RAW_DATA[
        (RAW_DATA["species"] == selected_species) &
        (RAW_DATA["year"] == selected_year - 1)
    ]
    prev_total = int(prev_year_df["count"].sum())
    delta = total_obs - prev_total
    delta_str = f"{'▲' if delta >= 0 else '▼'} {abs(delta):,} vs {selected_year-1}"
    delta_color = "#2e7d32" if delta >= 0 else "#c62828"

    def kpi_card(title, value, sub=None, sub_color="#666"):
        return html.Div(
            style={
                "background": "#fff",
                "border": "1px solid #e8e8e8",
                "borderRadius": "10px",
                "padding": "14px 16px",
                "boxShadow": "0 1px 3px rgba(0,0,0,0.06)",
            },
            children=[
                html.P(title, style={"fontSize": "11px", "color": "#888",
                                     "margin": "0 0 4px", "fontWeight": "600",
                                     "textTransform": "uppercase", "letterSpacing": "0.5px"}),
                html.P(value, style={"fontSize": "24px", "fontWeight": "700",
                                     "color": "#1b4332", "margin": "0"}),
                html.P(sub, style={"fontSize": "11px", "color": sub_color,
                                   "margin": "4px 0 0"}) if sub else None,
            ],
        )

    kpi_cards = [
        kpi_card("Total observations", f"{total_obs:,}", delta_str, delta_color),
        kpi_card("Grid cells occupied", f"{n_cells}",
                 f"of {int((DK_LAT_MAX-DK_LAT_MIN)*(DK_LON_MAX-DK_LON_MIN)/GRID_RES**2)} total"),
        kpi_card("Peak cell count", f"{max_count:,}", "in single 0.25° cell"),
    ]

    # ── 4c. TREND CHART ─────────────────────────────────────────────────────
    trend_df = YEARLY_TOTALS[YEARLY_TOTALS["species"] == selected_species]

    trend_fig = go.Figure()
    trend_fig.add_trace(go.Scatter(
        x=trend_df["year"], y=trend_df["total"],
        mode="lines+markers",
        line=dict(color="#2d6a4f", width=2.5),
        marker=dict(size=7, color="#52b788"),
        fill="tozeroy",
        fillcolor="rgba(82,183,136,0.12)",
        hovertemplate="<b>%{x}</b><br>%{y:,} observations<extra></extra>",
    ))
    # Highlight selected year
    sel_val = trend_df[trend_df["year"] == selected_year]["total"].values
    if len(sel_val):
        trend_fig.add_trace(go.Scatter(
            x=[selected_year], y=sel_val,
            mode="markers",
            marker=dict(size=12, color="#d62828", symbol="diamond"),
            hovertemplate=f"<b>Selected: {selected_year}</b><br>{int(sel_val[0]):,} obs<extra></extra>",
            showlegend=False,
        ))

    trend_fig.update_layout(
        title=dict(text=f"Annual observation trend — {selected_species.split('(')[0].strip()}",
                   font=dict(size=13), x=0.02),
        xaxis=dict(title="Year", tickmode="linear", dtick=2, showgrid=False),
        yaxis=dict(title="Total observations", showgrid=True,
                   gridcolor="rgba(0,0,0,0.05)"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=50, r=20, t=44, b=40),
        showlegend=False,
        height=280,
    )

    # ── 4d. HORIZONTAL BAR CHART ─────────────────────────────────────────────
    bar_year_df = (
        RAW_DATA[RAW_DATA["year"] == selected_year]
        .groupby("species")["count"]
        .sum()
        .reset_index()
        .sort_values("count")
    )
    bar_year_df["short"] = bar_year_df["species"].str.extract(r"^(.+?)\s*\(")

    bar_fig = go.Figure(go.Bar(
        x=bar_year_df["count"],
        y=bar_year_df["short"],
        orientation="h",
        marker=dict(
            color=[
                "#1b4332" if s == selected_species else "#95d5b2"
                for s in bar_year_df["species"]
            ],
            line=dict(width=0),
        ),
        hovertemplate="%{y}<br>%{x:,} observations<extra></extra>",
    ))
    bar_fig.update_layout(
        title=dict(text=f"All species observations in {selected_year}",
                   font=dict(size=13), x=0.02),
        xaxis=dict(title="Total observations", showgrid=True,
                   gridcolor="rgba(0,0,0,0.05)"),
        yaxis=dict(title="", showgrid=False),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=160, r=20, t=44, b=40),
        height=280,
    )

    # ── 4e. SIMULATED MONTHLY HEATMAP ────────────────────────────────────────
    # Simulate seasonal pattern (spring + autumn peaks typical for migrants)
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    seasonal_weights = np.array([0.3, 0.4, 0.8, 1.5, 2.0, 1.2,
                                  0.6, 0.5, 1.4, 1.8, 0.6, 0.3])
    base_per_month = total_obs / seasonal_weights.sum()
    monthly_counts = (base_per_month * seasonal_weights * np.random.uniform(0.8, 1.2, 12)).astype(int)

    heat_fig = go.Figure(go.Bar(
        x=months,
        y=monthly_counts,
        marker=dict(
            color=monthly_counts,
            colorscale="YlGn",
            showscale=False,
            line=dict(width=0),
        ),
        hovertemplate="%{x}: %{y:,} observations<extra></extra>",
    ))
    heat_fig.update_layout(
        title=dict(
            text=f"Estimated monthly distribution — {selected_species.split('(')[0].strip()}, {selected_year}",
            font=dict(size=13), x=0.02,
        ),
        xaxis=dict(title="Month", showgrid=False),
        yaxis=dict(title="Observation count", showgrid=True,
                   gridcolor="rgba(0,0,0,0.05)"),
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(l=50, r=20, t=44, b=40),
        height=220,
        bargap=0.15,
    )

    return map_fig, map_header, kpi_cards, trend_fig, bar_fig, heat_fig


# ---------------------------------------------------------------------------
# 5. ENTRY POINT
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
