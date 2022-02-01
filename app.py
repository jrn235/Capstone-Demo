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

# sigmap and magpsf scatter
sigmapsfScatter = px.scatter(sigmapsfDF, x="magpsf", y="sigmapsf")
sigmapsfScatterFig = DynamicPlot(sigmapsfScatter)

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
updateLayout(sigmapsfScatter)

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
                    dbc.NavLink("Sigmapsf and Magpsf", href="/sigmapsf_magpsf", id="sigmap-link", active="exact",
                                style={"color": "#AFEEEE"})),
                dbc.NavItem(
                    dbc.NavLink("DistNR and MagNR", href="/distnr_magnr", id="distnr-link", active="exact",
                                style={"color": "#AFEEEE"})),
                dbc.NavItem(
                    dbc.NavLink("Sigmapsf and Magpsf Scatter", href="/scatter", id="scatter", active="exact",
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
    content,
    download_button
])


@app.callback(
    Output("download-dataframe-csv", "data"),
    Input("btn_csv", "n_clicks"),
    prevent_initial_call=True,
)
def exportButton(n_clicks):
    return dcc.send_data_frame(sigmapsfDF.to_csv, "sigmapsfDF.csv")


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
    elif pathname == "/scatter":
        return [
            html.H1(
                children="Sigmapsf and Magpsf Scatter",
                style={
                    "textAlign": "center",
                    'color': colors['text']
                }),
            dcc.Graph(
                id="sigmapsf_magpsf_scatter",
                figure=sigmapsfScatter
            )
        ]
    elif pathname == "/login":
        return [
            html.H1(
                children="Login Page",
                style = {
                    "textAlign": "center",
                    'color': colors['text']
                }),
            html.Div([
                dcc.Input(
                    placeholder='Username',
                    type='text',
                    value=''
                ),
                dcc.Input(
                    placeholder='Password',
                    type='Password',
                    value=''
                ),
                html.Button('Login', id='submit-val', n_clicks=0),
                
                html.P("Don't have an account?"),
                html.P("Sign up Below"),
                dcc.Input(
                    placeholder='Email',
                    type='email',
                    value=''
                ),
                dcc.Input(
                    placeholder='Username',
                    type='text',
                    value=''
                ),
                dcc.Input(
                    placeholder='Password',
                    type='Password',
                    value=''
                ),
                html.Button('Submit', id='submit-val', n_clicks=0),
            ],
            )
        ]
    elif pathname == "/login":
        return [
            html.H1(
                children="Login Page",
                style = {
                    "textAlign": "center",
                    'color': colors['text']
                }),
            html.Div([
                dcc.Input(
                    placeholder='Username',
                    type='text',
                    value=''
                ),
                dcc.Input(
                    placeholder='Password',
                    type='Password',
                    value=''
                ),
                html.Button('Login', id='submit-val', n_clicks=0),
                
                html.P("Don't have an account?"),
                html.P("Sign up Below"),
                dcc.Input(
                    placeholder='Email',
                    type='email',
                    value=''
                ),
                dcc.Input(
                    placeholder='Username',
                    type='text',
                    value=''
                ),
                dcc.Input(
                    placeholder='Password',
                    type='Password',
                    value=''
                ),
                html.Button('Submit', id='submit-val', n_clicks=0),
            ],
            )
        ]


app.callback(
    Output('sigmapsf_magpsf_scatter', "figure"),
    [Input('sigmapsf_magpsf_scatter', 'relayoutData')]
)(sigmapsfScatterFig.refine_plot)

if __name__ == '__main__':
    app.run_server(debug=False, port=8051)
