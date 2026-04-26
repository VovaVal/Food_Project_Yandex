from flask_restful import Resource, reqparse, abort
from flask import jsonify
from flask_login import current_user, login_required

from datetime import date

from website.data.shops import Shops
from website.data import db_session


parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('name', required=True)
parser_post_args.add_argument('imgs', default='website/static/imgs/shop_img_default.jpg')
parser_post_args.add_argument('address', required=True)
parser_post_args.add_argument('rate', type=float, default=0)
parser_post_args.add_argument('description')
parser_post_args.add_argument('timetable')
parser_post_args.add_argument('coords', required=True)

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('name')
parser_patch_args.add_argument('imgs')
parser_patch_args.add_argument('address')
parser_patch_args.add_argument('rate', type=float)
parser_patch_args.add_argument('description')
parser_patch_args.add_argument('timetable')
parser_patch_args.add_argument('coords')


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
                    only=('id', 'name', 'imgs', 'address', 'rate', 'description',
                          'timetable', 'coords', 'created_date', 'user_id')
                )
            }
        )

    @login_required
    def delete(self, shop_id: int):
        shop = abort_if_shop_not_found(shop_id)
        is_shop_owner_or_admin(shop)

        with db_session.create_session() as sess:
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
                if value is not None:
                    setattr(shop, key, value)

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
                            only=('id', 'name', 'imgs', 'address', 'rate', 'description',
                                  'timetable', 'coords', 'user_id', 'created_date')
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
                address=args['address'],
                rate=args['rate'],
                user_id=current_user.id,
                description=args['description'],
                timetable=args['timetable'],
                coords=args['coords'],
                created_date=date.today()
            )
            sess.add(shop)
            sess.commit()

            shop_id = shop.id

        return jsonify(
            {
                'id': shop_id
            }
        )