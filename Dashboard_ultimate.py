import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import geopandas as gpd
import os
import base64

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────

grid_files = [
    rf"C:/Users/Sumit/OneDrive/Desktop/Project_dsp/output/grid_{i}.csv"
    for i in range(5)
]
birds_df = pd.concat(
    [pd.read_csv(f) for f in grid_files],
    ignore_index=True
)
species_df = pd.read_csv(r"C:/Users/Sumit/OneDrive/Desktop/Project_dsp/Graphs/unique_species.csv")

birds_df.columns = birds_df.columns.str.strip().str.lower()

# Fix column names from grid CSVs (species, lat_bin, lon_bin, year, individualCount)
birds_df.rename(columns={
    "lat_bin": "lat",
    "lon_bin": "lon",
    "individualcount": "count"
}, inplace=True)

# year is already an integer column in the grid CSVs — no date parsing needed

# Filter species
valid_species = set(species_df["species"].astype(str))
birds_df = birds_df[birds_df["species"].isin(valid_species)]

birds_df = birds_df.dropna(subset=["species", "year", "lat", "lon"])
birds_df["year"] = birds_df["year"].astype(int)

# Only data from 2000+
birds_df = birds_df[birds_df["year"] >= 2000]

RAW = birds_df[["species", "year", "lat", "lon", "count"]]

SPECIES = sorted(RAW["species"].unique())
YEARS = list(range(int(RAW["year"].min()), int(RAW["year"].max()) + 1))

# ─────────────────────────────────────────────
# GRID
# ─────────────────────────────────────────────

GRID_RES = 0.2

def snap_grid(df):
    d = df.copy()
    d["glat"] = (np.floor(d["lat"] / GRID_RES) * GRID_RES + GRID_RES/2)
    d["glon"] = (np.floor(d["lon"] / GRID_RES) * GRID_RES + GRID_RES/2)

    return d.groupby(["glat", "glon"]).agg(total=("count", "sum")).reset_index()

# ─────────────────────────────────────────────
# LOAD GADM
# ─────────────────────────────────────────────

gadm0 = gpd.read_file(r"C:/Users/Sumit/OneDrive/Desktop/Project_dsp/geopandas/gadm41_DNK_0.shp").to_crs(epsg=4326)
gadm1 = gpd.read_file(r"C:/Users/Sumit/OneDrive/Desktop/Project_dsp/geopandas/gadm41_DNK_1.shp").to_crs(epsg=4326)

def plot_geometry(fig, gdf, color, width, fill=False):
    for geom in gdf.geometry:
        if geom is None:
            continue

        if geom.geom_type == "Polygon":
            x, y = geom.exterior.xy
            fig.add_trace(go.Scattergeo(
                lon=list(x), lat=list(y),
                mode="lines",
                line=dict(color=color, width=width),
                fill="toself" if fill else None,
                fillcolor="rgba(0,150,0,0.25)" if fill else None,
                showlegend=False
            ))

        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                x, y = poly.exterior.xy
                fig.add_trace(go.Scattergeo(
                    lon=list(x), lat=list(y),
                    mode="lines",
                    line=dict(color=color, width=width),
                    fill="toself" if fill else None,
                    fillcolor="rgba(0,150,0,0.25)" if fill else None,
                    showlegend=False
                ))

# ─────────────────────────────────────────────
# MAP
# ─────────────────────────────────────────────

def make_map(gridded):
    fig = go.Figure()

    fig.update_geos(
        showland=True,
        landcolor="#e0e0e0",
        showocean=True,
        oceancolor="#e6f2ff",
        showcountries=True,
        countrycolor="gray",
        lataxis_range=[50, 65],
        lonaxis_range=[0, 25]
    )

    # Mask Denmark
    for geom in gadm0.geometry:
        if geom is None:
            continue

        if geom.geom_type == "Polygon":
            x, y = geom.exterior.xy
            fig.add_trace(go.Scattergeo(
                lon=list(x), lat=list(y),
                mode="lines",
                fill="toself",
                fillcolor="#e6f2ff",
                line=dict(width=0),
                showlegend=False
            ))

        elif geom.geom_type == "MultiPolygon":
            for poly in geom.geoms:
                x, y = poly.exterior.xy
                fig.add_trace(go.Scattergeo(
                    lon=list(x), lat=list(y),
                    mode="lines",
                    fill="toself",
                    fillcolor="#e6f2ff",
                    line=dict(width=0),
                    showlegend=False
                ))

    # Draw Denmark
    plot_geometry(fig, gadm0, "black", 2, fill=True)
    plot_geometry(fig, gadm1, "gray", 0.6, fill=False)

    # Data points
    if not gridded.empty:
        fig.add_trace(go.Scattergeo(
            lat=gridded["glat"],
            lon=gridded["glon"],
            mode="markers+text",
            text=gridded["total"],
            textposition="top center",
            marker=dict(
                size=8 + 20*(gridded["total"]/gridded["total"].max()),
                color=gridded["total"],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title="Observations")
            ),
            hovertemplate="Lat: %{lat:.2f}<br>Lon: %{lon:.2f}<br>Obs: %{text}<extra></extra>"
        ))

    return fig

