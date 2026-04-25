from flask_restful import Resource, reqparse, abort
from flask import jsonify
from flask_login import current_user, login_required

from website.data.products import Products
from website.data import db_session
from website.data.shops import Shops


parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('name', required=True)
parser_post_args.add_argument('shop_id', type=int, required=True)
parser_post_args.add_argument('imgs', default='website/static/imgs/product_img_default.png')
parser_post_args.add_argument('quantity', type=int, default=0)
parser_post_args.add_argument('rate', type=float, default=0)
parser_post_args.add_argument('price', type=int, required=True)
parser_post_args.add_argument('description')
parser_post_args.add_argument('product_type', choices=['drink', 'bakery', 'dessert', 'other'], default='other',
                              help='Allowed product types: "drink", "bakery", "dessert" and "other"')

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('name')
parser_patch_args.add_argument('shop_id', type=int)
parser_patch_args.add_argument('imgs')
parser_patch_args.add_argument('quantity', type=int)
parser_patch_args.add_argument('rate', type=float)
parser_patch_args.add_argument('price', type=int)
parser_patch_args.add_argument('description')
parser_patch_args.add_argument('product_type', choices=['drink', 'bakery', 'dessert', 'other'],
                               help='Allowed product types: "drink", "bakery", "dessert" and "other"')


def abort_if_product_not_found(product_id: int):
    with db_session.create_session() as sess:
        product = sess.get(Products, product_id)

    if not product:
        abort(404, message=f'Product with id {product_id} not found')
    return product


def is_shop_owner(shop: Shops):
    if current_user.id != shop.user_id and current_user.role != 'admin':
        abort(403, message='Access denied: you can only delete/add/edit products from your own shop')


class ProductsResource(Resource):
    def get(self, product_id: int):
        product = abort_if_product_not_found(product_id)
        return jsonify(
            {
                'product': product.to_dict(
                    only=('id', 'name', 'imgs', 'shop_id', 'rate', 'description',
                          'quantity', 'price', 'product_type')
                )
            }
        )

    @login_required
    def delete(self, product_id: int):
        product = abort_if_product_not_found(product_id)

        with db_session.create_session() as sess:
            shop = sess.get(Shops, product.shop_id)
            is_shop_owner(shop)

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
        args = parser_patch_args.parse_args()

        with db_session.create_session() as sess:
            shop = sess.get(Shops, product.shop_id)
            is_shop_owner(shop)

            for key, value in args.items():
                if key == 'shop_id' and value is not None:
                    shop = sess.get(Shops, args['shop_id'])
                    if not shop:
                        abort(404, message=f'Shop with id {args["shop_id"]} not found')

                    is_shop_owner(shop)

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
                                  'quantity', 'price', 'product_type')
                        )
                        for item in products
                    ]
            }
        )

    @login_required
    def post(self):
        if current_user.role != 'shop':
            abort(403, message='Only shops can create products')

        args = parser_post_args.parse_args()
        product_id = None

        with db_session.create_session() as sess:
            shop = sess.get(Shops, args['shop_id'])
            if not shop:
                abort(404, message=f'Shop with id {args["shop_id"]} not found')

            is_shop_owner(shop)

            product = Products(
                name=args['name'],
                imgs=args['imgs'],
                quantity=args['quantity'],
                price=args['price'],
                rate=args['rate'],
                description=args['description'],
                product_type=args['product_type'],
                shop_id=args['shop_id']
            )
            sess.add(product)
            sess.commit()

            product_id = product.id

        return jsonify(
            {
                'id': product_id
            }
        )