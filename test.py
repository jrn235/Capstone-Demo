import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import plotly.express as px

con = sqlite3.connect('pub_good_ztf_smallbodies.db')

df = pd.read_sql("SELECT magpsf, sigmapsf FROM ztf", con)

plt.hist2d(df.magpsf, df.sigmapsf, cmin=1)
plt.xlabel("magpsf")
plt.ylabel("sigmapsf")
plt.title("Test")
plt.colorbar(norm=mcolors.NoNorm)
plt.savefig("assets/test.png")

app = dash.Dash(__name__)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

app.layout = html.Div(style={'backgroundColor': colors['background']}, children=[
    html.H1(
        children='First Light Dash Demo',
        style = {
            'textAlign': 'center',
            'color': colors['text']
        }),

    html.Div(
        children='Testing the graphing of the ZTF slice database with Dash and Plotly.',
        style = {
            'textAlign': 'center',
            'color': colors['text']
        }),

    html.Img(src=app.get_asset_url("test.png"))
])

if __name__ == '__main__':
    app.run_server(debug=True)

app.run_server(debug=True)

