####################################################################################################################################################
#	Python Library Dependencies
####################################################################################################################################################

from types import NoneType
import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.express as px
import pandas as pd
import pymongo
import sqlite3
from lenspy import DynamicPlot

# Login Dependencies
# Manage database and users
from sqlalchemy import Table, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import select
from sqlalchemy.orm import Session
from flask_sqlalchemy import SQLAlchemy
from flask_login import login_user, logout_user, current_user, LoginManager, UserMixin
from flask import session

# Manage password hashing
from werkzeug.security import generate_password_hash, check_password_hash

# Use to config server
import warnings
import configparser
import os
# Use for email check
import re

# For diplaying the data
import numpy as np
import json
from dash import dash_table as dt

# For displaying the png's
import base64

# For the MongoDB connection
from constring import *



####################################################################################################################################################
#	Dash App Configuration
####################################################################################################################################################



#app = dash.Dash(__name__, requests_pathname_prefix='/snaps/', external_stylesheets=[dbc.themes.FLATLY])
# Create Dash instance
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], title='SNAPS')

# Create server instance
server = app.server

# Prevents initial errors for no callback input
app.config.suppress_callback_exceptions = True


# Connect to the MongoDB
client = pymongo.MongoClient(con_string)

# Create variable for easy access to the ZTF table
ztf = client.ztf.ztf

# Create variable for easy access to the Asteroids table
derived = client.ztf.asteroids

# Never print duplicate warnings
warnings.filterwarnings("ignore")

# Create and connect to the userData SQLite database file
user_data_con = sqlite3.connect('userData.sqlite')
user_data_engine = create_engine('sqlite:///userData.sqlite')
user_data_db = SQLAlchemy()

# Create the UserData Class for use in SQLAlchemy
class UserData(user_data_db.Model):
	id = user_data_db.Column(user_data_db.Integer, primary_key=True)
	username = user_data_db.Column(user_data_db.String(15), unique=False, nullable=False)
	asteroid_id = user_data_db.Column(user_data_db.String(50), unique=False)
UserData_tbl = Table('user_data', UserData.metadata)

# Create the user_data table within the SQLite database
def create_userData_table():
	UserData.metadata.create_all(user_data_engine)
create_userData_table()

# Create and connect to the users SQLite database file
users_con = sqlite3.connect('users.sqlite')
users_engine = create_engine('sqlite:///users.sqlite')
users_db = SQLAlchemy()

# Create a configuration objct for SQLite and SQLAlchemy interaction
config = configparser.ConfigParser()

# Create Users Class for interacting with users table
class Users(users_db.Model):
	id = users_db.Column(users_db.Integer, primary_key=True)
	username = users_db.Column(users_db.String(15), unique=True, nullable=False)
	email = users_db.Column(users_db.String(50), unique=True)
	password = users_db.Column(users_db.String(80))
Users_tbl = Table('users', Users.metadata)

# Create users table within SQLite database
def create_users_table():
	Users.metadata.create_all(users_engine)
create_users_table()

# Config the server to interact with the database
# Secret Key is used for user sessions
server.config.update(
	SECRET_KEY=os.urandom(12),
	SQLALCHEMY_DATABASE_URI='sqlite:///users.sqlite',
	SQLALCHEMY_TRACK_MODIFICATIONS=False
)

# Initialize users database server
users_db.init_app(server)

# Create login instance from Flask
login_manager = LoginManager()

# This provides default implementations for the methods that Flask-Login expects user objects to have
login_manager.init_app(server)

# Path from which the login manager will interact with
login_manager.login_view = '/snaps/login'

# Allows for anonymous users
class Users(UserMixin, Users):
	pass

# Callback to reload the user object
@login_manager.user_loader
def load_user(user_id):
	return Users.query.get(int(user_id))


# Name values for each asteroid attribute
entireDF = ['jd', 'fid', 'pid', 'diffmaglim', 'ra', 'dec', 'magpsf', 'sigmapsf', 'chipsf',
	'magap', 'sigmagap', 'magapbig', 'sigmagapbig', 'distnr', 'magnr', 'fwhm', 'elong', 'rb', 'ssdistnr',
	'ssmagnr', 'id', 'night', 'obsdist', 'phaseangle', 'G', 'H', 'heliodist', 'antaresID', 'ltc']

night_range = ztf.distinct("night")



####################################################################################################################################################
#	Initial dashboard pages
####################################################################################################################################################



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
	'color': 'white'
}
# sidebar content styling
CONTENT_STYLE = {
	'margin': '0',
	'padding': '0',
	'min-height': '100vh',
	'min-width':'100vw',
	'text-align':'center',
	'justifyContent':'center',
	'display':'flex',
}



# Search Bar design
search_bar = dbc.Row(
	[
		dbc.Col(dbc.Input(id= "search-field", type="search", placeholder="Search by ssnamenr")),
		dbc.Col(
			dbc.Button(
				"Search", id="ast-search-button", className="ms-2", n_clicks=0
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
				id="topNavBar_collapse",
				is_open=False,
				navbar=True,
			),
			dbc.NavItem(dbc.NavLink("Sign Up", href="/snaps/signup", id="signup-link", active="exact", style={"color": "#AFEEEE"})),
			dbc.NavItem(dbc.NavLink("Login", href="/snaps/login", id="login-link", active="exact", style={"color": "#AFEEEE"})),
			dbc.NavItem(dbc.Button("Logout", outline=True, id='logout_button', n_clicks=0, style={"color": "#AFEEEE"}), id='logout', style={})
		]
	),
	# this is intentionally wrong, leave it
	color="000173",
	dark=True,
	#fixed="top",
)



