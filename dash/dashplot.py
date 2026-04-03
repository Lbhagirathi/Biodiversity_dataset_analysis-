import dash_ag_grid as dag
from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go  
import wikipedia
import requests

app = Dash(__name__)

df_merged = pd.read_csv("./species_merged_final.csv")
plots = pd.read_csv("./plots.csv")

if "status" in df_merged.columns:
    df_merged["status"] = df_merged["status"].fillna("Common_Other")
else:
    df_merged["status"] = "Common_Other"

x_init = df_merged["species"]
y_init = df_merged["count"]

species_list = df_merged["species"].dropna().unique()
status_list = df_merged["status"].dropna().unique()
bar_graph = px.bar(x=x_init, y=y_init, labels={"x": "Species", "y": "Count"})

card_style = {
    "backgroundColor": "#ffffff",
    "padding": "20px",
    "borderRadius": "12px",
    "boxShadow": "0px 4px 12px rgba(0,0,0,0.1)",
    "margin": "10px"
}

def create_zoomable_image(img_url, title=""):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="markers", marker_opacity=0, hoverinfo="none"))
    
    fig.add_layout_image(
        dict(
            source=img_url,
            xref="x", yref="y",
            x=0, y=1, sizex=1, sizey=1,
            sizing="contain",
            layer="below"
        )
    )
    # Hide the axes but allow them to be zoomed/panned
    fig.update_xaxes(visible=False, range=[0, 1], fixedrange=False)
    fig.update_yaxes(visible=False, range=[0, 1], fixedrange=False, scaleanchor="x")
    
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=16)),
        margin=dict(l=0, r=0, t=40 if title else 0, b=0),
        plot_bgcolor="white",
        dragmode="pan", # Default to panning when clicked
        height=350 
    )
    
    return dcc.Graph(
        figure=fig, 
        config={'scrollZoom': True, 'displayModeBar': True, 'modeBarButtonsToRemove': ['lasso2d', 'select2d']},
        style={"width": "100%", "maxWidth": "400px", "margin": "auto"}
    )


app.layout = html.Div([
    html.H1("Bird Biodiversity Dashboard", style={
        "textAlign": "center",
        "marginBottom": "20px"
    }),

    html.Div([
        # Species Dropdown box
        html.Div(
            dcc.Dropdown(
                id="species-dropdown",
                options=[{"label": f"{row['common_name']} ({row['species']})"
                if pd.notna(row["common_name"]) and row["common_name"] != "Unknown"
                else row["species"],"value": row["species"]
                }
                for _, row in df_merged[["species", "common_name"]].drop_duplicates().iterrows()],
                placeholder="Select species...",
                searchable=True
            ),
            style={"width": "45%"}
        ),
        # Status Filter
        html.Div(
            dcc.Dropdown(
                id="status-filter",
                options=[{"label": "No filter", "value": "all"}] + [{"label": s, "value": s} for s in status_list],
                value="all", 
                clearable=False,
                placeholder="Filter by Status..."
            ),
            style={"width": "25%"}
        ),
        # Plot Type Filter
        html.Div(
            dcc.Dropdown(
                id="plot-type",
                options=[
                    {"label": "Hotspot", "value": "hotspot"},
                    {"label": "Temporal", "value": "sampling_effort"},
                    {"label": "Species Richness", "value": "species_richness"},
                ],
                value="hotspot",
                clearable=False
            ),
            style={"width": "25%"} 
        )
    ], style={
        **card_style, 
        "display": "flex", 
        "justifyContent": "space-between", 
        "width": "80%", 
        "margin": "10px auto"
    }),

    # Card with info and profile image
    html.Div([
        html.Div(
            html.Div(id="wiki-text"),
            style={**card_style, "width": "60%"}
        ),
        html.Div(
            html.Div(id="wiki-image"),
            style={**card_style, "width": "40%", "textAlign": "center"}
        )
    ], style={
        "display": "flex",
        "gap": "20px",
        "padding": "0 40px"
    }),

    html.Div(id="bottom-image-row", style={"padding": "0 30px"}),

    # Bar plpot
    html.Div(
        dcc.Graph(id="graph", figure=bar_graph),
        style={**card_style, "margin": "30px 40px"}
    )

], style={
    "backgroundColor": "#f5f7fa",
    "minHeight": "100vh",
    "padding": "20px"
})


# Fetching info from Wikipedia
def get_wiki_data(species):
    try:
        return wikipedia.summary(species, sentences=4, auto_suggest=True)
    except wikipedia.exceptions.DisambiguationError as e:
        try:
            return wikipedia.summary(e.options[0], sentences=4)
        except:
            return "Multiple matches found."
    except wikipedia.exceptions.PageError:
        results = wikipedia.search(species)
        if results:
            try:
                return wikipedia.summary(results[0], sentences=4)
            except:
                return "No Wikipedia summary found."
        return "No Wikipedia page found."
    except Exception as e:
        print("Wiki error:", e)
        return "Error fetching data."


