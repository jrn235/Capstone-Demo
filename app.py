from click import style
import dash
from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
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

import base64

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
	#'background-color': '#000173',
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



# Home page graphs as PNGs
image_filename1 = 'hist1.png' # replace with your own image
encoded_image1 = base64.b64encode(open(image_filename1, 'rb').read())

image_filename2 = 'hist_linear.png' # replace with your own image
encoded_image2 = base64.b64encode(open(image_filename2, 'rb').read())

def updateLayout(graphFig):
	return graphFig.update_layout(
		plot_bgcolor=colors['background'],
		paper_bgcolor=colors['background'],
		font_color=colors['text']
	)

#app = dash.Dash(__name__, requests_pathname_prefix='/snaps-dev/', external_stylesheets=[dbc.themes.FLATLY])
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
server = app.server
app.config.suppress_callback_exceptions = True

constring = "mongodb://mjl79:NxMswiyz0oGQ4kT2XdqM@cmp4818.computers.nau.edu:27017/?authSource=admin"

client = pymongo.MongoClient(constring)
ztf = client.ztf.ztf

warnings.filterwarnings("ignore")

# Connect to the userData SQLite database file
user_data_con = sqlite3.connect('userData.sqlite')
user_data_engine = create_engine('sqlite:///userData.sqlite')
user_data_db = SQLAlchemy()

class UserData(user_data_db.Model):
	id = user_data_db.Column(user_data_db.Integer, primary_key=True)
	username = user_data_db.Column(user_data_db.String(15), unique=False, nullable=False)
	asteroid_id = user_data_db.Column(user_data_db.String(50), unique=False)
UserData_tbl = Table('user_data', UserData.metadata)

# Creates the user_data table within the database
def create_userData_table():
	UserData.metadata.create_all(user_data_engine)
create_userData_table()


######################################################
### Account, login, and logout functionality setup ###
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
login_manager.login_view = '/snaps-dev/login'
class Users(UserMixin, Users):
	pass
# Callback to reload the user object
@login_manager.user_loader
def load_user(user_id):
	return Users.query.get(int(user_id))
###########################################

entireDF = ['jd', 'fid', 'pid', 'diffmaglim', 'ra', 'dec', 'magpsf', 'sigmapsf', 'chipsf',
	'magap', 'sigmagap', 'magapbig', 'sigmagapbig', 'distnr', 'magnr', 'fwhm', 'elong', 'rb', 'ssdistnr',
	'ssmagnr', 'id', 'night', 'obsdist', 'phaseangle', 'G', 'H', 'heliodist', 'antaresID', 'ltc']

# [('ztf',), ('orbdat',), ('desigs',), ('other_desig',)]
# magpsf and sigmapsf select through SQL
df = pd.DataFrame()




# Search Bar
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

# Search Bar Callback
@app.callback(
	Output("url", "href"),
	[Input("ast-search-button", "n_clicks")],
	[Input("search-field", "value")],
	prevent_initial_call=True
)
def asteroid_search_bar(n_clicks, value):
	if n_clicks > 0:
		if(value.startswith("ZTF")):
			return f"/snaps-dev/observation#{value}"
		else:
			return f"/snaps-dev/asteroid#{value}"

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
			dbc.NavItem(dbc.NavLink("Login", href="/snaps-dev/login", id="login-link", active="exact", style={"color": "#AFEEEE"})),
			dbc.NavItem(dbc.NavLink("Sign Up", href="/snaps-dev/signup", id="signup-link", active="exact", style={"color": "#AFEEEE"}))
		]
	),
	# this is intentionally wrong
	color="000173",
	dark=True,
	#fixed="top",

)

# Callback for top Navigation bar
@app.callback(
	Output("topNavBar-collapse", "is_open"),
	[Input("topNavBar-toggler", "n_clicks")],
	[State("topNavBar_collapse", "is_open")],
)
def toggle_navbar_collapse(n, is_open):
	if n:
		return not is_open
	return is_open