sidebar = html.Div(

[
	html.H1("SNAPS", className="display-4", style={'textAlign':'center'}),
	html.Hr(),
	html.P(
		"Solar System Notification Alert Processing System", className="lead", style={'textAlign':'center'}
	),
	dbc.Nav(
		[
			# Background color of pills: #a0faff
			dbc.NavItem(dbc.NavLink("Home", href="/snaps/", id="home-link", active="exact", style={"color": "#AFEEEE", "-webkit-text-stroke":"0.2px black"})),
			html.Br(),
			dbc.NavItem(
				dbc.NavLink("Account", href="/snaps/account", id="account-link", style={"color": "#AFEEEE", "-webkit-text-stroke":"0.2px black"})),
			html.Br(),
			dbc.NavItem(
				dbc.DropdownMenu(label="Plots", id="graph-link", style={"-webkit-text-stroke":"0.2px black"}, nav=True,
								 children=[dbc.DropdownMenuItem("Heat maps", href="/snaps/graph"),
										   dbc.DropdownMenuItem("Scatter plots", href="/snaps/scatter"),
										   ],
								 )),

		],
		# Makes the sidebar vertical instead of horizontal
		vertical=True,
		# Gives the active link a blue highlight
		pills=True,
	),
],
style=SIDEBAR_STYLE
)



# Sign up page
create = html.Div([

	html.H1('Sign Up', style={"color": "#AFEEEE"}),
	html.P("Please fill in this form to create an account.", style={"color": "#AFEEEE"}),
	html.Div(
		[
			dbc.Label("Username", style={"color": "#AFEEEE"}),
			dbc.Input(id="username", type="text", placeholder="Enter Username", maxLength=15, minLength=1),
		]),
	html.Br(),
	html.Div(
		[
			dbc.Label("Password", style={"color": "#AFEEEE"}),
			dbc.Input(id="password", type="password", placeholder="Enter Password", minLength=1),
		]),
	html.Br(),
	html.Div(
		[
			dbc.Label("Confirm Password", style={"color": "#AFEEEE"}),
			dbc.Input(id="confirmpassword", type="password", placeholder="Confirm Password", minLength=1),
		]),
	html.Br(),
	html.Div(
		[
			dbc.Label("Email", style={"color": "#AFEEEE"}),
			dbc.Input(id="email", type="email", placeholder="Enter Email", maxLength=50),
		]),
	html.Br(),

	html.Button('Sign Up', id='signup_button', n_clicks=0),
	html.Br(), html.Br(),
	html.Div(id='create_user', children=[])
], style={'margin-top':'40px'})



login = html.Div([

	html.H2('''Please log in to continue:''', id='h1', style={"color": "#AFEEEE"}),

	html.Div(
		[
			dbc.Label("Username", style={"color": "#AFEEEE"}),
			dbc.Input(id="uname-box", type="text", placeholder="Enter Username", maxLength=50),
		]),
	html.Br(),
	html.Div(
		[
			dbc.Label("Enter Password", style={"color": "#AFEEEE"}),
			dbc.Input(id="pwd-box", type="password", placeholder="Enter Password", maxLength=50),
		]),
	html.Br(),

	html.Button(children='Login', n_clicks=0, type='submit', id='login-button'),
	html.Div(id='login_output', children=[], style={})
], style={'margin-top':'100px'})



# Account page
account = html.Div([

	html.Br(), html.Br(),
	html.Button('My Asteroids', id='select_button', n_clicks=0, style={'textAlign':'center','margin-left':'120px', 'float':'left', 'margin-right':'50px','margin-left':'-100px', 'margin-top':'50px'}),
	html.H4("Click the button to view your saved asteroids", style={'color': '#AFEEEE', 'float':'right', 'margin-top':'50px', 'margin-right':'100px'}),
	html.Br(), html.Br(),
	html.Div(id='selection', children=[], style={'float':'left', 'margin-right':'50px','margin-left':'-100px', 'margin-top':'30px'}),
	html.Br()
],  style={'margin-left': '-800px'})



# Home page graphs as PNGs
image_filename1 = 'obs_hist.png' # replace with your own image
encoded_image1 = base64.b64encode(open(image_filename1, 'rb').read())

image_filename2 = 'lcamp_hist.png' # replace with your own image
encoded_image2 = base64.b64encode(open(image_filename2, 'rb').read())

# Home page graphs as PNGs
image_filename3 = 'lc_hist.png' # replace with your own image
encoded_image3 = base64.b64encode(open(image_filename3, 'rb').read())

image_filename4 = 'grColor_hist.png' # replace with your own image
encoded_image4 = base64.b64encode(open(image_filename4, 'rb').read())



home_page = html.Div([

	html.Div(html.Img(src='data:image/png;base64,{}'.format(encoded_image1.decode()), height='300', width='400'), style={'display':'flex', 'padding-right':'100px', 'float':'left', 'margin-left':'-150px'}),
	html.Br(),
	html.Div(html.Img(src='data:image/png;base64,{}'.format(encoded_image2.decode()), height='300', width='400'), style={'display':'flex', 'padding-left':'50px', 'margin-top':'-23px'}),
	html.Br(),
	html.Div(html.Img(src='data:image/png;base64,{}'.format(encoded_image3.decode()), height='300', width='400'), style={'display':'flex', 'padding-right':'100px', 'float':'left', 'margin-left':'-150px'}),
	html.Br(),
	html.Div(html.Img(src='data:image/png;base64,{}'.format(encoded_image4.decode()), height='300', width='400'), style={'display':'flex', 'padding-left':'50px', 'margin-top':'-23px'}),
], style={"margin-top":"30px"})



