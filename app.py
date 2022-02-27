from click import style
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import sqlite3
from lenspy import DynamicPlot
# import json
# import time

con = sqlite3.connect('pub_good_ztf_smallbodies.db', check_same_thread=False)

entireDF = pd.read_sql("PRAGMA table_info('ztf');", con)
catagories = entireDF['name'].values.tolist()

# [('ztf',), ('orbdat',), ('desigs',), ('other_desig',)]
# magpsf and sigmapsf select through SQL
df = pd.DataFrame()

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# background color
colors = {
    'background': '#002D62',
    'text': '#FFFFFF'
}


def updateLayout(graphFig):
    return graphFig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )

# sidebar styling
SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '16rem',
    'padding': '2rem 1rem',
    'background-color': '#000173',
    'color': 'white'
}

# sidebar content styling
CONTENT_STYLE = {
    'margin-left': '18rem',
    'margin-right': '2rem',
    'padding': '2rem 1rem',
}

# Download Button
download_button = dbc.Row(
    [
        html.Button("Download CSV", id="btn_csv"),
        dcc.Download(id="download-dataframe-csv"),
    ],
    align="center",
)

# search bar creation
search_bar = dbc.Row(
    [
        dbc.Col(dbc.Input(type="search", placeholder="Search")),
        dbc.Col(
            dbc.Button(
                "Search", color="primary", className="ms-2", n_clicks=0
            ),
            width="auto",
        ),
    ],
    className="g-0 ms-auto flex-nowrap mt-3 mt-md-0",
    align="center",
)

# Top nav bar creation
topNavBar = dbc.Navbar(
    dbc.Container(
        [
            dbc.NavbarToggler(id="topNavBar-toggler", n_clicks=0),
            dbc.Collapse(
                search_bar,
                id="topNavBar-collapse",
                is_open=False,
                navbar=True,
            ),
            dbc.NavItem(dbc.NavLink("Login", href="/login", id="login-link", active="exact", style={"color": "#AFEEEE"})),
        ]
    ),
    color="dark",
    dark=True,
)

# sidebar creation
sidebar = html.Div(
    [
        html.H1("Graphs", className="display-4"),
        html.Hr(),
        html.P(
            "Asteroid comparison through different attributes", className="lead"
        ),
        dbc.Nav(
            [
                # background color of pills: #a0faff
                dbc.NavItem(dbc.NavLink("Home", href="/", id="home-link", active="exact", style={"color": "#AFEEEE"})),
                dbc.NavItem(
                    dbc.NavLink("Account", href="/", id="account-link", active="exact", style={"color": "#AFEEEE"})),
                dbc.NavItem(
                    dbc.DropdownMenu(label="Graphs", id="graph-link", style={"color": "#AFEEEE"}, nav=True,
                                     children=[dbc.DropdownMenuItem("Sigmapsf and Magpsf",
                                                                    href="/sigmapsf_magpsf"),
                                               dbc.DropdownMenuItem("DistNR and MagNR",
                                                                    href="/distnr_magnr"),
                                               dbc.DropdownMenuItem("Sigmapsf and Magpsf Scatter",
                                                                    href="/scatter"),
                                               ],
                                     )),
                dbc.NavItem(
                    dbc.NavLink("Documentation", href="/", id="document-link", active="exact",
                                style={"color": "#AFEEEE"})),
                dbc.NavItem(
                    dbc.NavLink("Links", href="/", id="links-link", active="exact", style={"color": "#AFEEEE"})),

            ],
            # makes the sidebar vertical instead of horizontal
            vertical=True,
            # gives the active link a blue highlight
            pills=True,
        ),
    ],
    style=SIDEBAR_STYLE,

)

content = html.Div(id="page-content", children=[], style=CONTENT_STYLE)

app.layout = html.Div([
    dcc.Location(id="url"),
    topNavBar,
    sidebar,
    content,
    download_button
])

@app.callback(
    Output('ztf-dropdown', 'options'),
    [Input('ztf-attribute-dropdown', 'value')]
)

@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    prevent_initial_call=True,
)
def exportButton(n_clicks):
    return dcc.send_data_frame(df.to_csv, "sigmapsfDF.csv")