# Sidebar creation
sidebar = html.Div(
	[
		html.H1("SNAPS", className="display-4", style={'textAlign':'center'}),
		html.Hr(),
		html.P(
			"Solar System Notification Alert Processing System", className="lead", style={'textAlign':'center'}
		),
		dbc.Nav(
			[
				# background color of pills: #a0faff
				dbc.NavItem(dbc.NavLink("Home", href="/snaps-dev/", id="home-link", active="exact", style={"color": "#AFEEEE"})),
				html.Br(),
				dbc.NavItem(
					dbc.NavLink("Account", href="/snaps-dev/account", id="account-link", active="exact", style={"color": "#AFEEEE"})),
				html.Br(),
				dbc.NavItem(
					dbc.DropdownMenu(label="Plots", id="graph-link", style={"color": "#AFEEEE"}, nav=True,
									 children=[dbc.DropdownMenuItem("Heat maps",
																	href="/snaps-dev/graph"),
											   dbc.DropdownMenuItem("Scatter plots",
																	href="/snaps-dev/scatter"),
											   ],
									 )),
				html.Br(),
				dbc.NavItem(
					dbc.NavLink("Reference Links", href="/snaps-dev/otherlinks", id="links-link", active="exact", style={"color": "#AFEEEE"})),
			],
			# makes the sidebar vertical instead of horizontal
			vertical=True,
			# gives the active link a blue highlight
			pills=True,
		),
	],
	style=SIDEBAR_STYLE,

)

# Sign up page
create = html.Div([
			html.H1('Sign Up', style={"color": "#AFEEEE"}),
			html.P("Please fill in this form to create an account.", style={"color": "#AFEEEE"}),
			dcc.Location(id='creation', refresh=True),
			html.Div(
				[
					dbc.Label("Username", style={"color": "#AFEEEE"}),
					dbc.Input(id="username", type="text", placeholder="Enter Username", maxLength=15),
				]),
			html.Br(),
			html.Div(
				[
					dbc.Label("Password", style={"color": "#AFEEEE"}),
					dbc.Input(id="password", type="password", placeholder="Enter Password"),
				]),
			html.Br(),
			html.Div(
				[
					dbc.Label("Confirm Password", style={"color": "#AFEEEE"}),
					dbc.Input(id="confirmpassword", type="password", placeholder="Confirm Password"),
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
		], style={'margin-top':'40px'})  # end div

# Login page
login = html.Div([
			dcc.Location(id='url_login', refresh=True),
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
		], style={'margin-top':'100px'})  # end div

# Account page
account = html.Div([
					html.Br(),
					html.Button('Logout', id='logout_button', n_clicks=0),
					html.Br(), html.Br(),
					html.Div(id='url_logout', children=[]),
					html.Button('My Asteroids', id='select_button', n_clicks=0),
					html.Br(), html.Br(),
					html.Div(id='selection', children=[]),
					html.Br()
			],  style={'margin-left': '-950px'})

home_page = html.Div([
				html.H1("Home Page", style={"color": "#AFEEEE", 'margin-left':'200px', 'margin-bottom':'20px'}),
				html.Div(html.Img(src='data:image/png;base64,{}'.format(encoded_image1.decode()), height='300', width='400'), style={'display':'flex', 'padding-right':'100px', 'float':'left', 'margin-left':'-150px'}),
				html.Br(),
				html.Div(html.Img(src='data:image/png;base64,{}'.format(encoded_image2.decode()), height='300', width='400'), style={'display':'flex', 'padding-left':'50px', 'margin-top':'-23px'}),
				html.Br(),
				html.Div(html.Img(src='data:image/png;base64,{}'.format(encoded_image1.decode()), height='300', width='400'), style={'display':'flex', 'padding-right':'100px', 'float':'left', 'margin-left':'-150px'}),
				html.Br(),
				html.Div(html.Img(src='data:image/png;base64,{}'.format(encoded_image2.decode()), height='300', width='400'), style={'display':'flex', 'padding-left':'50px', 'margin-top':'-23px'}),
			])

other_links = html.Div([
		html.H1("Here are a few reference links", style={"color": "#AFEEEE"}),
		html.H3(dcc.Link(html.A('Github Repository'), href = 'https://github.com/jrn235/First-Light', target="_blank")),
		html.H3(dcc.Link(html.A('Project Description'), href = 'https://www.ceias.nau.edu/cs/CS_Capstone/Projects/F21/Trilling_Gowanlock_capstone2021.pdf', target="_blank")),
		html.H3(dcc.Link(html.A('Team Website'), href = 'https://ceias.nau.edu/capstone/projects/CS/2022/FirstLight/', target="_blank"))
		])

scatterplot_page = html.Div([
				html.Div([
					dcc.Dropdown(
						options = [{'label': i, 'value': i } for i in entireDF],
						value = 'ra',
						id = 'xaxis-column'),
					dcc.RadioItems(
						options = [
							{'label': 'Linear', 'value': 'Linear'},
							{'label': 'Log', 'value': 'Log'}],
						value = "Linear",
						id = 'xaxis-type',
						style={'color':'#AFEEEE'}
					)], style={'margin-left':'50px','width':'200px', "margin-top":"50px", 'display': 'inline-block', 'margin-bottom':'20px'}
				),
				html.Div([
					dcc.Dropdown(
						options = [{'label': i, 'value': i } for i in entireDF],
						value = 'dec',
						id = 'yaxis-column'),
					dcc.RadioItems(
						options = [
							{'label': 'Linear', 'value': 'Linear'},
							{'label': 'Log', 'value': 'Log'}],
						value = "Linear",
						id = 'yaxis-type',
						style={'color':'#AFEEEE'}
					)], style={'margin-left':'50px','width':'200px', "margin-top":"50px", 'display': 'inline-block', 'margin-bottom':'20px'}
				),
				html.Br(),
				dcc.Graph(id = "scatter", style={'width':'1000px', "margin-left":'200px'}),
				html.Div(
					html.Pre(id = 'click-data'),
				)]  )

heatmap_page = html.Div([
				html.Div([
					dcc.Dropdown(
						options = [{'label': i, 'value': i } for i in entireDF],
						value = 'ra',
						id = 'xaxis-column'),
					dcc.RadioItems(
						options = [
							{'label': 'Linear', 'value': 'Linear'},
							{'label': 'Log', 'value': 'Log'}],
						value = "Linear",
						id = 'xaxis-type',
						style={'color':'#AFEEEE'}
					)], style={'margin-left':'50px','width':'200px', "margin-top":"50px", 'display': 'inline-block', 'margin-bottom':'20px'}
				),
				html.Div([
					dcc.Dropdown(
						options = [{'label': i, 'value': i } for i in entireDF],
						value = 'dec',
						id = 'yaxis-column'),
					dcc.RadioItems(
						options = [
							{'label': 'Linear', 'value': 'Linear'},
							{'label': 'Log', 'value': 'Log'}],
						value = "Linear",
						id = 'yaxis-type',
						style={'color':'#AFEEEE'}
					)], style={'margin-left':'50px','width':'200px', "margin-top":"50px", 'display': 'inline-block', 'margin-bottom':'20px'}
				),
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
        value = 'ra',
        id = 'xaxis_ast'),
     ], style={'width':'200px', 'display': 'inline-block', "margin-top":"50px", 'margin-bottom':'20px'}
),
html.Div([
    dcc.Dropdown(
        options = [{'label': i, 'value': i } for i in entireDF],
        value = 'dec',
        id = 'yaxis_ast'),
    ], style={'margin-left':'50px','width':'200px', "margin-top":"50px", 'display': 'inline-block', 'margin-bottom':'20px'}
),
html.Br(),
dcc.Graph(id = "scatter_ast", style={'width':'1000px', "margin-left":'200px'}),
html.Div(
html.Pre(id = 'click-data-ast')),
html.Br(),
html.Button(id='save-button', children='Save Asteroid', n_clicks=0, style={'margin-left':'-100px'}),
html.Div(id='save-output', children=[])

])