scatterplot_page = html.Div([

	html.Div([
		html.H3("Specify X/Y range to build graph from."),
		html.Br(),
		html.H3("Change attributes from dropdown to update scatter plot."),
		], style={'color':'#AFEEEE', 'margin-left':'150px', "margin-top":"50px"}
	),

	html.Div(
		id="valid_night_scatter",
		style={"width": "400px", "height": "75px", "margin": 'auto'}
	),

	html.Div([
		dcc.Input(id='year', placeholder='Year'),
		dcc.Input(id='month', placeholder='Month'),
		dcc.Input(id='day', placeholder='Day'), 
		], style={'margin-top': '25px'},
	),
	
	html.Div([
		dcc.Dropdown(
			options = [{'label': i, 'value': i } for i in entireDF],
			value = 'ra',
			id = 'scatter-xaxis-column',
			style={'margin-left':'-100px'}),
		dcc.RadioItems(
			options = [
				{'label': 'Linear', 'value': 'Linear'},
				{'label': 'Log', 'value': 'Log'}],
			value = "Linear",
			id = 'xaxis-type',
			style={'color':'#AFEEEE', 'margin-left':'-400px'}
		)], style={'margin-left':'50px','width':'100px', "margin-top":"50px", 'display': 'inline-block', 'margin-bottom':'20px'}
	),
	html.Div([
		dcc.Dropdown(
			options = [{'label': i, 'value': i } for i in entireDF],
			value = 'dec',
			id = 'scatter-yaxis-column',
			style={"width":"200px", "margin-left":"50px"}),
		dcc.RadioItems(
			options = [
				{'label': 'Linear', 'value': 'Linear'},
				{'label': 'Log', 'value': 'Log'}],
			value = "Linear",
			id = 'yaxis-type',
			style={'color':'#AFEEEE', "margin-left":"100px"}
		)], style={'margin-left':'50px','width':'200px', "margin-top":"50px", 'display': 'inline-block', 'margin-bottom':'20px'}
	),
	html.Div([
		html.Div([
			dcc.Input(id='x_lower_scatter', placeholder='X Lower Bound'),
				dcc.Input(id='x_upper_scatter', placeholder='X Upper Bound')],
				style={"display":"inline-block"}),

		html.Div([
			dcc.Input(id='y_lower_scatter', placeholder='Y Lower Bound'),
			dcc.Input(id='y_upper_scatter', placeholder='Y Upper Bound')],
			style={"display":"inline-block", "margin-left":"75px"}),

		html.Br(),html.Br(),
		html.Button(id='range_button', n_clicks=0, children='Build Graph', style={"margin-left":"10px", "background-color":"#AFEEEE", "border-radius":"12px"}),
	    html.Br(),
	], style={"display":"flex", "margin-left":"250px"}),
	html.Br(),
	dcc.Graph(id = "scatter", style={'width':'1000px', "margin-left":'200px'}),
	html.Div(
		html.Pre(id = 'click-data'),
	)])

heatmap_page = html.Div([

	html.Div([
		html.H3("Specify X/Y range to build graph from."),
		html.Br(),
		html.H3("Change attributes from dropdown to update heat map.")
		], style={'color':'#AFEEEE', 'margin-left':'150px', "margin-top":"50px"}
	),

	html.Div(
		id="valid_night_heatmap",
		style={"width": "400px", "height": "75px", "margin": 'auto'}
	),

	html.Div([
		dcc.Input(id='year', placeholder='Year'),
		dcc.Input(id='month', placeholder='Month'),
		dcc.Input(id='day', placeholder='Day'), 
		], style={'margin-top': '25px'},
	),

	html.Div([
		dcc.Dropdown(
			options = [{'label': i, 'value': i } for i in entireDF],
			value = 'ra',
			id = 'xaxis-column',
			style={'margin-left':'-100px'})
		], style={'margin-left':'50px','width':'100px', "margin-top":"50px", 'display': 'inline-block', 'margin-bottom':'20px'}
	),
	html.Div([
		dcc.Dropdown(
			options = [{'label': i, 'value': i } for i in entireDF],
			value = 'dec',
			id = 'yaxis-column',
			style={"width":"200px", "margin-left":"50px"})
		], style={'margin-left':'50px','width':'200px', "margin-top":"50px", 'display': 'inline-block', 'margin-bottom':'20px'}
	),
	html.Div([
		html.Div([
			dcc.Input(id='x_lower_heatmap', placeholder='X Lower Bound'),
				dcc.Input(id='x_upper_heatmap', placeholder='X Upper Bound')],
				style={"display":"inline-block"}),

		html.Div([
			dcc.Input(id='y_lower_heatmap', placeholder='Y Lower Bound'),
			dcc.Input(id='y_upper_heatmap', placeholder='Y Upper Bound')],
			style={"display":"inline-block", "margin-left":"75px"}),

		html.Br(),html.Br(),
		html.Button(id='range_button_heatmap', n_clicks=0, children='Build Graph', style={"margin-left":"10px", "background-color":"#AFEEEE", "border-radius":"12px"}),
	    html.Br(),
	], style={"display":"flex", "margin-left":"250px"}),
	html.Br(),
	dcc.Graph(id = "heatmap", style={'width':'1000px', "margin-left":'200px'}),
	html.Div(
		html.Pre(id = 'click-data'),
	)]  )


