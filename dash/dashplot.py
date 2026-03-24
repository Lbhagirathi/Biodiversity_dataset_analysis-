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
    df_merged["status"] = df_merged["status"].fillna("common")
else:
    df_merged["status"] = "common"

counts = df_merged["species"].value_counts()
x = counts.index
y = counts.values

species_list = df_merged["species"].unique()
status_order = ["common", "migrating", "endangered", "exotic", "extinct"]

status_list = [s for s in status_order if s in df_merged["status"].unique()]
bar_graph = px.bar(x=x, y=y, labels={"x": "Species", "y": "Count"})

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
        dcc.Dropdown(
            id="status-filter",
            options=[{"label": "All", "value": "all"}] +
                    [{"label": s, "value": s} for s in status_list],
            value="all",
            placeholder="Filter by status"
        ),

        dcc.Dropdown(
            id="species-dropdown",
            options=[{"label": s, "value": s} for s in species_list],
            placeholder="Select species...",
            searchable=True
        )
    ], style={**card_style, "width": "60%", "margin": "10px auto"}),

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

        headers = {"User-Agent": "BirdDashboard/1.0"}

        response = requests.get(url, params=params, headers=headers)

        if response.status_code != 200:
            return None

        data = response.json()
        pages = data.get("query", {}).get("pages", {})

        for page in pages.values():
            if "thumbnail" in page:
                return page["thumbnail"]["source"]

        return None

    except Exception as e:
        print("Image error:", e)
        return None

@app.callback(
    Output("wiki-text", "children"),
    Output("wiki-image", "children"),
    Output("graph", "figure"),
    Input("species-dropdown", "value"),
    Input("status-filter", "value")
)
def update(species, status):
    if status == "all" or status is None:
        filtered = df_merged
    else:
        filtered = df_merged[df_merged["status"] == status]

    filtered_counts = filtered["species"].value_counts()
    x_filtered = filtered_counts.index
    y_filtered = filtered_counts.values

    fig = px.bar(x=x_filtered, y=y_filtered,
                 labels={"x": "Species", "y": "Count"})

    # Highlight selected species
    if species in x_filtered:
        colors = ["#EF553B" if s == species else "#636EFA" for s in x_filtered]
        fig.update_traces(marker_color=colors)

    if species is None:
        return "Select a species", "", fig

    summary = get_wiki_data(species)
    image = get_bird_image(species)

    img_component = html.Img(
        src=image if image else "https://via.placeholder.com/250",
        style={
            "width": "250px",
            "borderRadius": "10px"
        }
    )

    return html.Div([
        html.H3(species),
        html.P(summary, style={"lineHeight": "1.6"})
    ]), img_component, fig


if __name__ == "__main__":
    app.run(debug=True)
