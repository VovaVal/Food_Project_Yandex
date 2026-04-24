from flask_restful import Resource, reqparse, abort
from flask import jsonify

from werkzeug.security import generate_password_hash
from datetime import date

from website.data.shops import Shops
from website.data import db_session


parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('name', required=True)
parser_post_args.add_argument('imgs', default='website/static/imgs/shop_img_default.jpg')
parser_post_args.add_argument('email', required=True)
parser_post_args.add_argument('address', required=True)
parser_post_args.add_argument('password', required=True)
parser_post_args.add_argument('rate', type=int, default=0)
parser_post_args.add_argument('description')
parser_post_args.add_argument('timetable')
parser_post_args.add_argument('coords', required=True)

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('name')
parser_patch_args.add_argument('imgs')
parser_patch_args.add_argument('email')
parser_patch_args.add_argument('address')
parser_patch_args.add_argument('password')
parser_patch_args.add_argument('rate', type=int)
parser_patch_args.add_argument('description')
parser_patch_args.add_argument('timetable')
parser_patch_args.add_argument('coords')


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
                          'timetable', 'coords', 'email', 'hashed_password', 'created_date')
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
                if key == 'password' and value is not None:
                    key = 'hashed_password'
                    value = generate_password_hash(value)

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
                                  'timetable', 'coords', 'email', 'hashed_password', 'created_date')
                        )
                        for item in shops
                    ]
            }
        )

    def post(self):
        args = parser_post_args.parse_args()
        hashed_password = generate_password_hash(args['password'])
        shop_id = None

        with db_session.create_session() as sess:
            shop_exist = sess.query(Shops).filter(Shops.email == args['email']).first()
            if shop_exist:
                abort(400, message=f'Shop with email {args['email']} already exists')

            shop = Shops(
                name=args['name'],
                imgs=args['imgs'],
                email=args['email'],
                address=args['address'],
                rate=args['rate'],
                description=args['description'],
                timetable=args['timetable'],
                coords=args['coords'],
                hashed_password=hashed_password,
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