asteroid_page = html.Div([

    html.Div(id='asteroid', children=[]),
	html.Div([
    	dcc.Dropdown(
        	options = [{'label': i, 'value': i } for i in entireDF],
        	value = 'jd',
        	id = 'xaxis_ast'),
     	], style={'width':'200px', 'display': 'inline-block', "margin-top":"50px", 'margin-bottom':'20px'}
	),
	html.Div([
    	dcc.Dropdown(
        	options = [{'label': i, 'value': i } for i in entireDF],
        	value = 'H',
        	id = 'yaxis_ast'),
    	], style={'margin-left':'50px','width':'200px', "margin-top":"50px", 'display': 'inline-block', 'margin-bottom':'20px'}
	),
	html.Div(id='ssnamenr_data', style={'display':'inline-block', 'margin-bottom':'20px', 'margin-left': '-150px', 'color':'white', 'float':'right', "margin-top":"50px", 'margin-right': '50px'}),
	html.Br(),
	dcc.Graph(id = "scatter_ast", style={'width':'1000px', "margin-left":'200px'}),
	html.Div(
	html.Pre(id = 'click-data-ast')),
	html.Br(),
	html.Div([
    	html.Button(id='save-button', children='Save Asteroid', n_clicks=0, style={'float':'left', 'width':'150px', 'margin-top':'-25px', 'margin-left':'100px', 'height':'40px'}),
    	html.Div(id='save-output', children=[], style={'width':'400px', 'margin-left':'100px', 'margin-top':'-55px'}),
    	], style={'display':'flex', 'width':'900px', 'margin-left':'200px'})

	])


footer = html.Footer([

	html.Div([
		html.A([html.Img(src=app.get_asset_url('Northern_Arizona_Athletics_wordmark.svg.png'), style={'display':'flex','height': '2rem'})]),
		html.Div("Created by Team First Light 2022", id='footer-text', style={'margin-left':'20px'}),

		], style={'float':'left', 'padding-left':'30px','display':'flex'}),

    html.Div([
    	html.A([html.Img(src=app.get_asset_url('GitHub-Mark-32px.png'), style={'display':'flex','height': '2rem', 'margin-left':'10px',})], href="https://github.com/jrn235/First-Light", target="_blank"),
    	html.A("Project Description", href="https://www.ceias.nau.edu/cs/CS_Capstone/Projects/F21/Trilling_Gowanlock_capstone2021.pdf", style={'color':'black','margin-left':'10px','display':'flex', "text-decoration": "none"}, target="_blank"),
    	html.A("Team Website", href="https://ceias.nau.edu/capstone/projects/CS/2022/FirstLight/", style={'display':'flex', 'margin-left':'10px','color':'black', "text-decoration": "none"}, target="_blank")
    ], style={'float':'right', 'display':'flex', 'padding-right':'30px', 'padding-bottom':'10px'})
    ], id='footer', style={"padding":"15px", "border-top":"1px solid black"})



content = html.Div(id="page-content", children=[], style=CONTENT_STYLE)

app.layout = html.Div([
	dcc.Location(id="url"),
	html.Div(id='url_logout', children=[]),
	topNavBar,
	sidebar,
	content,
	footer
], style={'background-image':'linear-gradient(180deg, #000173, white)'})



##########################################################################################################
#   This function redirects the user to the desired web page
#
#       Output: Pathname to web page
#       Input: A url pathname and the url hash
##########################################################################################################
@app.callback(
	Output("page-content", "children"),
	Input("url", "pathname"),
	Input("url", "hash")
)
def render_page_content(pathname, hash):

	# If pathname is the default url
	if pathname == "/snaps/":
		return [home_page]

	# Path to the Heat Map page
	elif pathname == "/snaps/graph":
			return [heatmap_page]

	# Path to the Scatter Plot page
	elif pathname == "/snaps/scatter":
		return [scatterplot_page]

	# Path to the Individual Observation page with identification
	elif pathname == '/snaps/observation':
		return [
			html.Div(id='observation', style={'margin-left': '-450px'})
		]

	# Path to the SSNAMENR page
	elif pathname == '/snaps/asteroid':
		return [html.Div([html.Br(),html.H3(f"Asteroid {hash}",style={'color':'#AFEEEE', 'margin-right':'525px'}), asteroid_page])]

	# Path to either the Login page if not authenticated, or the Account page if authentication
	elif pathname == '/snaps/login':
		if current_user.is_authenticated:
			return dcc.Location(id='account_url', pathname='/snaps/account')
		else:
			return [login]

	# Path to the Sign Up page
	elif pathname == '/snaps/signup':
		return [create]

	# Path to the Account page if authenticated, or the Login page if not authenticated
	elif pathname == "/snaps/account":
		if current_user.is_authenticated:
			return [html.H1("Welcome " + current_user.username + "!", style={'color': '#AFEEEE', 'float':'left', 'margin-right':'600px'}), account]
		else:
			return dcc.Location(id='login_url', pathname='/snaps/login')





####################################################################################################################################################
# 	Functionality
####################################################################################################################################################


####################################################################################################################################################
#	Plotting functions
####################################################################################################################################################



##########################################################################################################
#   This function updates the plot layout to match eaxch color to a value
#
#       Output: Updated plot layout
#       Input: Plot figure
##########################################################################################################
def updateLayout(graphFig):
	return graphFig.update_layout(
		plot_bgcolor=colors['background'],
		paper_bgcolor=colors['background'],
		font_color=colors['text']
	)



