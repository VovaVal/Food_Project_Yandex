from flask import Flask
from flask_restful import Api

from website.config import SECRET_KEY, DATABASE_URL
from website.data import db_session
from website.data.api import users_api, shops_api


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

    api = Api(app)
    api.add_resource(users_api.UsersResource, '/api/users/<int:user_id>')
    api.add_resource(users_api.UsersListResource, '/api/users/')
    api.add_resource(shops_api.ShopsResource, '/api/shops/<int:shop_id>')
    api.add_resource(shops_api.ShopsListResource, '/api/shops/')

    # инициализируем базу данных
    db_session.global_init(app.config['SQLALCHEMY_DATABASE_URI'])

    return app