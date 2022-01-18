import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.express as px
import pandas as pd
import sqlite3

con = sqlite3.connect('pub_good_ztf_smallbodies.db')

# [('ztf',), ('orbdat',), ('desigs',), ('other_desig',)]
# magpsf and sigmapsf select through SQL
sigmapsfDF = pd.read_sql("SELECT magpsf, sigmapsf FROM ztf", con)
# distnr and magnr selected through SQL
distMagNRDF = pd.read_sql("SELECT distnr, magnr FROM ztf", con)

# sigmap and magpsf heatmap graph created
sigmapsfFig = px.density_heatmap(sigmapsfDF, x="magpsf", y="sigmapsf", nbinsx=10, nbinsy=10)
sigmapsfFig.update_layout(coloraxis_showscale=True)

# distnr and magnr heatmap graph created
distMagNRFig = px.density_heatmap(distMagNRDF, x="distnr", y="magnr", nbinsx=10, nbinsy=10)
distMagNRFig.update_layout(coloraxis_showscale=True)

sigmapsfFig.write_html("test.html")

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


updateLayout(sigmapsfFig)
updateLayout(distMagNRFig)

# Top nav bar styling
# TOP_NAVBAR_STYLING = {
#
# }

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
                    dbc.NavLink("Sigmapsf and Magpsf", href="/sigmapsf_magpsf", id="sigmap-link", active="exact",
                                style={"color": "#AFEEEE"})),
                dbc.NavItem(
                    dbc.NavLink("DistNR and MagNR", href="/distnr_magnr", id="distnr-link", active="exact",
                                style={"color": "#AFEEEE"})),
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
    content
])


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
    [Input("url", "pathname")]
)
def render_page_content(pathname):
    # if pathname is the main page show that main graph
    if pathname == "/":
        return [
            html.H1(
                children='First Light Dash Demo',
                style={
                    'textAlign': 'center',
                    'color': colors['text']
                }),
            html.Div(
                children='Testing the graphing of the ZTF slice database with Dash and Plotly.',
                style={
                    'textAlign': 'center',
                    'color': colors['text']
                }),

            dcc.Graph(
                id='example-graph',
                figure=sigmapsfFig
            )
        ]
    elif pathname == "/sigmapsf_magpsf":
        return [
            html.H1(
                children='Sigmapsf and Magpsf',
                style={
                    'textAlign': 'center',
                    'color': colors['text']
                }),
            dcc.Graph(
                id='sigmapsf-magpsf-graph',
                figure=sigmapsfFig
            )
        ]
    elif pathname == "/distnr_magnr":
        return [
            html.H1(
                children='DistNR and MagNR',
                style={
                    'textAlign': 'center',
                    'color': colors['text']
                }),
            dcc.Graph(
                id='distnr-magnr-graph',
                figure=distMagNRFig
            )
        ]


if __name__ == '__main__':
    app.run_server(debug=False, port=8051)