##########################################################################################################
#   This function updates the heatmap for which attributes will be plotted on the X and Y axis
#
#       Output: Heatmap plot
#       Input: X and Y values, upper and lower bounds for X and Y values, X and Y axis types, Heatmap
#				column values, and an n_clicks value
##########################################################################################################
@app.callback(
	Output('heatmap', 'figure'),
	Output('valid_night_heatmap', 'children'),
	Input('range_button_heatmap', 'n_clicks'),
	Input('xaxis-column', 'value'),
	Input('yaxis-column', 'value'),
	Input('x_lower_heatmap', 'value'),
	Input('x_upper_heatmap', 'value'),
	Input('y_lower_heatmap', 'value'),
	Input('y_upper_heatmap', 'value'),
	Input('year', 'value'),
	Input('month', 'value'),
	Input('day', 'value'),
	)
def update_heatmap(n_clicks, xaxis_column_name, yaxis_column_name, x_low, x_up, y_low, y_up, year, month, day):

	# Create night integer
	night = int(year + month + day)

	# Gather a list of all props that triggered the callback
	changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

	# Check if the range button triggerd the callback
	if 'range_button' in changed_id:

		if night not in night_range:
			plot = px.density_heatmap(None)
			return plot, dbc.Alert(f'{year}-{month}-{day} Not In Database Currently', color="danger")

		# Lower bound for X axis
		x_low = float(x_low)

		# Upper bound for X axis
		x_up = float(x_up)

		# Lower bound for Y axis
		y_low = float(y_low)

		# Upper bound for Y axis
		y_up = float(y_up)

		# Create query to find the associated values under the respected X and Y column names
		filter_query = {xaxis_column_name: {"$gte":x_low, "$lte": x_up}, yaxis_column_name: {"$gte": y_low, "$lte": y_up}, "night": night}

		# Search for the data
		ztf_heatmap = ztf.find(
			filter_query,
			{xaxis_column_name: 1, yaxis_column_name: 1}
		)

		# Put the resulting data into a dataframe
		df = pd.DataFrame(ztf_heatmap, columns=(xaxis_column_name, yaxis_column_name))

		# Create a heatmap figure with the X and Y values
		plot = px.density_heatmap(df, x = xaxis_column_name, y = yaxis_column_name,
								nbinsx = 25, nbinsy = 25, text_auto = False)

		# Update the X axis
		plot.update_xaxes(title=xaxis_column_name)

		# Update the Y axis
		plot.update_yaxes(title=yaxis_column_name)

		# Update the plot
		updateLayout(plot)

		# Set n_clicks back to 0
		n_clicks = 0

		# Clear the dataframe to conserve memory
		del df

		# Return the plot
		return plot

	# If the range button dd not trigger the callback
	else:

		# Prevent the callback from firing
		raise PreventUpdate



##########################################################################################################
#   This function updates the main scatter plot
#
#       Output: Scatter plot
#       Input: X and Y values, upper and lower bounds for X and Y values, X and Y axis types, Scatter
#				column values, and an n_clicks value
##########################################################################################################
@app.callback(
	Output('scatter', 'figure'),
	Output('valid_night_scatter', 'children'),
	Input('range_button', 'n_clicks'),
	Input('scatter-xaxis-column', 'value'),
	Input('scatter-yaxis-column', 'value'),
	Input('xaxis-type', 'value'),
	Input('yaxis-type', 'value'),
	Input('x_lower_scatter', 'value'),
	Input('x_upper_scatter', 'value'),
	Input('y_lower_scatter', 'value'),
	Input('y_upper_scatter', 'value'),
	Input('year', 'value'),
	Input('month', 'value'),
	Input('day', 'value'),
	prevent_initial_call = True
	)
def update_scatter(n_clicks, xaxis_column_name, yaxis_column_name, xaxis_type, yaxis_type, x_low, x_up, y_low, y_up, year, month, day):

	# Build the night the user selects
	night = int(year + month + day)

	# Gather a list of all props that triggered the callback
	changed_id = [p['prop_id'] for p in dash.callback_context.triggered][0]

	# Check if the range button triggerd the callback
	if 'range_button' in changed_id:
		# If night is not in database, do not update graph, will consider adding an alert to user that the night is not in the database
		if night not in night_range:
			fig = px.scatter(None)
			updateLayout(fig)
			return fig, dbc.Alert(f'{year}-{month}-{day} Not In Database Currently', color="danger")

		# Lower bound for X axis
		x_low = float(x_low)

		# Upper bound for X axis
		x_up = float(x_up)

		# Lower bound for Y axis
		y_low = float(y_low)

		# Upper bound for Y axis
		y_up = float(y_up)

		# X axis Log
		xlog = xaxis_type == "Log"

		# Y axis Log
		ylog = yaxis_type == "Log"

		# Create query to find the associated values under the respected X and Y column names
		filter_query = {xaxis_column_name: {"$gte":x_low, "$lte": x_up}, yaxis_column_name: {"$gte": y_low, "$lte": y_up}, "night": night}

		# Search for the data
		ztf_scatter = ztf.find(
			filter_query,
			{xaxis_column_name: 1, yaxis_column_name: 1, "ssnamenr": 1}
		)

		# Put the resulting data into a dataframe
		df = pd.DataFrame(ztf_scatter)

		# Create a scatter plot figure with the X and Y values
		fig = px.scatter(df,
				x = xaxis_column_name, y = yaxis_column_name,
				hover_name = 'ssnamenr',
				hover_data={xaxis_column_name:':.3f', yaxis_column_name:':.3f'},
				log_x = xlog, log_y = ylog
				)

		# Update the X axis
		fig.update_xaxes(title=xaxis_column_name)

		# Update the Y axis
		fig.update_yaxes(title=yaxis_column_name)

		# Create a faster, more dynamic plot that only renders 100000 data points at a time
		# plot = DynamicPlot(fig, max_points=100000)

		# Update the plot
		updateLayout(fig)

		# Set n_clicks back to 0
		n_clicks = 0

		# Clear the dataframe to conserve memory
		del df

		# Return the plot
		return fig, None

	# If the range button dd not trigger the callback
	else:

		# Prevent the callback from firing
		raise PreventUpdate



