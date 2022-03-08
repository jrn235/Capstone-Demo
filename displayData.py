import sqlite3
from sqlalchemy import Table, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import select
from flask_sqlalchemy import SQLAlchemy
import dash
from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import json
from dash import dash_table as dt
import pandas as pd
import numpy as np

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY], prevent_initial_callbacks=True)
server = app.server
app.config.suppress_callback_exceptions = True

CONTENT_STYLE = {
    'padding': '2rem 1rem',
}

content = html.Div([
            html.H1('Select Username Data'),
            dcc.Location(id='user_name', refresh=True),
            dcc.Input(id="username", type="text", placeholder="username", maxLength=15),
            html.Button('Select Data', id='select_button', n_clicks=0),
            html.Br(),
            html.Br(),
            html.Label(id='name', htmlFor='selection'),
            html.Div(id='selection')
            
])


      
   
            
           
    

app.layout = html.Div([
    dcc.Location(id="url"),
    content
    
    ], 

    style=CONTENT_STYLE
    )
    

@app.callback(
    Output('name', 'children'),
    [Input('select_button', 'n_clicks')],
    [State('username', 'value')])
def send_username(n_clicks, un):
    return un + "'s data:"




@app.callback(
    Output('selection', 'children'),
    [Input('select_button', 'n_clicks')],
    [State('username', 'value')])
def displayUserData(n_clicks, un):
    query = select(UserData_tbl.c.ssnamr).where(UserData_tbl.c.username == un)

    with engine.connect() as connection:
        try:
            result = connection.execute(query)
        except Exception as e:
                print(e)
        else:
 
            json_list = []
            for row in result:
                row_list = []
                row_data = (row[0])
                row_list.append(row_data.replace("[", "").replace("]", ""))

                jsonString = json.dumps(row_list)
                json_list.append(jsonString.replace("[", "").replace("]", "").replace('"', ""))

            result.close()
            
            clean_up = np.array(json_list)
            link_array = []

            for value in clean_up:
            	#value = f"<a href='/asteroid#{value}'>{value}</a>"
            	value = f"<a href='/asteroid#{value}'>{value}</a>"
            	link_array.append(value)

            df = pd.DataFrame(link_array)
            df.columns = ['SSNAMR']

            columns = [{"name": i, "id": i, "presentation": "markdown"} for i in df.columns]

            data_array = df.to_dict('records')

            return dt.DataTable(data=data_array, columns=columns, style_header={'textAlign': 'center'}, style_table={'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'}, style_data={'paddingLeft': '25px', 'paddingTop': '20px'}, markdown_options={"html": True})


user_con = sqlite3.connect('userData.sqlite')
engine = create_engine('sqlite:///userData.sqlite')
db = SQLAlchemy()

class UserData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=False, nullable=False)
    ssnamr = db.Column(db.String(50), unique=False)
UserData_tbl = Table('user_data', UserData.metadata)

def create_userData_table():
    UserData.metadata.create_all(engine)
# Create the table
create_userData_table()

def insertData(un, a_name):
    ins = UserData_tbl.insert().values(username=un, ssnamr=a_name)
    conn = engine.connect()
    conn.execute(ins)
    conn.close()





def main():
    #insertData('jakob', '13hjci')
    #insertData('carson', '3fjkf83')
    #insertData('john', 'fhr8e')
    #insertData('jakob', '3fjkf83')
    #insertData('carson', '13hjci')


    displayUserData('jakob')
   

if __name__ == '__main__':
    #main()
    app.run_server(debug=True, port=8051)


