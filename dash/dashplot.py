import dash_ag_grid as dag
from dash import Dash, dcc, html   
import pandas as pd
import plotly.express as px

app = Dash()

df = pd.read_csv("./birds.csv").iloc[:,1:]

birds = {}
for species in df["species"]:
    if species not in birds:
        birds[species] = 1
    else:
        birds[species] += 1

x = list(birds.keys())
y = list(birds.values())

app.layout = html.Div([dcc.Graph(figure=px.bar(x=x, y=y,labels={"x": "Species","y":"Count"} ))])

app.run(debug=True)
