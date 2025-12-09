from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['ALLOW_REGISTRATION'] = False
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

from app import routes, models
from app.models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    # Create a default user if one doesn't exist
    if not User.query.filter_by(username='tivon').first():
        hashed_password = generate_password_hash('yp627', method='pbkdf2:sha256')
        new_user = User(username='tivon', password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
