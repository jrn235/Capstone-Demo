import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import sqlite3
from lenspy import DynamicPlot

con = sqlite3.connect('pub_good_ztf_smallbodies.db')
cursor = con.cursor()

entireDF = pd.read_sql("SELECT G, H, jd FROM ztf", con)

asteroidNames = pd.read_sql("SELECT id FROM ztf", con)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# db_dropdown = html.Div([
#     html.Div([
#         'XIndicator',
#         dcc.Dropdown(
#             id='ztf-xaxis-column',
#             options=[{'label': i, 'value': i} for i in entireDF.keys()],
#             value='x',
#             clearable=False,
#             placeholder="Select the x-axis"
#         ),
#         # dcc.RadioItems(
#         #     ['Linear', 'Log'], 'Linear',
#         #     id='xaxis-type',
#         #     inline=True,
#         # )
#     ], style={'width': '28%', 'display': 'inline-block'}),
#
#     html.Div([
#         'YIndicator',
#         dcc.Dropdown(
#             id='ztf-yaxis-column',
#             options=[{'label': i, 'value': i} for i in entireDF.keys()],
#             value='y',
#             clearable=False,
#             placeholder="Select the y-axis",
#         ),
#         # dcc.RadioItems(
#         #     ['Linear', 'Log'],
#         #     'Linear',
#         #     id='yaxis-type',
#         #     inline=True,
#         # )
#     ], style={'width': '28%', 'float': 'right', 'display': 'inline-block'})
# ])

app.layout = html.Div([
    html.Div([

        html.Div([
            dcc.Dropdown(
                entireDF.keys(),
                'G',
                id='xaxis-column'
            ),
            dcc.RadioItems(
                ['Linear', 'Log'],
                'Linear',
                id='xaxis-type',
                inline=True
            )
        ], style={'width': '25%', 'display': 'inline-block'}),

        html.Div([
            dcc.Dropdown(
                entireDF.keys(),
                'jd',
                id='yaxis-column'
            ),
            dcc.RadioItems(
                ['Linear', 'Log'],
                'Linear',
                id='yaxis-type',
                inline=True
            )
        ], style={'width': '25%', 'float': 'right', 'display': 'inline-block'})
    ]),

    dcc.Graph(id='indicator-graphic')
])

@app.callback(
    Output('indicator-graphic', 'figure'),
    Input('xaxis-column', 'value'),
    Input('yaxis-column', 'value'),
    Input('xaxis-type', 'value'),
    Input('yaxis-type', 'value')
)
def update_graph( xaxis_column_name, yaxis_column_name,
                  xaxis_type, yaxis_type):
    fig = px.scatter(x=entireDF['Value'])


if __name__ == '__main__':
    app.run_server(debug=False, port=8053)
