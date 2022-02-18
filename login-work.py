# Dashboard / Graphing Dependencies
import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash import callback_context
import plotly.express as px
import pandas as pd
import sqlite3
from lenspy import DynamicPlot

# Login Dependencies

# Manage database and users
from sqlalchemy import Table, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import select
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, current_user, LoginManager, UserMixin

# Manage password hashing
from werkzeug.security import generate_password_hash, check_password_hash

# Use to config server
import warnings
import configparser
import os

# Use for email check
import re

warnings.filterwarnings("ignore")

# CSS
# background color
colors = {
    'background': '#002D62',
    'text': '#FFFFFF'
}
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

# Create the dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], prevent_initial_callbacks=True)
server = app.server
app.config.suppress_callback_exceptions = True

con = sqlite3.connect('pub_good_ztf_smallbodies.db')
cursor = con.cursor()

# Login functionality
user_con = sqlite3.connect('data.sqlite')
engine = create_engine('sqlite:///data.sqlite')
db = SQLAlchemy()
config = configparser.ConfigParser()

# Create users class for interacting with users table
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True, nullable=False)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

Users_tbl = Table('users', Users.metadata)

# Fuction to create table using Users class
def create_users_table():
    Users.metadata.create_all(engine)

# Create the table
create_users_table()

# Config the server to interact with the database
# Secret Key is used for user sessions
server.config.update(
    SECRET_KEY=os.urandom(12),
    SQLALCHEMY_DATABASE_URI='sqlite:///data.sqlite',
    SQLALCHEMY_TRACK_MODIFICATIONS=False
)
db.init_app(server)

login_manager = LoginManager()

# This provides default implementations for the methods that Flask-#Login expects user objects to have
login_manager.init_app(server)
login_manager.login_view = '/login'

class Users(UserMixin, Users):
    pass

# Callback to reload the user object
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Create graphs
entireDF = pd.read_sql("PRAGMA table_info('ztf');", con)
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

# Update the graphs
def updateLayout(graphFig):
    return graphFig.update_layout(
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text']
    )
updateLayout(sigmapsfFig)
updateLayout(distMagNRFig)
updateLayout(sigmapsfScatter)

# Attribute dropdowns
db_dropdown = html.Div([
    dcc.Dropdown(
        id='ztf-attribute-dropdown',
        options=[{'label': i, 'value': i } for i in entireDF["name"]],
        value='x',
        clearable=False,
        placeholder="Select an Attribute",
        style={'float': 'right', 'width': '50%'}
    ),

    dcc.Dropdown(
        id='ztf-dropdown',
        options=[{'label': i, 'value': i } for i in entireDF["name"]],
        value='y',
        clearable=False,
        placeholder="Select an Attribute",
        style={'float': 'right', 'width': '50%'}
    ),

    html.Div(id='display selected-values')
])

# Download Button
download_button = dbc.Row(
    [
        html.Button("Download CSV", id="btn_csv"),
        dcc.Download(id="download-dataframe-csv"),
    ],
    align="center",
)

# Search bar creation
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
            dbc.NavItem(dbc.NavLink("Sign Up", href="/signup", id="signup-link", active="exact", style={"color": "#AFEEEE"}))
        ]
    ),
    color="dark",
    dark=True,
)

# Sidebar creation
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
                dbc.NavItem(dbc.NavLink("Home", href="/home", id="home-link", active="exact", style={"color": "#AFEEEE"})),
                dbc.NavItem(
                    dbc.NavLink("My Account", href="/account", id="account-link", active="exact", style={"color": "#AFEEEE"})),
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
            pills=False,
        ),
    ],
    style=SIDEBAR_STYLE,

)

# Sign up page
create = html.Div([
            html.H1('Create User Account:'),
            dcc.Location(id='creation', refresh=True),
            dcc.Input(id="username", type="text", placeholder="user name", maxLength=15),
            dcc.Input(id="password", type="password", placeholder="password"),
            dcc.Input(id="confirmpassword", type="password", placeholder="confirm password"),
            dcc.Input(id="email", type="email", placeholder="email", maxLength=50),
            html.Button('Sign Up', id='signup_button', n_clicks=0),
            html.Div(id='create_user', children=[])
        ])  # end div

# Login page
login = html.Div([
            dcc.Location(id='url_login', refresh=True),
            html.H2('''Please log in to continue:''', id='h1'),

            dcc.Input(placeholder='Enter your username', type='text', id='uname-box'),
            dcc.Input(placeholder='Enter your password', type='password', id='pwd-box'),
            dcc.Input(placeholder='Confirm your password', type='password', id='con-pwd-box'),

            html.Button(children='Login', n_clicks=0, type='submit', id='login-button'),
            html.Div(id='login_output', children=[], style={})
        ])  # end div