content = html.Div(id="page-content", children=[], style=CONTENT_STYLE)

app.layout = html.Div([
	dcc.Location(id="url"),
	topNavBar,
	sidebar,
	content
], style={'background-image':'linear-gradient(180deg, #000173, white)'})

@app.callback(
	Output("page-content", "children"),
	Input("url", "pathname")
)
def render_page_content(pathname):
	# if pathname is the main page show that main graph
	if pathname == "/snaps-dev/":
		return [home_page]

	elif pathname == "/snaps-dev/graph":
			return [heatmap_page]
			
	elif pathname == "/snaps-dev/scatter":
			return [scatterplot_page]

	elif pathname == '/snaps-dev/observation':
		return [
			html.Div(id='observation', style={'margin-left': '-500px'})
		]

	elif pathname == '/snaps-dev/asteroid':
		return [asteroid_page]

	elif pathname == '/snaps-dev/login':
		if current_user.is_authenticated:
			return [html.H1("Welcome " + current_user.username + "!", style={'color': '#AFEEEE', 'margin-left':'-50px'}), account]
		else:
			return [login]

	elif pathname == '/snaps-dev/signup':
		return [create]

	elif pathname == "/snaps-dev/account":
		if current_user.is_authenticated:
			return [html.H1("Welcome " + current_user.username + "!", style={'color': '#AFEEEE'}), account]
		else:
			return [login]

	elif pathname == "/snaps-dev/otherlinks":
		return [other_links]

