import dash_ag_grid as dag
from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import wikipedia
import requests

app = Dash()

df = pd.read_csv("./birds.csv").iloc[:, 1:]
df_species = pd.read_csv("./species_status.csv")

df_merged = df.merge(df_species, on="species", how="left")

if "status" in df_merged.columns:
    df_merged["status"] = df_merged["status"].fillna("Common_Other")
else:
    df_merged["status"] = "Common_Other"

counts = df_merged["species"].value_counts()
x_init = counts.index
y_init = counts.values

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

app.layout = html.Div([

    html.H1("Bird Biodiversity Dashboard", style={
        "textAlign": "center",
        "marginBottom": "20px"
    }),

    html.Div([
        html.Div(
            dcc.Dropdown(
                id="status-filter",
                options=[{"label": "All Statuses", "value": "all"}] + [{"label": s, "value": s} for s in status_list],
                value="all", 
                clearable=False,
                placeholder="Filter by Status..."
            ),
            style={"width": "30%"}
        ),
        
        # Species Dropdown box
        html.Div(
            dcc.Dropdown(
                id="species-dropdown",
                options=[{"label": s, "value": s} for s in species_list],
                placeholder="Select species...",
                searchable=True
            ),
            style={"width": "65%"}
        )
    ], style={
        **card_style, 
        "display": "flex", 
        "justifyContent": "space-between", 
        "width": "60%", 
        "margin": "10px auto"
    }),

    # Card with info and image
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

    # Graph 
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
    Output("graph", "figure"),
    Output("species-dropdown", "options"), 
    Input("species-dropdown", "value"),
    Input("status-filter", "value")
)
def update(species, status):
    if status == "all" or status is None:
        filtered_df = df_merged
    else:
        filtered_df = df_merged[df_merged["status"] == status]

    filtered_counts = filtered_df["species"].value_counts()
    x_filtered = filtered_counts.index
    y_filtered = filtered_counts.values
    

    available_species = filtered_df["species"].dropna().unique()
    dropdown_options = [{"label": s, "value": s} for s in available_species]

    # rebuilds graph with filtered data  only
    fig = px.bar(x=x_filtered, y=y_filtered, labels={"x": "Species", "y": "Count"})
    
    # Highlight selected species if it exists in the filtered graph
    if species and species in x_filtered:
        colors = ["#EF553B" if s == species else "#636EFA" for s in x_filtered]
        fig.update_traces(marker_color=colors)
    else:
        fig.update_traces(marker_color="#636EFA")
    # Fetch Wikipedia info only if a species is actually selected
    if species is None or species not in available_species:
        return html.P("Select a species to view details.", style={"color": "gray"}), "", fig, dropdown_options

    summary = get_wiki_data(species)
    image = get_bird_image(species)

    if image:
        img_component = html.Img(
            src=image,
            style={
                "width": "250px",
                "borderRadius": "10px",
                "objectFit": "cover"
            }
        )
    else:
        img_component = html.P("No image available", style={"color": "gray"})

    text_component = html.Div([
        html.H3(species),
        html.P(summary, style={"lineHeight": "1.6"})
    ])

    return text_component, img_component, fig, dropdown_options

if __name__ == "__main__":
    app.run(debug=True)
