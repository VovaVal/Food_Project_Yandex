from flask_restful import Resource, reqparse, abort
from flask import jsonify

from datetime import date

from website.data.shops import Shops
from website.data import db_session
from website.data.users import User

parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('name', required=True)
parser_post_args.add_argument('imgs', default='website/static/imgs/shop_img_default.jpg')
parser_post_args.add_argument('address', required=True)
parser_post_args.add_argument('rate', type=float, default=0)
parser_post_args.add_argument('description')
parser_post_args.add_argument('timetable')
parser_post_args.add_argument('coords', required=True)
parser_post_args.add_argument('user_id', type=int, required=True)

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('name')
parser_patch_args.add_argument('imgs')
parser_patch_args.add_argument('address')
parser_patch_args.add_argument('rate', type=float)
parser_patch_args.add_argument('description')
parser_patch_args.add_argument('timetable')
parser_patch_args.add_argument('coords')
parser_patch_args.add_argument('user_id', type=int)


def abort_if_shop_not_found(shop_id: int):
    with db_session.create_session() as sess:
        shop = sess.get(Shops, shop_id)

    if not shop:
        abort(404, message=f'Shop with id {shop_id} not found')
    return shop


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

    def delete(self, shop_id: int):
        shop = abort_if_shop_not_found(shop_id)

        with db_session.create_session() as sess:
            sess.delete(shop)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )

    def patch(self, shop_id: int):
        shop = abort_if_shop_not_found(shop_id)
        args = parser_patch_args.parse_args()

        with db_session.create_session() as sess:
            for key, value in args.items():
                if key == 'user_id' and value is not None:
                    user = sess.get(User, value)
                    if not user:
                        abort(404, message=f'User with id {args["user_id"]} not found')

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

    def post(self):
        args = parser_post_args.parse_args()
        shop_id = None

        with db_session.create_session() as sess:
            user = sess.get(User, args['user_id'])
            if not user:
                abort(404, message=f'User with id {args["user_id"]} not found')

            shop = Shops(
                name=args['name'],
                imgs=args['imgs'],
                address=args['address'],
                rate=args['rate'],
                user_id=args['user_id'],
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