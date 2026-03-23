import dash_ag_grid as dag
from dash import Dash, dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import wikipedia
import requests

app = Dash()
df = pd.read_csv("./birds.csv").iloc[:, 1:]

counts = df["species"].value_counts()
x = counts.index
y = counts.values

species_list = df["species"].unique()

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

    html.Div(
        dcc.Dropdown(
            id="species-dropdown",
            options=[{"label": s, "value": s} for s in species_list],
            placeholder="Search species...",
            searchable=True
        ),
        style={
            **card_style,
            "width": "50%",
            "margin": "20px auto"
        }
    ),

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
        # to access images from wikipedia 
        headers = {"User-Agent": "BirdBiodiversityDashboard/1.0 (learning_dash@example.com)"}
        response = requests.get(url, params=params, headers=headers)

        # Safety check: Only try to parse JSON if the server said "200 OK"
        if response.status_code != 200:
            print(f"Server blocked request. Status: {response.status_code}")
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
    Input("species-dropdown", "value")
)
def update(species):
    if species is None:
        return "Select a species", "", bar_graph

    summary = get_wiki_data(species)
    image = get_bird_image(species)

    img_component = html.Img(
        src=image,
        style={
            "width": "250px",
            "borderRadius": "10px"
        }
    )

    # Highlight selected species
    colors = ["#636EFA" if s != species else "#EF553B" for s in x]

    fig = px.bar(x=x, y=y, labels={"x": "Species", "y": "Count"})
    fig.update_traces(marker_color=colors)

    return html.Div([
        html.H3(species),
        html.P(summary, style={"lineHeight": "1.6"})
        ]), img_component, fig


if __name__ == "__main__":
    app.run(debug=True)
