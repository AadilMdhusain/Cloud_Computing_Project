from flask import Flask, request, jsonify, render_template
import os
from extensions import db
from models.user import User

def create_app():
	app = Flask(__name__)

	app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/userdb')
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

	db.init_app(app)

	with app.app_context():
		db.create_all()
	
	return app
 
app = create_app()

@app.route('/')
def home():
	return "User service is running!!"

@app.route('/register', methods=['GET'])
def register_form():
	return render_template('register.html')

@app.route('/register', methods=['POST'])
def register_user():
	name = request.form.get('name')
	email = request.form.get('email')
	password = request.form.get('password')
	role = request.form.get('role')

	existing_user = User.query.filter_by(email=email).first()
	if existing_user:
		return "Email already exists"

	user = User(name=name, email=email, password_hash=password, role=role)
	db.session.add(user)
	db.session.commit()

	return "Registration Successful!!"


if __name__ == "__main__":
	app.run(host="0.0.0.0", port=5000)