##########################################################################################################
#   This function updates the ssnamenr asteroid scatter plot
#
#       Output: Scatter plot
#       Input: X and Y values, and a url hash
##########################################################################################################
@app.callback(
	Output('scatter_ast', 'figure'),
	Input('xaxis_ast', 'value'),
	Input('yaxis_ast', 'value'),
	Input('url', 'hash'))
def update_scatter_asteroid(xaxis_ast, yaxis_ast, hash):

	# Check if the url hash is a ZTF value
	if(hash.startswith("#ZTF")):

		# Prevent the callback from firing
		raise PreventUpdate

	# Create a query to search for an ssnamenr
	filter_query = { "ssnamenr": int(hash[1:]) }

	# Search for the ssnamenr
	scatter_mong = ztf.find(
		filter_query
	)

	# Put the resulting data into a dataframe
	df = pd.DataFrame(scatter_mong)

	# Create a scatter plot figure with the X and Y values
	plot = px.scatter(df, xaxis_ast, yaxis_ast, hover_name = 'id')

	# Update the X axis
	plot.update_xaxes(title=xaxis_ast)

	# Update the Y axis
	plot.update_yaxes(title=yaxis_ast)

	# Update the plot
	updateLayout(plot)

	# Clear the dataframe to conserve memory
	del df

	# Return the plot
	return plot



##########################################################################################################
#   This function creates a link for an asteroid after clicking on a data point in the scatter plot
#
#       Output: Link to asteroid observation
#       Input: Scatter Plot clickData
##########################################################################################################
@app.callback(
	Output('click-data', 'children'),
	Input('scatter', 'clickData')
)
def click_scatter(clickData):

	# Check if a data point was clicked on
	if(clickData != None):

		# Store the data from the clicked data point
		click_data = clickData['points'][0]['hovertext']

		# Create a link to visit the asteroid with the data value ssnamenr
		ssnamenr_link = dcc.Link(html.Button(id='scatter_button', n_clicks=0, children=f'Go to {click_data}', style={"margin-top":"10px", "margin-left":"10px"}), href = f'/snaps/asteroid#{click_data}')

		# Return the link
		return ssnamenr_link

	# If a data point was not clicked
	else:

		# Prevent the callback from firing
		raise PreventUpdate



##########################################################################################################
#   This function creates a link for an asteroid observation after clicking on a data point in the scatter plot
#
#       Output: Link to asteroid observation
#       Input: Scatter Plot clickData
##########################################################################################################
@app.callback(
	Output('click-data-ast', 'children'),
	Input('scatter_ast', 'clickData')
)
def click_scatter_ast(clickData):

	# Check if a data point was clicked on
	if(clickData != None):

		# Store the data from the clicked data point
		click_data = clickData['points'][0]['hovertext']

		# Create a link to visit the individual asteroid
		observation_link = dcc.Link(html.Button(id='scatter_ast_button', n_clicks=0, children=f'Go to {click_data}', style={"margin-top":"10px", "margin-left":"10px"}), href = f'/snaps/observation#{click_data}')

		# Return the link
		return observation_link

	# If a data point was not clicked
	else:

		# Prevnt the callback from firing
		raise PreventUpdate





####################################################################################################################################################
#	User-related functions
####################################################################################################################################################



# Search Bar Callback, Prevents intial firing of callback before a value is inputted
@app.callback(
	Output("url", "href"),
	[Input("ast-search-button", "n_clicks")],
	[Input("search-field", "value")],
	prevent_initial_call=True
)
def asteroid_search_bar(n_clicks, value):

	# If the button was clicked, continue
	if n_clicks > 0:

		# If the value inputted was an observation
		if(value.startswith("ZTF")):

			# Return the obsrvation page
			return f"/snaps/observation#{value}"
		else:
			# Still need to implement catch for anything other than a number
			# being typed in. Sometimes the search bar jumps the gun and executes
			# before button is it. Need to fix this.
			#if(isinstance(value, str)):
			#	return dash.no_update

			# Queries to see if ssnamenr exists. Does not currently throw message
			# to user saying "doesn't exist".

			# Cast thee input value to an integer
			value = int(value)

			# If the input value is not a valid i.e. less than zero
			if(value < 0):

				# Prevent the callback from firing
				raise PreventUpdate

			# If the value is valid, create a dict pair to search for the ssnamenr value
			filter_query = { "ssnamenr": value }

			# Serch for the ssnamenr value in the ZTF table
			scatter_mong = ztf.find(
				filter_query
			)

			# Put all values into a dataframe
			ssnamenr_df = pd.DataFrame(scatter_mong)

			# If the search returns an empty dataframe
			if(len(ssnamenr_df) == 0):

				# Prevent the callback from firing
				raise PreventUpdate

			# Search returns a non-empty dataframe
			else:

				# Return the associated ssnamenr page
				return f"/snaps/asteroid#{value}"