@app.callback(
	Output('observation', 'children'),
	Input('url', 'hash')
)
def observation_page(hash):
	if(hash.startswith("#ZTF")):
		hash = hash.replace("#", "")
		filter_query = { "id": hash }
		searched = ztf.find(
			filter_query
		)

		original_df = pd.DataFrame(searched)


		original_df = original_df.transpose()

		dict_list = []
		# need to fix this line, maybe df.items
		for index, row in original_df.itertuples():

			dict_data = (str(index), str(row))
			dict_list.append(dict_data)

		df_dict = dict(dict_list)

		transposed_df = pd.DataFrame.from_dict(df_dict, orient='index')

		transposed_df = transposed_df.reset_index()

		transposed_df.columns = ['Attribute','Value']
		columns = [{"name": i, "id": i} for i in transposed_df.columns]

		dataframe = transposed_df.to_dict('records')

		return html.Div([html.H3(f"Observation {hash}",style={'color':'#AFEEEE'}), html.Br(), dt.DataTable(data=dataframe, columns = columns, style_as_list_view=True, style_header={'textAlign': 'center', 'border':'1px rgb(10, 41, 122)', 'backgroundColor': 'transparent','fontWeight': 'bold', 'color':'#AFEEEE'}, style_table={'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'}, style_data={'border':'none','fontWeight':'bold','color':'black', 'backgroundColor': 'rgba(255,255,255,0.5)', 'paddingLeft': '25px', 'paddingTop': '20px', 'textAlign':'center'}, export_format='csv')])



@app.callback(
	Output('click-data', 'children'),
	Input('scatter', 'clickData')
)
def click_scatter(clickData):
	if(clickData != None):
		click_data = clickData['points'][0]['hovertext']
		goto = html.H2(dcc.Link(html.A(f'Go to {click_data}'), href = f'/snaps-dev/asteroid#{click_data}'))
		return goto

@app.callback(
	Output('scatter', 'figure'),
	Input('xaxis-column', 'value'),
	Input('yaxis-column', 'value'),
	Input('xaxis-type', 'value'),
	Input('yaxis-type', 'value')
	)
def update_scatter(xaxis_column_name, yaxis_column_name, xaxis_type, yaxis_type):
	# Larger query
	# {"sigmapsf": {"$gte": 0.15, "$lte": 0.3}, "magpsf": {"$gte": 9, "$lte": 14}}
	# Filter to speed up during demonstration

	xlog = xaxis_type == "Log"
	ylog = yaxis_type == "Log"

	filter_query = {xaxis_column_name: {"$gte": 0.02, "$lte": 0.25}, yaxis_column_name: {"$gte": 9, "$lte": 14}}
	ztf_scatter = ztf.find(
		filter_query
	)

	df = pd.DataFrame(ztf_scatter)

	if(len(df) == 0):
		return html.Div([
			html.H1("No observations for ssnamenr of " + hash + "! Try another search.")
		])

	fig = px.scatter(df, x = xaxis_column_name, y = yaxis_column_name, 
		hover_name = 'ssnamenr', 
		hover_data={xaxis_column_name:':.3f', yaxis_column_name:':.3f'},
		log_x = xlog, log_y = ylog)

	fig.update_xaxes(title=xaxis_column_name)
	fig.update_yaxes(title=yaxis_column_name)
	plot = DynamicPlot(fig, max_points=1000)

	updateLayout(fig)
	return plot.fig

@app.callback(
	Output('scatter_ast', 'figure'),
	Input('xaxis_ast', 'value'),
	Input('yaxis_ast', 'value'),
	Input('url', 'hash'))
def update_scatter_asteroid(xaxis_ast, yaxis_ast, hash):
	if(hash.startswith("#ZTF")):
		return
	filter_query = { "ssnamenr": int(hash[1:]) }
	#ztf_query = { "ssnamenr": 1, xaxis_ast: 1, yaxis_ast: 1 }
	scatter_mong = ztf.find(
		filter_query
	)

	df = pd.DataFrame(scatter_mong)
	fig = px.scatter(df, xaxis_ast, yaxis_ast, hover_name = 'id')

	fig.update_xaxes(title=xaxis_ast)
	fig.update_yaxes(title=yaxis_ast)

	updateLayout(fig)
	return fig

@app.callback(
	Output('click-data-ast', 'children'),
	Input('scatter_ast', 'clickData')
)
def click_scatter_ast(clickData):
	if(clickData != None):
		click_data = clickData['points'][0]['hovertext']
		goto = html.H2(dcc.Link(html.A(f'Go to {click_data}'), href = f'/snaps-dev/observation#{click_data}'))
		return goto

