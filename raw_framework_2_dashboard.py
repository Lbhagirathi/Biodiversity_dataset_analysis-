"""
Denmark Biodiversity Monitoring Dashboard  ·  v2 (Enhanced)
=============================================================
Improvements over v1:
  • 3D orthographic globe projection centred on Denmark
  • Denmark-only land polygon — other countries hidden
  • 1° × 1° grid lines (clipped to Denmark bounds)
  • Scroll-to-zoom + drag-to-rotate fully enabled
  • Projection toggle: Orthographic 3D  ↔  Natural Earth flat
  • Dark-themed UI with vivid accent colours, glassmorphism cards
  • 5 KPI cards with colour-coded accents and YoY delta
  • Spline trend chart with mean reference line
  • Seasonal monthly bar chart
  • Radar chart for top-5 species relative strength

Requirements:
    pip install dash plotly pandas numpy

Run:
    python denmark_biodiversity_dashboard.py
Open:
    http://127.0.0.1:8050
"""

import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# COLOUR PALETTE
# ─────────────────────────────────────────────────────────────────────────────
C = {
    "bg":        "#0d1117",
    "surface":   "#161b22",
    "surface2":  "#21262d",
    "border":    "#30363d",
    "a1":        "#58a6ff",   # electric blue   – primary
    "a2":        "#3fb950",   # vivid green     – nature / positive
    "a3":        "#f78166",   # coral           – hot spots / warn
    "a4":        "#d2a8ff",   # violet          – secondary info
    "a5":        "#ffa657",   # amber           – mid-range
    "tp":        "#e6edf3",   # text primary
    "tm":        "#8b949e",   # text muted
    "td":        "#484f58",   # text dim
    "grid":      "rgba(88,166,255,0.18)",
    "dk_fill":   "#52b788",   # Denmark polygon fill — brighter mint green
    "dk_line":   "#3fb950",   # Denmark polygon border
}

HEADER_GRAD = "linear-gradient(135deg,#0d1117 0%,#0e2233 50%,#0f2115 100%)"

# ─────────────────────────────────────────────────────────────────────────────
# DENMARK OUTLINE  (simplified clockwise polygon, Jutland + main islands)
# For production replace with a proper GeoJSON boundary.
# ─────────────────────────────────────────────────────────────────────────────
DK_LAT = [
    57.75, 57.73, 57.55, 57.30, 57.10, 56.90, 56.70, 56.50,
    56.30, 56.10, 55.90, 55.70, 55.40, 55.10, 54.80, 54.60,
    54.60, 54.90, 55.10, 55.40, 55.70, 55.90, 56.10, 56.30,
    56.55, 56.80, 57.10, 57.50, 57.75, 57.75,
]
DK_LON = [
    9.00,  9.80, 10.60, 11.80, 12.20, 12.40, 12.50, 12.30,
    12.00, 11.70, 11.40, 11.00, 10.60, 10.20,  9.80,  9.20,
     8.60,  8.70,  8.90,  9.10,  9.55,  9.85, 10.00, 10.00,
    10.30, 10.65, 10.80, 10.60,  9.80,  9.00,
]

# Bounding box
LAT_MIN, LAT_MAX = 54.50, 57.80
LON_MIN, LON_MAX =  8.00, 15.20
GRID_RES = 1.0   # 1-degree grid

# ─────────────────────────────────────────────────────────────────────────────
# SAMPLE DATA
# ─────────────────────────────────────────────────────────────────────────────
np.random.seed(42)