# Account page
account = html.Div([
            dcc.Location(id='user_account', refresh=True),
            html.Div(id='account_output', children=[], style={}),  # end div
            html.Div([
                html.Br(),
                html.Button(id='back-button', children='Go back', n_clicks=0)
                ]),  # end div
            html.Br(), html.Br(),
            html.Button('Logout', id='logout_button', n_clicks=0),
            html.Div(id='url_logout', children=[]) # end div
        ])  # end div

content = html.Div(id="page-content", children=[], style=CONTENT_STYLE)

app.layout = html.Div([
    dcc.Location(id="url"),
    topNavBar,
    sidebar,
    db_dropdown,
    content,
    download_button
])


@app.callback(
    Output('ztf-dropdown', 'options'),
    [Input('ztf-attribute-dropdown', 'value')]
)
def set_attribute_options(selected_attribute):
    if type(selected_attribute) == 'str':
        return [{'label': i, 'value': i} for i in entireDF["name"]]
    else:
        return [{'label': i, 'value': i} for attribute in selected_attribute for i in entireDF["name"]]


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
    if pathname == "/home" or pathname == '/':
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
        if current_user.is_authenticated:
            return [account]
        else:
            return [login]

    elif pathname == "/signup":
        return [create]

    elif pathname == "/account":
        if current_user.is_authenticated:
            return [account]
        else:
            return [login]
    else:
        return [html.H1("Sorry, that page could not be found. Error: 404")]


@app.callback(
    [Output('create_user', "children")],
    [Input('signup_button', 'n_clicks')],
    [State('username', 'value'), State('password', 'value'), State('confirmpassword', 'value'), State('email', 'value')])
def insert_users(n_clicks, un, pw, cpw, em):
    # Hash the password
    hashed_password = generate_password_hash(pw, method='sha256')

    # Valid Email constraints
    regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # Check if all the fields are not empty
    if un is not None and pw is not None and cpw is not None and em is not None:

        # Checks if no errors occur
        try:

            # Check if the password and confirm password values are the same
            if cpw == pw:

            	# Check if the email is valid
                if re.fullmatch(regex, em):

                	# Create a new user object for the database
                	ins = Users_tbl.insert().values(username=un,  password=hashed_password, email=em)

                	# Connect to the database
                	user_con = engine.connect()

                	# Insert the new user into the database
                	user_con.execute(ins)

                	# Close the connection to the database
               		user_con.close()

                	# Return to the home page
                	return [html.Div([html.H2('Account Successfully Created')])]
                else:

                	# Email is not valid
                	return [html.Div([html.H2('This email is not valid')])]

            # If the passwords do not match
            else:

               	# Print the error
                return [html.Div([html.H2('Passwords do not match')])]

        # Which error occured?
        except SQLAlchemyError as e:

            # To see error
            error = str(e.__dict__['orig'])

            # Username already in use
            if error == 'UNIQUE constraint failed: users.username':

                # Print the error
                return [html.Div([html.H2('This username is already taken')])]

            # Email already used
            elif error == 'UNIQUE constraint failed: users.email':

                return [html.Div([html.H2('There is already an account associated with this email')])]

    # If one or more of the fields are empty
    else:
        # Print the error
        return [html.Div([html.H2('A field is empty')])]

# Callback for logging in
@app.callback(
    Output('login_output', 'children'), [Input('login-button', 'n_clicks')],
    [State('uname-box', 'value'), State('pwd-box', 'value'), State('con-pwd-box', 'value')])
def login_to_account(n_clicks, input1, input2, input3):
    if n_clicks > 0:
        # Gets the username data from the database
        user = Users.query.filter_by(username=input1).first()

        # If the user exists
        if user:
            # Check the passwords to see if they match the recorded password in the database
            if check_password_hash(user.password, input2) and check_password_hash(user.password, input3):
                login_user(user)
                # All is good, continue
                return dcc.Location(pathname="/home", id="home-link")
            # If one, or both, password(s) do not match
            else:
                # Print the error
                return [html.Div([html.H2('Incorrect Password')])]

        # If the username does not exist
        else:
            # Print the Error
            return [html.Div([html.H2('Incorrect Username')])]

# Callback for account page
@app.callback(
    Output('account_output', 'pathname'),
    [Input('account_button', 'n_clicks')])
def display_account():
    if n_clicks > 0:
        return '/account'

# Callback for logout
@app.callback(
    Output('url_logout', 'children'), [Input('logout_button', 'n_clicks')])
def logout_of_account(n_clicks):
    if n_clicks > 0:
        logout_user()
        return [html.H1("You've been logged out")]

app.callback(
    Output('sigmapsf_magpsf_scatter', "figure"),
    [Input('sigmapsf_magpsf_scatter', 'relayoutData')]
)(sigmapsfScatterFig.refine_plot)


if __name__ == '__main__':
    app.run_server(debug=False, port=8051)