@app.callback(
	Output('heatmap', 'figure'),
	Input('xaxis-column', 'value'),
	Input('yaxis-column', 'value'))
def update_heatmap(xaxis_column_name, yaxis_column_name):
	filter_query = {"sigmapsf": {"$gte": 0.15, "$lte": 0.35}, "magpsf": {"$gte": 8, "$lte": 15}}
	ztf_query = {xaxis_column_name: 1, yaxis_column_name: 1}
	ztf_heat = ztf.find(
		filter_query,
		ztf_query)

	df = pd.DataFrame(ztf_heat, columns=(xaxis_column_name, yaxis_column_name))

	fig = px.density_heatmap(df, x = xaxis_column_name, y = yaxis_column_name,
							nbinsx = 25, nbinsy = 25, text_auto = True)

	fig.update_xaxes(title=xaxis_column_name)
	fig.update_yaxes(title=yaxis_column_name)

	updateLayout(fig)
	return fig

# Login functionality
@app.callback(
	[Output('create_user', "children")],
	[Input('signup_button', 'n_clicks')],
	[State('username', 'value'), State('password', 'value'), State('confirmpassword', 'value'), State('email', 'value')],
	prevent_initial_call=True,
)
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


@app.callback(
	Output('save-output', 'children'),
	Input('save-button', 'n_clicks'),
	State('url', 'hash')
)
def save_asteroid(n_clicks, hash):
	if(n_clicks > 0):
		if(current_user.is_authenticated):
			un = current_user.username
			hash = hash.replace("#", "")

			already_exists = select(UserData_tbl.c.id).where((UserData_tbl.c.username) == un).where((UserData_tbl.c.asteroid_id) == hash)
			connection = user_data_engine.connect()
			already_exists_result = connection.execute(already_exists)
			check_result = already_exists_result.first()

			if(check_result is None):
				ins = UserData_tbl.insert().values(username=un, asteroid_id=hash)

				# Insert the new user into the database
				connection.execute(ins)

				# Close the connection to the database
				connection.close()

				# Return to the home page
				return (html.H2('Asteroid Saved!'))

			else:
				return [html.Br(), dbc.Alert("You already have this asteroid saved!", color='info')]
		else:
			return [html.Br(), dbc.Alert('You must be logged in to save asteroids!', color="danger")]


##########################################################################################################
#   This function uses the input username to query the database for all asteroids that correspond to it
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

	if(n_clicks > 0):
		# Query that elects the asteroid_id column values where the username column values match the inputted
		# username
		un = current_user.username
		query = select(UserData_tbl.c.asteroid_id).where(UserData_tbl.c.username == un)

		# Connect to the database
		with user_data_engine.connect() as connection:

			# Try to
			try:
				# Execute the query
				result = connection.execute(query)

			# There was an error
			except Exception as e:
					print(e)

			# The query executed
			else:

				# Create a list for the JSON data that needs to be passed into the dataframe
				json_list = []

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
					json_list.append(jsonString.replace("[", "").replace("]", "").replace('"', ""))
				# Disconnect from the database
				result.close()

				# Use numpy to put the JSON data into an Array
				clean_up = np.array(json_list)

				# Create a list for the asteroid links
				link_array = []

				# Loop through each value in the Array
				for value in clean_up:

					# reformat the value to be an HTML link using an f string with HTML code and the value
					value = f"<a href='/snaps-dev/asteroid#{value}'>{value}</a>"

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
				data_array = df.to_dict('records')

				# Return a Dash Datatable with the data centered
				return dt.DataTable(data=data_array, columns=columns, style_header={'textAlign': 'center'}, style_table={'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'}, style_data={'paddingLeft': '25px', 'paddingTop': '20px'}, markdown_options={"html": True})


# Callback for logging in
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
				return dcc.Location(pathname="/snaps-dev/account", id="account-link")
			# If one, or both, password(s) do not match
			else:
				# Print the error
				return [html.Br(), dbc.Alert('Incorrect Password', color="danger")]

		# If the username does not exist
		else:
			# Print the Error
			return [html.Br(), dbc.Alert('Incorrect Username', color="danger")]


# Callback for logout
@app.callback(
	Output('url_logout', 'children'), [Input('logout_button', 'n_clicks')])
def logout_of_account(n_clicks):
	if n_clicks > 0:
		logout_user()
		return dcc.Location(pathname="/snaps-dev/", id="home-link")


if __name__ == '__main__':
	app.run_server(host='127.0.0.1', port=8050, debug=True)
