from flask_restful import Resource, reqparse, abort
from flask import jsonify
from flask_login import current_user, login_required

from website.bucket_requests import delete_by_key
from website.data.products import Products
from website.data import db_session
from website.data.shops import Shops


parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('name', required=True)
parser_post_args.add_argument('shop_id', type=int, required=True)
parser_post_args.add_argument('imgs', default='products/imgs/product_img_default.png')
parser_post_args.add_argument('quantity', type=int, default=0)
parser_post_args.add_argument('rate', type=float, default=0)
parser_post_args.add_argument('price', type=int, required=True)
parser_post_args.add_argument('product_weight', type=float, required=True)
parser_post_args.add_argument('description')
parser_post_args.add_argument('product_type', choices=['drink', 'bakery', 'dessert', 'other'], default='other',
                              help='Allowed product types: "drink", "bakery", "dessert" and "other"')
parser_post_args.add_argument('type_of_count', choices=['kg', 'g', 'l', 'ml'], default='g',
                              help='Allowed product types of count: "kg", "g", "l" and "ml"')

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('name')
parser_patch_args.add_argument('shop_id', type=int)
parser_patch_args.add_argument('imgs')
parser_patch_args.add_argument('quantity', type=int)
parser_patch_args.add_argument('rate', type=float)
parser_patch_args.add_argument('price', type=int)
parser_patch_args.add_argument('product_weight', type=float)
parser_patch_args.add_argument('description')
parser_patch_args.add_argument('product_type', choices=['drink', 'bakery', 'dessert', 'other'],
                               help='Allowed product types: "drink", "bakery", "dessert" and "other"')
parser_patch_args.add_argument('type_of_count', choices=['kg', 'g', 'l', 'ml'],
                              help='Allowed product types of count: "kg", "g", "l" and "ml"')


def abort_if_product_not_found(product_id: int):
    with db_session.create_session() as sess:
        product = sess.get(Products, product_id)

    if not product:
        abort(404, message=f'Product with id {product_id} not found')
    return product


def check_shop_ownership(shop_id: int):
    """Проверка, что текущий пользователь владеет магазином или админ"""
    with db_session.create_session() as sess:
        shop = sess.get(Shops, shop_id)
        if not shop:
            abort(404, message=f'Shop with id {shop_id} not found')
        if current_user.id != shop.user_id and current_user.role != 'admin':
            abort(403, message='Access denied: you can only manage products from your own shop')
        return shop


class ProductsResource(Resource):
    def get(self, product_id: int):
        product = abort_if_product_not_found(product_id)
        return jsonify(
            {
                'product': product.to_dict(
                    only=('id', 'name', 'imgs', 'shop_id', 'rate', 'description',
                          'quantity', 'price', 'product_type', 'product_weight', 'type_of_count')
                )
            }
        )

    @login_required
    def delete(self, product_id: int):
        product = abort_if_product_not_found(product_id)
        check_shop_ownership(product.shop_id)

        with db_session.create_session() as sess:
            product_imgs = product.imgs

            if product_imgs and product_imgs != None:
                for img in product_imgs.split(','):
                    if img != 'products/imgs/product_img_default.png':
                        delete_by_key(img)

            sess.delete(product)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )

    @login_required
    def patch(self, product_id: int):
        product = abort_if_product_not_found(product_id)
        check_shop_ownership(product.shop_id)

        args = parser_patch_args.parse_args()

        if args.get('quantity') is not None and args['quantity'] < 0:
            abort(400, message='Quantity cannot be negative')
        if args.get('price') is not None and args['price'] < 0:
            abort(400, message='Price cannot be negative')
        if args.get('rate') is not None and (args['rate'] < 0 or args['rate'] > 5):
            abort(400, message='Rate cannot be negative or more than 5')

        with db_session.create_session() as sess:
            for key, value in args.items():
                if key == 'shop_id' and value is not None and args['shop_id'] != product.shop_id:
                    check_shop_ownership(args['shop_id'])

                if key == 'imgs' and value is not None and value.strip() == '':
                    value = 'products/imgs/product_img_default.png'

                if value is not None:
                    setattr(product, key, value)

            sess.add(product)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )


class ProductsListResource(Resource):
    def get(self):
        with db_session.create_session() as sess:
            products = sess.query(Products).all()
        return jsonify(
            {
                'products':
                    [
                        item.to_dict(
                            only=('id', 'name', 'imgs', 'shop_id', 'rate', 'description',
                                  'quantity', 'price', 'product_type', 'product_weight', 'type_of_count')
                        )
                        for item in products
                    ]
            }
        )

    @login_required
    def post(self):
        if current_user.role == 'customer':
            abort(403, message='Only shops can create products')

        args = parser_post_args.parse_args()
        product_id = None

        if args.get('quantity') is not None and args['quantity'] < 0:
            abort(400, message='Quantity cannot be negative')
        if args.get('price') is not None and args['price'] < 0:
            abort(400, message='Price cannot be negative')
        if args.get('rate') is not None and (args['rate'] < 0 or args['rate'] > 5):
            abort(400, message='Rate cannot be negative or more than 5')

        with db_session.create_session() as sess:
            check_shop_ownership(args['shop_id'])

            product = Products(
                name=args['name'],
                imgs=args['imgs'],
                quantity=args['quantity'],
                price=args['price'],
                rate=args['rate'],
                description=args['description'],
                product_type=args['product_type'],
                shop_id=args['shop_id'],
                product_weight=args['product_weight'],
                type_of_count=args['type_of_count']
            )
            sess.add(product)
            sess.commit()

            product_id = product.id

        return jsonify(
            {
                'id': product_id
            }
        )