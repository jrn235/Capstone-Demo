# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
from dash import dcc
from  dash import html
import plotly.express as px
import pandas as pd
import base64

app = dash.Dash(__name__)
app.title = "Team First Light Demo"

# assume you have a "long-form" data frame
# see https://plotly.com/python/px-arguments/ for more options
Graphs = html.Div(children = [
html.Div(children = ["Original Characteristics", dcc.Graph()], #dash graph element
style = {'width': '45%', "position": "static", "left": "2%",
         'display': 'inline-block', 'text-align': 'center',
         'top': '10%', 'height':'50%', 'margin-top': '40px', 
         'margin-left': '50px', 'color': 'white'
         }
        ),
html.Div(children = ["Derived Characteristics", dcc.Graph()], #dash graph element
style = {'width': '45%', 'position': 'static', 'left': '53%',
         'display': 'inline-block', 'text-align': 'center',
         'top': '10%', 'height':'50%', 'margin-top': '40px', 
         'margin-left': '30px', 'color': 'white'
        }
        )
                    ])

Links = html.Div(children = [
    html.Div(children = ['''Here are some useful links'''],
    style = {'text-align':'center', 'color' : 'white', 'margin-top': '40px' }
        )
    

    ])

test_png = 'vera.png'
test_base64 = base64.b64encode(open(test_png, 'rb').read()).decode('ascii')

Main = html.Div([
    html.Div(html.Img(src='data:image/png;base64,{}'.format(test_base64))),
    html.Div('''Vera C. Rubin Observatory views a 9.62 square-degree patch of sky, more than 40 times the area of the full moon. ''')

    ],
    style = {'width': '40%', 'position': 'relative', 'left': '53%',
         'display': 'inline-block', 'text-align': 'center',
         'top': '10%', 'height':'10%', 'margin-top': '40px', 
         'color': 'white'
        }
    )

Tabs  = html.Nav(children=[
            dcc.Tabs([
                dcc.Tab(label='Main', children=[Main]),
                dcc.Tab(label='Account', children=[]),
                dcc.Tab(label='Graphs', children=[Graphs]),
                dcc.Tab(label='Links', children=[Links]),
                dcc.Tab(label='Documentation', children=[]),
                    ])

            

                    ],
                style = {'background': '#1C1646', 'border': '2px white'}
                )

Heading  = html.H1(children=['Team First Light'],
style = {'background-color': '#1C1646', 'border': '2px white','color': ' white','text-align': 'center'}
    )

Description  =  html.Div(children=['''
        This GUI visualizes large amounts of astronomical data.
    '''],
style = {'background-color': '#1C1646', 'border': '2px white','color': ' white', 'text-align': 'center',
            'margin-bottom': '20px'}
    )


app.layout = html.Div(id='main_div', children=[Heading, Description, Tabs],

style = {'background-color': '#1C1646', 'padding':'0',           
         'width':'100%', 'height':'100%', 'position': 'fixed',
         'top': '0%', 'left': '0%', 'bottom': '0%', 'height':'100%'}
)

if __name__ == '__main__':
    app.run_server(debug=False)