# call back for top Navigation bar
@app.callback(
    Output("topNavBar-collapse", "is_open"),
    [Input("topNavBar-toggler", "n_clicks")],
    [State("topNavBar_collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname")
)
def render_page_content(pathname):
    # if pathname is the main page show that main graph
    if pathname == "/":
        return [
            html.Div([

            ])
        ]
    elif pathname == "/graph":
        return [
            html.Div([
                dcc.Dropdown(
                    options = [{'label': i, 'value': i } for i in entireDF["name"]],
                    value = 'sigmapsf', 
                    id = 'xaxis-column'),
                dcc.RadioItems(
                    options = [
                        {'label': 'Linear', 'value': 'Linear'},
                        {'label': 'Log', 'value': 'Log'}],
                    value = "Linear",
                    id = 'xaxis-type'
                )], style = {'width': '48%', 'display': 'inline-block'}
            ),
            html.Div([
                dcc.Dropdown(
                    options = [{'label': i, 'value': i } for i in entireDF["name"]], 
                    value = 'magpsf', 
                    id = 'yaxis-column'),
                dcc.RadioItems(
                    options = [
                        {'label': 'Linear', 'value': 'Linear'},
                        {'label': 'Log', 'value': 'Log'}],
                    value = "Linear",
                    id = 'yaxis-type'
                )], style = {'width': '48%', 'float': 'right', 'display': 'inline-block'}
            ),
            dcc.Graph(id = "heatmap"),
            html.Div(
                html.Pre(id = 'click-data')
            )
        ]

    elif pathname == "/scatter":
        return [
            html.Div([
                dcc.Dropdown(
                    options = [{'label': i, 'value': i } for i in entireDF["name"]],
                    value = 'sigmapsf', 
                    id = 'xaxis-column'),
                dcc.RadioItems(
                    options = [
                        {'label': 'Linear', 'value': 'Linear'},
                        {'label': 'Log', 'value': 'Log'}],
                    value = "Linear",
                    id = 'xaxis-type'
                )], style = {'width': '48%', 'display': 'inline-block'}
            ),
            html.Div([
                dcc.Dropdown(
                    options = [{'label': i, 'value': i } for i in entireDF["name"]], 
                    value = 'magpsf', 
                    id = 'yaxis-column'),
                dcc.RadioItems(
                    options = [
                        {'label': 'Linear', 'value': 'Linear'},
                        {'label': 'Log', 'value': 'Log'}],
                    value = "Linear",
                    id = 'yaxis-type'
                )], style = {'width': '48%', 'float': 'right', 'display': 'inline-block'}
            ),
            dcc.Graph(id = "scatter"),
            html.Div(
                html.Pre(id = 'click-data')
            )
        ]

    elif pathname == '/asteroid/*':
        return [
            html.Div([
                html.H1(f"Asteroid")
            ])
        ]


@app.callback(
    Output('click-data', 'children'),
    Input('scatter', 'clickData')
)
def click_scatter(clickData):
    if(type(clickData) != None):
        click_data = clickData['points'][0]['hovertext']
        goto = dcc.Link(html.A(f'Go to {click_data}'), href = f'/asteroid/{click_data}')
        return goto

@app.callback(
    Output('heatmap', 'figure'),
    Input('xaxis-column', 'value'),
    Input('yaxis-column', 'value'))
def update_heatmap(xaxis_column_name, yaxis_column_name):
    df = pd.read_sql(f"SELECT {xaxis_column_name}, {yaxis_column_name} FROM ztf", con)
    fig = px.density_heatmap(df, x = xaxis_column_name, y = yaxis_column_name,
                            nbinsx = 25, nbinsy = 25, text_auto = True)
    
    fig.update_xaxes(title=xaxis_column_name)
    fig.update_yaxes(title=yaxis_column_name)

    updateLayout(fig)
    return fig

@app.callback(
    Output('scatter', 'figure'),
    Input('xaxis-column', 'value'),
    Input('yaxis-column', 'value'))
def update_scatter(xaxis_column_name, yaxis_column_name):
    df = pd.read_sql(f"SELECT {xaxis_column_name}, {yaxis_column_name}, ssnamenr FROM ztf", con)

    fig = px.scatter(df, x = xaxis_column_name, y = yaxis_column_name,
                        hover_name = 'ssnamenr')

    fig.update_xaxes(title=xaxis_column_name)
    fig.update_yaxes(title=yaxis_column_name)
    plot = DynamicPlot(fig, max_points=1000)

    updateLayout(fig)
    return plot.fig

if __name__ == '__main__':
    app.run_server(debug=False, port=8051)