# ─────────────────────────────────────────────
# METRICS
# ─────────────────────────────────────────────

YEAR_TOTAL = RAW.groupby("year")["count"].sum().reindex(YEARS, fill_value=0)
RICHNESS = RAW.groupby("year")["species"].nunique().reindex(YEARS, fill_value=0)

# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────

app = dash.Dash(__name__)

app.layout = html.Div([

    html.H2("Denmark Biodiversity Dashboard"),

    dcc.Tabs([

        # TAB 1
        dcc.Tab(label="📊 Dashboard", children=[

            dcc.Dropdown(
                id="species",
                options=[{"label": s, "value": s} for s in SPECIES],
                value=SPECIES[0]
            ),

            dcc.Slider(
                id="year",
                min=min(YEARS),
                max=max(YEARS),
                step=1,
                value=min(YEARS),
                marks={y: str(y) for y in YEARS}
            ),

            dcc.Graph(id="map", style={"height": "85vh"}),
            dcc.Graph(id="abundance"),
            dcc.Graph(id="richness"),
            dcc.Graph(id="species_trend")

        ]),
    
        # TAB 2
dcc.Tab(label="🖼️ Species Visualizations", children=[

    html.Div([

        html.H3("Species Visualization"),

        # Year selector (NEW)
        dcc.Dropdown(
            id="image-year",
            options=[{"label": y, "value": y} for y in YEARS],
            placeholder="Select a year"
        ),

        html.H4("Species Map"),
        html.Img(id="species-map", style={
            "width": "70%",
            "margin": "10px",
            "border": "2px solid gray"
        }),

        html.H4("Monthly-Yearly Map"),
        html.Img(id="monthly-map", style={
            "width": "70%",
            "margin": "10px",
            "border": "2px solid gray"
        }),

        html.H4("Yearly Distribution Map"),
        html.Img(id="yearly-map", style={
            "width": "70%",
            "margin": "10px",
            "border": "2px solid gray"
        }),

    ], style={"padding": "20px"})

])
])
])
# ─────────────────────────────────────────────
# CALLBACKS
# ─────────────────────────────────────────────

@app.callback(
    Output("map", "figure"),
    Output("abundance", "figure"),
    Output("richness", "figure"),
    Output("species_trend", "figure"),
    Input("species", "value"),
    Input("year", "value")
)
def update(sp, yr):

    df = RAW[(RAW["species"] == sp) & (RAW["year"] == yr)]
    gridded = snap_grid(df)

    map_fig = make_map(gridded)

    abundance_fig = go.Figure(go.Scatter(
        x=YEARS, y=YEAR_TOTAL.values,
        mode="lines+markers"
    )).update_layout(title="Total Observations")

    richness_fig = go.Figure(go.Scatter(
        x=YEARS, y=RICHNESS.values,
        mode="lines+markers"
    )).update_layout(title="Species Richness")

    sp_df = RAW[RAW["species"] == sp]
    sp_year = sp_df.groupby("year")["count"].sum().reindex(YEARS, fill_value=0)

    species_fig = go.Figure(go.Scatter(
        x=YEARS, y=sp_year.values,
        mode="lines+markers"
    )).update_layout(title=f"{sp} Trend")

    return map_fig, abundance_fig, richness_fig, species_fig


# IMAGE CALLBACK
@app.callback(
    Output("species-map", "src"),
    Output("monthly-map", "src"),
    Output("yearly-map", "src"),
    Input("species", "value"),
    Input("image-year", "value")
)
def update_images(species, year):

    if species is None:
        return "", "", ""

    import base64

    safe_name = species.replace(" ", "_")

    base_species_map = "C:/Users/Sumit/OneDrive/Desktop/Project_dsp/Graphs/species_maps"
    monthly_yearly_path = f"C:/Users/Sumit/OneDrive/Desktop/Project_dsp/Graphs/species_monthly_yearly/{safe_name}"
    yearly_map_path = f"C:/Users/Sumit/OneDrive/Desktop/Project_dsp/Graphs/species_yearly_maps/{safe_name}"

    def encode_image(path):
        if os.path.exists(path):
            ext = path.split(".")[-1]
            encoded = base64.b64encode(open(path, "rb").read()).decode()
            return f"data:image/{ext};base64,{encoded}"
        return ""

    # ── 1. Species base map ──
    species_img = ""

    for ext in ["png", "jpg", "jpeg", "PNG", "JPG", "JPEG"]:
        path1 = f"{base_species_map}/{safe_name}.{ext}"
        path2 = f"{base_species_map}/{species}.{ext}"

        if os.path.exists(path1):
            species_img = encode_image(path1)
            break
        elif os.path.exists(path2):
            species_img = encode_image(path2)
            break

    # ── 2. Year-based maps ──  ✅ OUTSIDE LOOP
    monthly_img = ""
    yearly_img = ""

    if year is not None:
        monthly_file = f"{monthly_yearly_path}/{year}.png"
        yearly_file = f"{yearly_map_path}/{year}.png"

        monthly_img = encode_image(monthly_file)
        yearly_img = encode_image(yearly_file)

    return species_img, monthly_img, yearly_img


if __name__ == "__main__":
    app.run(debug=True)