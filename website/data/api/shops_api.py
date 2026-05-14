import datetime

import requests
from flask_restful import Resource, reqparse, abort
from flask import jsonify, request
from flask_login import current_user, login_required

from datetime import date

from website.data.products import Products
from website.data.shops import Shops
from website.data import db_session
from website.bucket_requests import delete_by_key


parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('name', required=True)
parser_post_args.add_argument('imgs', default='shops/imgs/shop_img_default.jpg')
parser_post_args.add_argument('logo', default='shops/logos/default_logo.svg')
parser_post_args.add_argument('address', required=True)
parser_post_args.add_argument('rate', type=float, default=0)
parser_post_args.add_argument('description')
parser_post_args.add_argument('timetable', type=dict)
parser_post_args.add_argument('coords', required=True)
parser_post_args.add_argument('delivery_radius', type=int, default=3000)

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('name')
parser_patch_args.add_argument('imgs')
parser_patch_args.add_argument('logo')
parser_patch_args.add_argument('address')
parser_patch_args.add_argument('rate', type=float)
parser_patch_args.add_argument('description')
parser_patch_args.add_argument('timetable', type=dict)
parser_patch_args.add_argument('coords')
parser_patch_args.add_argument('delivery_radius', type=int)


def abort_if_shop_not_found(shop_id: int):
    with db_session.create_session() as sess:
        shop = sess.get(Shops, shop_id)

    if not shop:
        abort(404, message=f'Shop with id {shop_id} not found')
    return shop


def is_shop_owner_or_admin(shop: Shops):
    """Проверка, что текущий пользователь владелец магазина или админ"""
    if current_user.id != shop.user_id and current_user.role != 'admin':
        abort(403, message='Access denied: you can only access your own shop')


class ShopsResource(Resource):
    def get(self, shop_id: int):
        shop = abort_if_shop_not_found(shop_id)

        return jsonify(
            {
                'shop': shop.to_dict(
                    only=('id', 'name', 'imgs', 'address', 'rate', 'description', 'delivery_radius',
                          'timetable', 'coords', 'created_date', 'user_id', 'logo', 'updated_date')
                )
            }
        )

    @login_required
    def delete(self, shop_id: int):
        shop = abort_if_shop_not_found(shop_id)
        is_shop_owner_or_admin(shop)

        shop_imgs = shop.imgs
        for img in shop_imgs.split(','):
            if img != 'shops/imgs/shop_img_default.jpg':
                delete_by_key(img)
                print('deleted', img)

        if shop.logo != 'shops/logos/default_logo.svg':
            delete_by_key(shop.logo)
            print('deleted logo')

        with db_session.create_session() as sess:
            products = sess.query(Products).filter(Products.shop_id == shop_id)

            print('product')
            for product in products:
                api_url = '127.0.0.1:5000' + f'api/products/{product.id}'
                requests.delete(api_url, cookies=request.cookies, verify=False, allow_redirects=True)

            sess.delete(shop)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )

    @login_required
    def patch(self, shop_id: int):
        shop = abort_if_shop_not_found(shop_id)
        is_shop_owner_or_admin(shop)

        args = parser_patch_args.parse_args()

        with db_session.create_session() as sess:
            for key, value in args.items():
                if key == 'imgs' and value is not None and value.strip() == '':
                    value = 'shops/imgs/shop_img_default.jpg'

                if key == 'logo' and value is not None and value.strip() == '':
                    value = 'shops/logos/default_logo.svg'

                if value is not None:
                    setattr(shop, key, value)

            shop.updated_date = datetime.datetime.now()

            sess.add(shop)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )


class ShopsListResource(Resource):
    def get(self):
        with db_session.create_session() as sess:
            shops = sess.query(Shops).all()
        return jsonify(
            {
                'shops':
                    [
                        item.to_dict(
                            only=('id', 'name', 'imgs', 'address', 'rate', 'description', 'delivery_radius',
                                  'timetable', 'coords', 'user_id', 'created_date', 'logo', 'updated_date')
                        )
                        for item in shops
                    ]
            }
        )

    @login_required
    def post(self):
        if current_user.role != 'shop':
            abort(403, message='Only users with shop role can create a shop')

        args = parser_post_args.parse_args()
        shop_id = None

        with db_session.create_session() as sess:
            shop = Shops(
                name=args['name'],
                imgs=args['imgs'],
                logo=args['logo'],
                address=args['address'],
                rate=args['rate'],
                user_id=current_user.id,
                description=args['description'],
                timetable=args['timetable'],
                coords=args['coords'],
                created_date=date.today(),
                updated_date = datetime.datetime.now(),
                delivery_radius=args['delivery_radius']
            )
            sess.add(shop)
            sess.commit()

            shop_id = shop.id

        return jsonify(
            {
                'id': shop_id
            }
        )