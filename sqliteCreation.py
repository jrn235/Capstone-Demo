from sqlalchemy import Table, create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import select
from sqlalchemy.orm import Session
from flask_sqlalchemy import SQLAlchemy

# Create the userData SQLite database file
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


# Create the users SQLite database file
users_engine = create_engine('sqlite:///users.sqlite')
users_db = SQLAlchemy()

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