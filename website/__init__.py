from flask import Flask
from flask_restful import Api

from website.config import SECRET_KEY, DATABASE_URL
from website.data import db_session
from website.data.api import users_api, shops_api, products_api, orders_api, order_items_api, reviews_shop_api, reviews_product_api


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

    api = Api(app)
    api.add_resource(users_api.UsersResource, '/api/users/<int:user_id>')
    api.add_resource(users_api.UsersListResource, '/api/users/')
    api.add_resource(shops_api.ShopsResource, '/api/shops/<int:shop_id>')
    api.add_resource(shops_api.ShopsListResource, '/api/shops/')
    api.add_resource(products_api.ProductsResource, '/api/products/<int:product_id>')
    api.add_resource(products_api.ProductsListResource, '/api/products/')
    api.add_resource(orders_api.OrdersResource, '/api/orders/<int:order_id>')
    api.add_resource(orders_api.OrdersListResource, '/api/orders/')
    api.add_resource(order_items_api.OrderItemsResource, '/api/order_items/<int:order_item_id>')
    api.add_resource(order_items_api.OrderItemsListResource, '/api/order_items/')
    api.add_resource(reviews_shop_api.ReviewsShopResource, '/api/reviews_shop/<int:review_shop_id>')
    api.add_resource(reviews_shop_api.ReviewsShopListResource, '/api/reviews_shop/')
    api.add_resource(reviews_product_api.ReviewsProductResource, '/api/reviews_product/<int:review_product_id>')
    api.add_resource(reviews_product_api.ReviewsProductListResource, '/api/reviews_product/')

    # инициализируем базу данных
    db_session.global_init(app.config['SQLALCHEMY_DATABASE_URI'])

    return app