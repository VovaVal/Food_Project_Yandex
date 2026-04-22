from flask import Flask

from website.config import SECRET_KEY, DATABASE_URL
from website.data import db_session


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

    db_session.global_init(app.config['SQLALCHEMY_DATABASE_URI'])

    return app