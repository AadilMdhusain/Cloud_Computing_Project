from flask_sqlalchemy import SQLAlchemy
from extensions import db


class User(db.Model) :
	__tablename__ = 'users'

	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100), nullable=False)
	email = db.Column(db.String(120), unique=True, nullable=False)
	password_hash = db.Column(db.String(128), nullable=False)
	role = db.Column(db.String(20), nullable=False)

	def __repr__(self):
		return f"<User {self.name}>"