# Callback for ssnamenr scatter plot page to display the observation count
@app.callback(
    Output('ssnamenr_data', 'children'),
    Input('url', 'hash')
)
def ssnamenr_data(hash):

	# Take out the # from the ssnamenr value input
    hash = hash.replace("#", "")

    # Create a dict pair to search for the ssnamenr value
    filter_query = { "ssnamenr": hash }

    # Search for the ssnamenr value in the asteroids table
    searched = derived.find(
        filter_query
    )

    # Put all values into dataframe
    original_df = pd.DataFrame(searched)

    # Pull out the value of observationCounts
    counts = original_df["observationCounts"]

    # Create a string with the observation counts value
    observation_string = f'Observation Count: {counts.iloc[0]}'

    # Return the html object with the observation counts to the scatter plot page
    return html.H3(observation_string)



# Callback for displaying individual observation data for analysis
@app.callback(
	Output('observation', 'children'),
	Input('url', 'hash')
)
def observation_page(hash):

	# Check if the value inputted was an observation
	if(hash.startswith("#ZTF")):

		# Take out # from the input
		hash = hash.replace("#", "")

		# Create a dict pair to search for the ZTF value
		filter_query = { "id": hash }

		# Serch for the ZTF value in the ZTF table
		searched = ztf.find(
			filter_query
		)

		# Create a dataframe with the found value
		original_df = pd.DataFrame(searched)

		# Transpose the dataframe so that it is verticala and not horizontal
		original_df = original_df.transpose()

		# Create an empty list to put items in dict format
		dict_list = []

		# need to fix this line, maybe df.items
		## For each index and row value
		for index, row in original_df.itertuples():

			# Create a pair value from the index and row
			dict_data = (str(index), str(row))

			# Append the pair value to the dict list
			dict_list.append(dict_data)

		# Cast the dict list to a dictionary
		df_dict = dict(dict_list)

		# Create a new dataframe from the dict list dictionary
		transposed_df = pd.DataFrame.from_dict(df_dict, orient='index')

		# Reset the indicies
		transposed_df = transposed_df.reset_index()

		# Create the column names for the dataframe
		transposed_df.columns = ['Attribute','Value']

		# Create columns for the datatable
		columns = [{"name": i, "id": i} for i in transposed_df.columns]

		# Create a new dataframe to be treated like records and thus as  a Attribute - Value pairing
		dataframe = transposed_df.to_dict('records')

		# Create and return the datatable
		return html.Div([html.H3(f"Observation {hash}",style={'color':'#AFEEEE'}), html.Br(), dt.DataTable(data=dataframe, columns = columns, style_as_list_view=True, style_header={'textAlign': 'center', 'border':'1px rgb(10, 41, 122)', 'backgroundColor': 'transparent','fontWeight': 'bold', 'color':'#AFEEEE'}, style_table={'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'}, style_data={'border':'none','fontWeight':'bold','color':'black', 'backgroundColor': 'rgba(255,255,255,0.5)', 'paddingLeft': '25px', 'paddingTop': '20px', 'textAlign':'center'}, export_format='csv')])



##########################################################################################################
#   This function creates a user account using a username, password, and email; and inserts thee user into
# 	the "users" SQLite database
#
#       Output: Into a Div with the ID 'create_user'
#       Input: The n_clicks value entered into the signup button when clicked
#       State: Username, Password, Email
##########################################################################################################
@app.callback(
	[Output('create_user', "children")],
	[Input('signup_button', 'n_clicks')],
	[State('username', 'value'), State('password', 'value'), State('confirmpassword', 'value'), State('email', 'value')],
	prevent_initial_call=True,
)
def insert_users(n_clicks, username, password, check_password, email):
	# Hash the password
	hashed_password = generate_password_hash(password, method='sha256')

	# Valid Email constraints
	regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

	# Check if all the fields are not empty
	if username is not None and password is not None and check_password is not None and email is not None:

		# Checks if no errors occur
		try:

			# Check if the password and confirm password values are the same
			if check_password == password:

				# Check if the email is valid
				if re.fullmatch(regex, email):

					# Create a new user object for the database
					insert = Users_tbl.insert().values(username=username,  password=hashed_password, email=email)

					# Connect to the database
					user_con = users_engine.connect()

					# Insert the new user into the database
					user_con.execute(insert)

					# Close the connection to the database
					user_con.close()

					user = Users.query.filter_by(username=username).first()

					# If the user exists
					if user:
						login_user(user)

					# Return to the home page
					return [dbc.Alert('Account Successfully created', color="success")]
				else:

					# Email is not valid
					return [dbc.Alert('This is not a valid email address', color="danger")]

			# If the passwords do not match
			else:

				# Print the error
				return [dbc.Alert('Passwords do no match', color="danger")]

		# Which error occured?
		except SQLAlchemyError as e:

			# To see error
			error = str(e.__dict__['orig'])

			# Username already in use
			if error == 'UNIQUE constraint failed: users.username':

				# Print the error
				return [dbc.Alert('This username is already taken', color="danger")]

			# Email already used
			elif error == 'UNIQUE constraint failed: users.email':

				return [dbc.Alert('There is already an account associated with this email', color='danger')]

	# If one or more of the fields are empty
	else:
		# Print the error
		return [dbc.Alert('A field is empty', color="danger")]



