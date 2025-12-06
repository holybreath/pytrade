from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from app import routes, models

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['ALLOW_REGISTRATION'] = True

db = SQLAlchemy(app)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


# 导入模型，确保 SQLAlchemy 认识表结构


# 如果数据库不存在，则初始化表结构
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'db.sqlite3')
if not os.path.exists(db_path):
    with app.app_context():
        db.create_all()
        print("Database created successfully!")

# 注册路由
from app import routes