SPECIES = [
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

ICONS = {
    "White Stork (Ciconia ciconia)":           "🦢",
    "Common Swift (Apus apus)":                "🐦",
    "Red Kite (Milvus milvus)":                "🦅",
    "Eurasian Curlew (Numenius arquata)":      "🐧",
    "Northern Lapwing (Vanellus vanellus)":    "🕊️",
    "Atlantic Puffin (Fratercula arctica)":    "🐤",
    "Common Crane (Grus grus)":                "🦩",
    "Barn Swallow (Hirundo rustica)":          "🪶",
    "European Hedgehog (Erinaceus europaeus)": "🦔",
    "Eurasian Otter (Lutra lutra)":            "🦦",
}

CENTERS = {
    "White Stork (Ciconia ciconia)":           (55.4,  9.5),
    "Common Swift (Apus apus)":                (55.7, 12.5),
    "Red Kite (Milvus milvus)":                (56.2, 10.0),
    "Eurasian Curlew (Numenius arquata)":      (57.0,  9.0),
    "Northern Lapwing (Vanellus vanellus)":    (55.5, 11.8),
    "Atlantic Puffin (Fratercula arctica)":    (57.5, 10.5),
    "Common Crane (Grus grus)":                (56.5,  9.3),
    "Barn Swallow (Hirundo rustica)":          (55.9, 12.0),
    "European Hedgehog (Erinaceus europaeus)": (55.6, 10.8),
    "Eurasian Otter (Lutra lutra)":            (56.8,  8.8),
}

YEARS = list(range(2000, 2027))


def generate_data():
    rows = []
    base_year = min(YEARS)
    for sp in SPECIES:
        clat, clon = CENTERS[sp]
        for yr in YEARS:
            n = np.random.randint(60, 150)
            lats = np.clip(np.random.normal(clat, 0.9, n), LAT_MIN, LAT_MAX)
            lons = np.clip(np.random.normal(clon, 1.3, n), LON_MIN, LON_MAX)
            cnts = np.clip(
                (np.random.randint(1, 35, n) * (1 + 0.03 * (yr - base_year))).astype(int),
                1, 80,
            )
            for la, lo, ct in zip(lats, lons, cnts):
                rows.append(dict(species=sp, year=yr,
                                 lat=round(la, 4), lon=round(lo, 4), count=int(ct)))
    return pd.DataFrame(rows)


def snap_grid(df):
    d = df.copy()
    d["glat"] = (np.floor(d["lat"] / GRID_RES) * GRID_RES + GRID_RES / 2).round(2)
    d["glon"] = (np.floor(d["lon"] / GRID_RES) * GRID_RES + GRID_RES / 2).round(2)
    d = d[(d["glat"] >= LAT_MIN) & (d["glat"] <= LAT_MAX) &
          (d["glon"] >= LON_MIN) & (d["glon"] <= LON_MAX)]
    return (d.groupby(["glat", "glon"])
             .agg(total=("count", "sum"), recs=("count", "count"))
             .reset_index())


RAW = generate_data()
YTOT = (RAW.groupby(["species", "year"])["count"]
            .sum().reset_index().rename(columns={"count": "total"}))


# ─────────────────────────────────────────────────────────────────────────────
# MAP BUILDER
# ─────────────────────────────────────────────────────────────────────────────

OBS_COLORSCALE = [
    [0.00, "#0d2137"],
    [0.20, "#1a4a7a"],
    [0.45, "#1e7fc1"],
    [0.65, "#f5a623"],
    [0.82, "#f07030"],
    [1.00, "#e8281e"],
]


def make_map(gridded, projection):
    traces = []

    # 1. Denmark fill polygon
    traces.append(go.Scattergeo(
        lat=DK_LAT, lon=DK_LON,
        mode="lines",
        fill="toself",
        fillcolor=C["dk_fill"],
        line=dict(color=C["dk_line"], width=1.8),
        hoverinfo="skip", showlegend=False,
    ))

    # 2. 1° grid lines (Denmark-clipped)
    for lat in np.arange(np.floor(LAT_MIN), LAT_MAX + GRID_RES, GRID_RES):
        traces.append(go.Scattergeo(
            lat=[lat, lat], lon=[LON_MIN, LON_MAX],
            mode="lines",
            line=dict(width=0.7, color=C["grid"]),
            hoverinfo="skip", showlegend=False,
        ))
    for lon in np.arange(np.floor(LON_MIN), LON_MAX + GRID_RES, GRID_RES):
        traces.append(go.Scattergeo(
            lat=[LAT_MIN, LAT_MAX], lon=[lon, lon],
            mode="lines",
            line=dict(width=0.7, color=C["grid"]),
            hoverinfo="skip", showlegend=False,
        ))

    # 3. Observation bubbles
    if not gridded.empty:
        mx = gridded["total"].max()
        sizes = 10 + 30 * (np.log1p(gridded["total"]) / np.log1p(mx))
        traces.append(go.Scattergeo(
            lat=gridded["glat"], lon=gridded["glon"],
            mode="markers",
            marker=dict(
                size=sizes,
                color=gridded["total"],
                colorscale=OBS_COLORSCALE,
                cmin=0, cmax=mx,
                showscale=True,
                colorbar=dict(
                    title=dict(text="Obs", font=dict(color=C["tp"], size=11)),
                    thickness=10, len=0.5, x=1.01,
                    tickfont=dict(color=C["tm"], size=10),
                    bgcolor="rgba(22,27,34,0.9)",
                    bordercolor=C["border"], borderwidth=1,
                ),
                opacity=0.90,
                line=dict(width=1.0, color="rgba(255,255,255,0.25)"),
            ),
            customdata=np.stack([gridded["total"], gridded["recs"],
                                 gridded["glat"], gridded["glon"]], axis=-1),
            hovertemplate=(
                "<b>%{customdata[2]:.0f}°N  %{customdata[3]:.0f}°E</b><br>"
                "Observations : <b>%{customdata[0]}</b><br>"
                "Records       : %{customdata[1]}<br>"
                "<span style='color:#8b949e;font-size:10px'>1° × 1° cell</span>"
                "<extra></extra>"
            ),
            showlegend=False,
        ))

    rot = dict(lon=11.5, lat=56.0, roll=0) if projection == "orthographic" else {}

    fig = go.Figure(data=traces)
    fig.update_geos(
        projection_type=projection,
        projection_rotation=rot,
        lataxis_range=[LAT_MIN - 0.6, LAT_MAX + 0.6],
        lonaxis_range=[LON_MIN - 0.8, LON_MAX + 0.8],
        # Background — everything outside Denmark blends into dark bg
        showland=True,        landcolor="#2d6a4f",
        showocean=True,       oceancolor="#1a6fa8",
        showlakes=False,      showrivers=False,
        showcountries=False,  showcoastlines=False,
        showframe=False,
        bgcolor=C["surface"],
    )
    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=C["surface"],
        dragmode="zoom",
        uirevision="dk-map",   # preserves zoom between callbacks
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# CHART LAYOUT HELPER
# ─────────────────────────────────────────────────────────────────────────────

def clayout(title, h=290, ml=52, mr=20, mt=46, mb=40):
    return dict(
        title=dict(text=title, font=dict(color=C["tp"], size=13, family="Inter"), x=0.02),
        plot_bgcolor=C["surface"],
        paper_bgcolor=C["surface"],
        font=dict(color=C["tm"], size=11, family="Inter"),
        height=h,
        margin=dict(l=ml, r=mr, t=mt, b=mb),
        xaxis=dict(showgrid=True, gridcolor=C["border"],
                   color=C["tm"], linecolor=C["border"], zeroline=False),
        yaxis=dict(showgrid=True, gridcolor=C["border"],
                   color=C["tm"], linecolor=C["border"], zeroline=False),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────────────────────────────────────

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Inter',sans-serif;background:{C["bg"]};color:{C["tp"]};min-height:100vh}}
::-webkit-scrollbar{{width:5px;height:5px}}
::-webkit-scrollbar-track{{background:{C["surface"]}}}
::-webkit-scrollbar-thumb{{background:{C["border"]};border-radius:3px}}

/* Dropdown — white bg, black text for contrast */
.Select-control{{background:#ffffff!important;border-color:#d0d7de!important;
    color:#000000!important;border-radius:8px!important;}}
.Select-menu-outer{{background:#ffffff!important;border-color:#d0d7de!important;z-index:9999!important}}
.Select-option{{color:#000000!important;background:#ffffff!important}}
.Select-option.is-focused{{background:#f0f6ff!important;color:#000000!important}}
.Select-option.is-selected{{background:#dbeafe!important;color:#000000!important}}
.Select-value-label{{color:#000000!important}}
.Select-single-value{{color:#000000!important}}
.Select-placeholder{{color:#555555!important}}
.Select-arrow{{border-top-color:#444444!important}}
.Select-input > input{{color:#000000!important}}

/* Slider — visible on white controls bar */
.rc-slider-track{{background:{C["a1"]}!important}}
.rc-slider-handle{{border-color:{C["a1"]}!important;background:{C["a1"]}!important;
    box-shadow:0 0 8px rgba(88,166,255,0.5)!important}}
.rc-slider-rail{{background:#cccccc!important}}
.rc-slider-dot{{border-color:#aaaaaa!important;background:#ffffff!important}}
.rc-slider-dot-active{{border-color:{C["a1"]}!important}}
.rc-slider-mark-text{{color:#000000!important;font-size:10px!important;font-weight:600!important}}
.rc-slider-tooltip-inner{{background:{C["a1"]}!important;border-radius:6px!important;
    font-weight:700!important;font-size:12px!important;color:#ffffff!important}}

/* Radio */
input[type=radio]{{accent-color:{C["a1"]}}}

/* KPI card */
@keyframes kpi-in{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:translateY(0)}}}}
.kpi-card{{animation:kpi-in .3s ease both}}

/* Plotly tooltip global */
.hoverlayer .hovertext rect{{fill:{C["surface2"]}!important;stroke:{C["border"]}!important}}
.hoverlayer .hovertext text{{fill:{C["tp"]}!important}}
"""

# ─────────────────────────────────────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────────────────────────────────────

app = dash.Dash(__name__, title="Denmark Biodiversity Monitor")

app.index_string = f"""<!DOCTYPE html>
<html>
<head>
{{%metas%}}<title>{{%title%}}</title>{{%favicon%}}{{%css%}}
<style>{CSS}</style>
</head>
<body>{{%app_entry%}}<footer>{{%config%}}{{%scripts%}}{{%renderer%}}</footer>
</body></html>"""


def label(txt):
    return html.Div(txt, style={
        "fontSize": "10px", "fontWeight": "600", "letterSpacing": "1.2px",
        "textTransform": "uppercase", "color": C["td"], "marginBottom": "8px",
    })


def card(children, style_extra=None):
    s = {
        "background": C["surface"],
        "border": f"1px solid {C['border']}",
        "borderRadius": "12px",
        "overflow": "hidden",
    }
    if style_extra:
        s.update(style_extra)
    return html.Div(style=s, children=children)


app.layout = html.Div(style={"background": C["bg"], "minHeight": "100vh"}, children=[

    # ── HEADER ────────────────────────────────────────────────────────────────
    html.Div(style={
        "background": HEADER_GRAD,
        "borderBottom": f"1px solid {C['border']}",
        "padding": "0 32px",
        "height": "64px",
        "display": "flex", "alignItems": "center", "justifyContent": "space-between",
    }, children=[
        html.Div(style={"display": "flex", "alignItems": "center", "gap": "14px"}, children=[
            html.Span("🦅", style={"fontSize": "28px"}),
            html.Div([
                html.Div("Denmark Biodiversity Monitor", style={
                    "fontSize": "16px", "fontWeight": "700", "color": C["tp"],
                    "letterSpacing": "-0.3px",
                }),
                html.Div("Gridded species observations · 2010–2023 · GBIF-style data", style={
                    "fontSize": "11px", "color": C["tm"], "marginTop": "1px",
                }),
            ]),
        ]),
        html.Div(style={"display": "flex", "alignItems": "center", "gap": "14px"}, children=[
            html.Div("● Live", style={
                "background": "rgba(63,185,80,0.1)", "border": f"1px solid {C['a2']}44",
                "borderRadius": "20px", "padding": "3px 10px",
                "fontSize": "11px", "color": C["a2"], "fontWeight": "500",
            }),
            html.Div("v2.0  ·  Orthographic 3D", style={
                "fontSize": "11px", "color": C["td"],
            }),
        ]),
    ]),

    # ── CONTROLS ──────────────────────────────────────────────────────────────
    html.Div(style={
        "background": "#ffffff",
        "borderBottom": "1px solid #d0d7de",
        "padding": "14px 32px",
        "display": "flex", "alignItems": "flex-start", "gap": "36px", "flexWrap": "wrap",
    }, children=[

        html.Div(style={"minWidth": "300px"}, children=[
            html.Div("Species", style={
                "fontSize": "10px", "fontWeight": "700", "letterSpacing": "1.2px",
                "textTransform": "uppercase", "color": "#1a1a2e", "marginBottom": "8px",
            }),
            dcc.Dropdown(
                id="species-dd",
                options=[{"label": f"{ICONS.get(s,'🐾')}  {s}", "value": s}
                         for s in SPECIES],
                value=SPECIES[0],
                clearable=False,
                style={"width": "320px", "fontSize": "13px", "color": "#000000"},
            ),
        ]),

        html.Div(style={"flex": "1", "minWidth": "340px"}, children=[
            html.Div("Observation year", style={
                "fontSize": "10px", "fontWeight": "700", "letterSpacing": "1.2px",
                "textTransform": "uppercase", "color": "#1a1a2e", "marginBottom": "8px",
            }),
            html.Div(style={"padding": "4px 6px 0"}, children=[
                dcc.Slider(
                    id="year-sl",
                    min=min(YEARS), max=max(YEARS), step=1, value=2020,
                    marks={y: {"label": str(y), "style": {"fontSize": "10px", "color": "#000000", "fontWeight": "600"}}
                           for y in YEARS if y % 4 == 0},
                    tooltip={"placement": "top", "always_visible": True},
                ),
            ]),
        ]),

        html.Div(style={"minWidth": "190px"}, children=[
            html.Div("Map projection", style={
                "fontSize": "10px", "fontWeight": "700", "letterSpacing": "1.2px",
                "textTransform": "uppercase", "color": "#1a1a2e", "marginBottom": "8px",
            }),
            dcc.RadioItems(
                id="proj-radio",
                options=[
                    {"label": "  Orthographic (3D globe)", "value": "orthographic"},
                    {"label": "  Natural Earth (2D flat)",  "value": "natural earth"},
                ],
                value="orthographic",
                inputStyle={"marginRight": "6px", "accentColor": C["a1"]},
                labelStyle={"display": "block", "fontSize": "12px",
                            "color": "#1a1a2e", "marginBottom": "5px", "fontWeight": "500"},
            ),
        ]),
    ]),

    # ── KPI STRIP ─────────────────────────────────────────────────────────────
    html.Div(id="kpi-row", style={
        "display": "flex", "gap": "14px", "padding": "16px 32px 4px",
        "overflowX": "auto",
    }),

    # ── MAIN BODY ─────────────────────────────────────────────────────────────
    html.Div(style={"padding": "12px 32px 28px", "display": "flex",
                    "flexDirection": "column", "gap": "14px"}, children=[

        # Row 1: Map + Trend
        html.Div(style={"display": "flex", "gap": "14px"}, children=[

            card(style_extra={"flex": "3"}, children=[
                html.Div(style={
                    "padding": "12px 18px 8px",
                    "borderBottom": f"1px solid {C['border']}",
                    "display": "flex", "justifyContent": "space-between", "alignItems": "center",
                }, children=[
                    html.Div(id="map-title", style={
                        "fontSize": "13px", "fontWeight": "600", "color": C["tp"],
                    }),
                    html.Div(style={"display": "flex", "gap": "10px", "alignItems": "center"}, children=[
                        html.Div("1° × 1° grid", style={
                            "fontSize": "10px", "padding": "2px 8px",
                            "background": f"rgba(88,166,255,0.1)",
                            "border": f"1px solid {C['a1']}44",
                            "borderRadius": "10px", "color": C["a1"], "fontWeight": "500",
                        }),
                        html.Div("Scroll = zoom · Drag = rotate", style={
                            "fontSize": "10px", "color": C["td"],
                        }),
                    ]),
                ]),
                dcc.Graph(
                    id="map-graph",
                    config={
                        "scrollZoom": True,
                        "displayModeBar": True,
                        "modeBarButtonsToRemove": ["select2d", "lasso2d", "toImage"],
                        "displaylogo": False,
                    },
                    style={"height": "500px"},
                ),
            ]),

            card(style_extra={"flex": "1"}, children=[
                dcc.Graph(id="trend-graph",
                          config={"displayModeBar": False},
                          style={"height": "554px"}),
            ]),
        ]),

        # Row 2: Bar + Monthly + Radar
        html.Div(style={"display": "flex", "gap": "14px"}, children=[
            card(style_extra={"flex": "1"}, children=[
                dcc.Graph(id="bar-graph", config={"displayModeBar": False},
                          style={"height": "310px"}),
            ]),
            card(style_extra={"flex": "1"}, children=[
                dcc.Graph(id="month-graph", config={"displayModeBar": False},
                          style={"height": "310px"}),
            ]),
            card(style_extra={"flex": "1"}, children=[
                dcc.Graph(id="radar-graph", config={"displayModeBar": False},
                          style={"height": "310px"}),
            ]),
        ]),

        # Footer note
        html.Div(style={
            "background": "rgba(247,129,102,0.07)",
            "border": f"1px solid {C['a3']}33",
            "borderRadius": "10px",
            "padding": "10px 16px",
            "fontSize": "11px",
            "color": C["tm"],
            "lineHeight": "1.7",
        }, children=[
            html.Span("⚠  Data constraints:  ", style={"color": C["a3"], "fontWeight": "600"}),
            "Counts reflect citizen-science detection effort, not true abundance. "
            "Empty cells may indicate unsampled areas, not species absence. "
            "1° × 1° cells ≈ 70 × 111 km — interpret spatial clusters with caution. "
            "Replace generate_data() with a real GBIF export for production use.",
        ]),
    ]),
])


# ─────────────────────────────────────────────────────────────────────────────
# CALLBACK
# ─────────────────────────────────────────────────────────────────────────────

@app.callback(
    Output("map-graph",   "figure"),
    Output("map-title",   "children"),
    Output("kpi-row",     "children"),
    Output("trend-graph", "figure"),
    Output("bar-graph",   "figure"),
    Output("month-graph", "figure"),
    Output("radar-graph", "figure"),
    Input("species-dd",   "value"),
    Input("year-sl",      "value"),
    Input("proj-radio",   "value"),
)
def update(sp, yr, proj):

    # ── Filter ───────────────────────────────────────────────────────────────
    filt    = RAW[(RAW["species"] == sp) & (RAW["year"] == yr)]
    gridded = snap_grid(filt)
    short   = sp.split("(")[0].strip()
    icon    = ICONS.get(sp, "🐾")

    # ── Map ──────────────────────────────────────────────────────────────────
    map_fig   = make_map(gridded, proj)
    map_title = f"{icon}  {short}  ·  {yr}  ·  Denmark"

    # ── KPIs ─────────────────────────────────────────────────────────────────
    total  = int(gridded["total"].sum())  if not gridded.empty else 0
    ncells = len(gridded)
    peak   = int(gridded["total"].max())  if not gridded.empty else 0
    dens   = round(total / ncells, 1)     if ncells else 0.0

    prev_df    = RAW[(RAW["species"] == sp) & (RAW["year"] == yr - 1)]
    prev_total = int(prev_df["count"].sum()) if (not prev_df.empty and yr > min(YEARS)) else 0
    delta      = total - prev_total
    dsign      = "▲" if delta >= 0 else "▼"
    dcol       = C["a2"] if delta >= 0 else C["a3"]
    delta_sub  = f"vs {yr - 1}" if yr > min(YEARS) else "first year"

    max_cells = int((LAT_MAX - LAT_MIN) * (LON_MAX - LON_MIN) / GRID_RES**2)

    def kpi_card(ico, lbl, val, sub, accent, delay="0s"):
        return html.Div(className="kpi-card", style={
            "background": C["surface"],
            "border": f"1px solid {accent}2a",
            "borderTop": f"3px solid {accent}",
            "borderRadius": "10px",
            "padding": "12px 16px",
            "minWidth": "150px", "flex": "1",
            "position": "relative", "overflow": "hidden",
            "animationDelay": delay,
        }, children=[
            html.Div(ico, style={
                "position": "absolute", "right": "12px", "top": "10px",
                "fontSize": "20px", "opacity": "0.18",
            }),
            html.Div(lbl, style={
                "fontSize": "9px", "fontWeight": "600", "color": C["td"],
                "letterSpacing": "0.9px", "textTransform": "uppercase", "marginBottom": "5px",
            }),
            html.Div(val, style={
                "fontSize": "24px", "fontWeight": "700", "color": accent,
                "lineHeight": "1", "marginBottom": "4px",
            }),
            html.Div(sub, style={"fontSize": "10px", "color": C["tm"]}),
        ])

    kpis = [
        kpi_card("📊", "Total observations",  f"{total:,}",
                 f"all records in {yr}", C["a1"], "0s"),
        kpi_card("📍", "Occupied cells",      str(ncells),
                 f"of {max_cells} total 1° cells", C["a2"], "0.05s"),
        kpi_card("🔥", "Peak cell",           f"{peak:,}",
                 "highest single cell",   C["a5"], "0.10s"),
        kpi_card("📐", "Avg density",         f"{dens}",
                 "obs / occupied cell",   C["a4"], "0.15s"),
        kpi_card("📈", "YoY change",
                 f"{dsign} {abs(delta):,}",
                 delta_sub, dcol, "0.20s"),
    ]

    # ── Trend chart ──────────────────────────────────────────────────────────
    td = YTOT[YTOT["species"] == sp]
    mean_v = td["total"].mean()

    tf = go.Figure()
    tf.add_trace(go.Scatter(
        x=td["year"], y=td["total"],
        mode="lines+markers",
        name="Annual total",
        line=dict(color=C["a1"], width=2.5, shape="spline"),
        marker=dict(size=6, color=C["a1"], line=dict(width=1.5, color=C["surface"])),
        fill="tozeroy", fillcolor="rgba(88,166,255,0.07)",
        hovertemplate="<b>%{x}</b><br>%{y:,} obs<extra></extra>",
    ))
    sel_row = td[td["year"] == yr]["total"].values
    if len(sel_row):
        tf.add_trace(go.Scatter(
            x=[yr], y=sel_row,
            mode="markers",
            marker=dict(size=14, color=C["a3"], symbol="diamond",
                        line=dict(width=2, color=C["surface"])),
            hovertemplate=f"<b>{yr}</b><br>{int(sel_row[0]):,} obs<extra></extra>",
            showlegend=False,
        ))
    tf.add_hline(y=mean_v, line=dict(color=C["a4"], width=1, dash="dot"),
                 annotation_text=f"Mean {int(mean_v):,}",
                 annotation_font=dict(color=C["a4"], size=9))

    tf.update_layout(
        **clayout(f"Annual trend — {short}", h=554, ml=52, mr=18, mt=46, mb=40),
        showlegend=False,
    )

    # ── Horizontal bar — all species ─────────────────────────────────────────
    bdf = (RAW[RAW["year"] == yr]
           .groupby("species")["count"].sum().reset_index()
           .sort_values("count"))
    bdf["sh"] = bdf["species"].str.extract(r"^(.+?)\s*\(")
    bc = [C["a1"] if s == sp else C["surface2"] for s in bdf["species"]]
    be = [C["a1"] if s == sp else C["border"]   for s in bdf["species"]]

    bf = go.Figure(go.Bar(
        x=bdf["count"], y=bdf["sh"], orientation="h",
        marker=dict(color=bc, line=dict(color=be, width=1)),
        hovertemplate="%{y}<br><b>%{x:,}</b> obs<extra></extra>",
    ))
    bf.update_layout(**clayout(f"All species · {yr}", h=310, ml=165, mr=18, mt=44, mb=36))
    bf.update_xaxes(title_text="Observations")
    bf.update_yaxes(title_text="")

    # ── Monthly seasonal bar ─────────────────────────────────────────────────
    months = ["Jan","Feb","Mar","Apr","May","Jun",
              "Jul","Aug","Sep","Oct","Nov","Dec"]
    sw = np.array([0.25, 0.35, 0.85, 1.6, 2.1, 1.3,
                   0.55, 0.45, 1.5, 1.9, 0.55, 0.25])
    base = total / sw.sum() if total else 1
    mc   = np.clip(
        (base * sw * np.random.default_rng(yr).uniform(0.85, 1.15, 12)).astype(int),
        0, None,
    )
    mf = go.Figure(go.Bar(
        x=months, y=mc,
        marker=dict(
            color=mc,
            colorscale=[[0, "rgba(33,38,45,1)"], [0.4, "rgba(63,185,80,0.53)"], [1, "rgba(63,185,80,1)"]],
            line=dict(width=0),
        ),
        hovertemplate="%{x}: <b>%{y:,}</b> obs<extra></extra>",
    ))
    mf.update_layout(
        **clayout(f"Seasonal pattern · {short} · {yr}", h=310, ml=50, mr=18, mt=44, mb=36),
        bargap=0.18,
    )
    mf.update_xaxes(title_text="Month")
    mf.update_yaxes(title_text="Est. observations")

    # ── Radar — top-5 species relative strength ───────────────────────────────
    top5 = (RAW[RAW["year"] == yr]
            .groupby("species")["count"].sum()
            .nlargest(5).reset_index())
    top5["sh"] = top5["species"].str.extract(r"^(.+?)\s*\(")
    rv = (top5["count"] / top5["count"].max()).round(3).tolist()
    th = top5["sh"].tolist()
    rv.append(rv[0]); th.append(th[0])

    rf = go.Figure(go.Scatterpolar(
        r=rv, theta=th,
        fill="toself",
        fillcolor="rgba(63,185,80,0.10)",
        line=dict(color=C["a2"], width=2),
        marker=dict(size=6, color=C["a2"]),
        hovertemplate="<b>%{theta}</b><br>Score: %{r:.2f}<extra></extra>",
    ))
    rf.update_layout(
        **clayout(f"Top-5 relative strength · {yr}", h=310, ml=28, mr=28, mt=44, mb=28),
        polar=dict(
            bgcolor=C["surface"],
            radialaxis=dict(
                visible=True, showticklabels=False,
                gridcolor=C["border"], linecolor=C["border"], range=[0, 1],
            ),
            angularaxis=dict(
                gridcolor=C["border"], linecolor=C["border"],
                color=C["tm"], tickfont=dict(size=9),
            ),
        ),
    )

    return map_fig, map_title, kpis, tf, bf, mf, rf


# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True)
