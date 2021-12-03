import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import sqlite3

con = sqlite3.connect('pub_good_ztf_smallbodies.db')

# [('ztf',), ('orbdat',), ('desigs',), ('other_desig',)]
df = pd.read_sql("SELECT magpsf, sigmapsf FROM ztf", con)

fig = px.density_heatmap(df, x="magpsf", y="sigmapsf", nbinsx = 10, nbinsy = 10)
fig.update_layout(coloraxis_showscale=False)

fig.write_html("test.html")
        
app = dash.Dash(__name__)

colors = {
    'background': '#111111',
    'text': '#7FDBFF'
}

fig.update_layout(
    plot_bgcolor=colors['background'],
    paper_bgcolor=colors['background'],
    font_color=colors['text']
)

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

    dcc.Graph(
        id='example-graph',
        figure=fig
    )
])

if __name__ == '__main__':
    app.run_server(debug=True, port=8051)

app.run_server(debug=True)