##########################################################################################################
#   This function saves the current asteroid to a list corresponding to the logged in user for display in
#	the account page
#
#       Output: Into a Div with the ID 'save-output'
#       Input: The n_clicks value entered into the save asteroid button when clicked
#       State: Saves the url hash
##########################################################################################################
@app.callback(
	Output('save-output', 'children'),
	Input('save-button', 'n_clicks'),
	State('url', 'hash')
)
def save_asteroid(n_clicks, hash):
	if(n_clicks > 0):
		if(current_user.is_authenticated):
			username = current_user.username
			hash = hash.replace("#", "")

			already_exists = select(UserData_tbl.c.id).where((UserData_tbl.c.username) == username).where((UserData_tbl.c.asteroid_id) == hash)
			connection = user_data_engine.connect()
			already_exists_result = connection.execute(already_exists)
			check_result = already_exists_result.first()

			if(check_result is None):
				insert = UserData_tbl.insert().values(username=username, asteroid_id=hash)

				# Insert the new user into the database
				connection.execute(insert)

				# Close the connection to the database
				connection.close()

				# Return to the home page
				return [html.Br(), dbc.Alert("Asteroid Saved", color='success')]

			else:
				return [html.Br(), dbc.Alert("You already have this asteroid saved!", color='info')]
		else:
			return [html.Br(), dbc.Alert('You must be logged in to save asteroids!', color="danger")]



##########################################################################################################
#   This function uses the input username to query the database for all asteroids that correspond to it
#	and display the asteroids in a table
#
#       Output: Into a Div with the ID 'selection'
#       Input: The username value entered into the select button when clicked
#       State: Saves the username
##########################################################################################################
@app.callback(
	Output('selection', 'children'),
	[Input('select_button', 'n_clicks')]
)
def displayUserData(n_clicks):

	# Check if the display asteroids button was clicked
	if(n_clicks > 0):

		# Query that selects the asteroid_id column values where the username column values match the inputted
		# username
		username = current_user.username
		query = select(UserData_tbl.c.asteroid_id).where(UserData_tbl.c.username == username)

		# Connect to the database
		with user_data_engine.connect() as connection:

			# Try to
			try:
				# Execute the query
				result = connection.execute(query)

			# There was an error
			except Exception as e:

					# Print the error
					print(e)

			# The query executed
			else:

				# Create a list for the JSON data that needs to be passed into the dataframe from the query
				query_list = []

				# Loop through each row queried
				for row in result:

					# Create a list for the row data
					row_list = []

					# Set the row data into a tuple
					row_data = (row[0])

					# Append row data into the row list and take out the square brackets [ ] around the data
					row_list.append(row_data.replace("[", "").replace("]", ""))

					# JSON serialize the data
					jsonString = json.dumps(row_list)

					# Append the JSON string while taking out the square brackets [ ] and quotes " " around
					# the data
					query_list.append(jsonString.replace("[", "").replace("]", "").replace('"', ""))

				# Disconnect from the database
				result.close()

				# Use numpy to put the JSON data into an Array
				cleaned_result_list = np.array(query_list)

				# Create a list for the asteroid links
				link_array = []

				# Loop through each value in the Array
				for value in cleaned_result_list:

					# Reformat the value to be an HTML link using an f string with HTML code and the value
					value = f"<a href='/snaps/asteroid#{value}'>{value}</a>"

					# Append the link into the link list
					link_array.append(value)

				# Create a Dataframe using the link data
				df = pd.DataFrame(link_array)

				# Set the column name to be asteroid_id
				df.columns = ['Asteroid ID']

				# Set the columns to be a dictionary with the column name and value, and for it to contain
				# HTML code
				columns = [{"name": i, "id": i, "presentation": "markdown"} for i in df.columns]

				# Set a data array to be the DataFrame split into dictionary records
				data_list = df.to_dict('records')

				# Return a Dash Datatable with the data centered
				return dt.DataTable(data=data_list, columns=columns, style_header={'textAlign': 'center'}, style_table={'width':'110px'}, style_data_conditional=[{'if': {'column_id': 'Asteroid ID',},'textAlign': 'center', 'padding-left': '27px', 'padding-top': '15px'}], markdown_options={"html": True})



##########################################################################################################
#   This function is used to login the user
#
#       Output: Into a Div with the ID 'login_output'
#       Input: The button n_clicks value entered into the logout button when clicked
#       State: Saved username and password from the input
##########################################################################################################
@app.callback(
	Output('login_output', 'children'), [Input('login-button', 'n_clicks')],
	[State('uname-box', 'value'), State('pwd-box', 'value')])
def login_to_account(n_clicks, input1, input2):
	if n_clicks > 0:
		# Gets the username data from the database
		user = Users.query.filter_by(username=input1).first()

		# If the user exists
		if user:
			# Check the passwords to see if they match the recorded password in the database
			if check_password_hash(user.password, input2):
				login_user(user)
				# All is good, continue
				return dcc.Location(pathname="/snaps/account", id="account-link")
			# If one, or both, password(s) do not match
			else:
				# Print the error
				return [html.Br(), dbc.Alert('Incorrect Password', color="danger")]

		# If the username does not exist
		else:
			# Print the Error
			return [html.Br(), dbc.Alert('Username Doesn\'t Exist', color="danger")]



##########################################################################################################
#   This function is used to logout the user
#
#       Output: Into a Div with the ID 'url_logout'
#       Input: The n_clicks value entered into the login button when clicked
##########################################################################################################
@app.callback(
	Output('url_logout', 'children'),
   [Input('logout_button', 'n_clicks')],
   prevent_initial_call=True)
def logout_of_account(n_clicks):

	# Check if the logout button was clicked
	if n_clicks > 0:

		# Check if the user is already logged in
		if current_user.is_authenticated:

			# Log out the user
			logout_user()

			# Return to the home pagee
			return dcc.Location(pathname="/snaps/", id="home-link")

		# If the user was not logged in
		else:

			# Prevent the callback from firing
			raise PreventUpdate


if __name__ == '__main__':
	app.run_server(host='127.0.0.1', port=8050, debug=True)