# Collects image 
def get_bird_image(species):
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "format": "json",
            "titles": species,
            "prop": "pageimages",
            "pithumbsize": 500, 
            "redirects": 1       
        }
        headers = {"User-Agent": "BirdBiodiversityDashboard/1.0 (learning_dash@example.com)"}
        response = requests.get(url, params=params, headers=headers)

        if response.status_code != 200:
            return None

        data = response.json()
        pages = data.get("query", {}).get("pages", {})

        for page_id, page_data in pages.items():
            if "thumbnail" in page_data:
                return page_data["thumbnail"]["source"]
        return None
    except Exception as e:
        print("Image API error:", e)
        return None


@app.callback(
    Output("wiki-text", "children"),
    Output("wiki-image", "children"),
    Output("bottom-image-row", "children"), 
    Output("graph", "figure"),
    Output("species-dropdown", "options"), 
    Input("species-dropdown", "value"),
    Input("status-filter", "value"),
    Input("plot-type", "value")
)
def update(species, status, plot_type):
    # Filter the Data
    if status == "all" or status is None:
        filtered_df = df_merged
    else:
        filtered_df = df_merged[df_merged["status"] == status]

    x_filtered = filtered_df["species"]
    y_filtered = filtered_df["count"]
    filtered_unique = filtered_df[["species", "common_name"]].drop_duplicates()

    dropdown_options = [
        {
            "label": f"{row['common_name']} ({row['species']})"
            if pd.notna(row["common_name"]) and row["common_name"] != "Unknown"
            else row["species"],
            "value": row["species"]
        }
        for _, row in filtered_unique.iterrows()
    ]

    available_species = filtered_unique["species"].values

    # Rebuild the barplot with filter
    fig = px.bar(x=x_filtered, y=y_filtered, labels={"x": "Species", "y": "Count"})
    
    if species and species in x_filtered.values:
        colors = ["#EF553B" if s == species else "#636EFA" for s in x_filtered]
        fig.update_traces(marker_color=colors)
    else:
        fig.update_traces(marker_color="#636EFA")

    plot_rows = plots[plots["title"] == plot_type]
    if not plot_rows.empty:
        #zoomable plots
        interactive_images = [
            create_zoomable_image(row["url"], title="")
            for _, row in plot_rows.iterrows()
        ]
        
        global_plot_card = html.Div([
            html.H4(plot_type.replace("_", " ").title(), style={"textAlign": "center"}),
            html.Div(interactive_images,
                     style={
                         "display": "flex",
                         "flexWrap": "wrap",
                         "justifyContent": "center",
                         "width": "100%"})
        ],
        style={**card_style, "flex": "1", "display": "flex", "flexDirection": "column", "alignItems": "center"})
    else:
        global_plot_card = html.Div("No plot available", style={**card_style, "flex": "1", "textAlign": "center", "color": "gray"})

    # "No Species Selected"
    if species is None or species not in available_species:
        bottom_row = html.Div([global_plot_card], style={"display": "flex", "justifyContent": "center", "width": "100%"})
        return html.P("Select a species to view details.", style={"color": "gray"}), "", bottom_row, fig, dropdown_options

    # "Species Selected" 
    summary = get_wiki_data(species)
    image = get_bird_image(species)

    if image:
        # Kept the profile picture as a static image since it's just a thumbnail
        img_component = html.Img(
            src=image,
            style={"width": "250px", "borderRadius": "10px", "objectFit": "cover"}
        )
    else:
        img_component = html.P("No image available", style={"color": "gray"})

    row = df_merged[df_merged["species"] == species].iloc[0]
    image_url = row.get("url")

    if pd.notna(image_url):
        # Swap the static Cloudinary image for an interactive zoomable plot
        zoomable_cloud_map = create_zoomable_image(image_url, title="")
        
        cloud_img_card = html.Div([
            html.H4("Species distribution", style={"textAlign": "center"}),
            zoomable_cloud_map
        ], style={**card_style, "flex": "1", "display": "flex", "flexDirection": "column", "alignItems": "center"})
    else:
        cloud_img_card = html.Div([html.P("No image available", style={"color": "gray"})], style={**card_style, "flex": "1", "textAlign": "center"})

    # Put both cards side by side using Flexbox
    bottom_row = html.Div([cloud_img_card, global_plot_card], style={"display": "flex", "gap": "20px", "alignItems": "stretch", "width": "100%"})

    display_name = (
        f"{row['common_name']} ({species})"
        if pd.notna(row["common_name"]) and row["common_name"] != "Unknown"
        else species
    )

    text_component = html.Div([
        html.H3(display_name),
        html.P(summary, style={"lineHeight": "1.6"})
    ])

    return text_component, img_component, bottom_row, fig, dropdown_options

if __name__ == "__main__":
    app.run(debug=True)
