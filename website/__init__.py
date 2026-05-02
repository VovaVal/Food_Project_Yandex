from flask import Flask, request, jsonify, render_template
from flask_restful import Api
from flask_login import LoginManager
from werkzeug.exceptions import HTTPException

from website.config import SECRET_KEY, DATABASE_URL, BUCKET_NAME, BUCKET_CLIENT
from website.data import db_session
from website.data.api import users_api, shops_api, products_api, orders_api, order_items_api, reviews_shop_api, reviews_product_api, auth_api
from website.data.users import User


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    app.config['BUCKET_NAME'] = BUCKET_NAME
    app.config['BUCKET_CLIENT'] = BUCKET_CLIENT

    # инициализируем базу данных
    db_session.global_init(app.config['SQLALCHEMY_DATABASE_URI'])

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему'

    @login_manager.user_loader
    def load_user(user_id):
        with db_session.create_session() as sess:
            user = sess.get(User, user_id)
        return user

    from website.routes.auth import auth_bp
    from website.routes.common_routes import bp_common
    from website.routes.customers import customer_bp
    from website.routes.shops import shop_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(bp_common)
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(shop_bp, url_prefix='/shop')

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
    api.add_resource(auth_api.LoginResource, '/api/login/')
    api.add_resource(auth_api.LogoutResource, '/api/logout/')
    api.add_resource(auth_api.CurrentUserResource, '/api/current_user/')

    # 404 - Страница не найдена
    @app.errorhandler(404)
    def not_found_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found'}), 404
        return render_template('errors/error.html', title='Ошибка',
                               error_code=404, error_message='Resource not found'), 404

    # 403 - Доступ запрещён
    @app.errorhandler(403)
    def forbidden_error(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Access forbidden'}), 403
        return render_template('errors/error.html', title='Ошибка',
                               error_code=403, error_message='Access forbidden'), 403

    # 500 - Внутренняя ошибка сервера
    @app.errorhandler(500)
    def internal_error(error):
        # Логируем ошибку для отладки
        app.logger.error(f'Server Error: {error}')
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/error.html', title='Ошибка',
                               error_code=500, error_message='Internal server error'), 500

    # Перехват всех HTTP исключений
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': error.description}), error.code
        return render_template(f'errors/error.html', title='Ошибка',
                               error_code=error.code, error_message=error.description), error.code

    # Перехват любых других исключений
    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f'Unhandled Exception: {error}')
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Something went wrong'}), 500
        return render_template('errors/error.html', title='Ошибка',
                               error_code=500, error_message='Something went wrong'), 500

    return app