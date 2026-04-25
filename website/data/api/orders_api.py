from flask_restful import Resource, reqparse, abort
from flask import jsonify

from website.data import db_session
from website.data.orders import Orders
from website.data.shops import Shops
from website.data.users import User


parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('user_id', type=int, required=True)
parser_post_args.add_argument('shop_id', type=int, required=True)
parser_post_args.add_argument('description')
parser_post_args.add_argument('total_amount', type=int, required=True)
parser_post_args.add_argument('price', type=int, required=True)
parser_post_args.add_argument('delivery_type', choices=['pickup', 'delivery'], default='pickup',
                              help='Allowed delivery types: "pickup" and "delivery"')
parser_post_args.add_argument('status', choices=['active', 'finished'], default='active',
                              help='Allowed status types: "active" and "finished"')
parser_post_args.add_argument('type_of_payment', choices=['cash', 'card', 'bonus'], default='cash',
                              help='Allowed payment types: "cash", "card" and "bonus"')
parser_post_args.add_argument('address', required=True)
parser_post_args.add_argument('coords', required=True)

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('user_id', type=int)
parser_patch_args.add_argument('shop_id', type=int)
parser_patch_args.add_argument('description')
parser_patch_args.add_argument('total_amount', type=int)
parser_patch_args.add_argument('price', type=int)
parser_patch_args.add_argument('delivery_type', choices=['pickup', 'delivery'],
                               help='Allowed delivery types: "pickup" and "delivery"')
parser_patch_args.add_argument('status', choices=['active', 'finished'],
                               help='Allowed status types: "active" and "finished"')
parser_patch_args.add_argument('type_of_payment', choices=['cash', 'card', 'bonus'],
                              help='Allowed payment types: "cash", "card" and "bonus"')
parser_patch_args.add_argument('address')
parser_patch_args.add_argument('coords')



def abort_if_order_not_found(order_id: int):
    with db_session.create_session() as sess:
        order = sess.get(Orders, order_id)

    if not order:
        abort(404, message=f'Order with id {order_id} not found')
    return order


class OrdersResource(Resource):
    def get(self, order_id: int):
        order = abort_if_order_not_found(order_id)
        return jsonify(
            {
                'order': order.to_dict(
                    only=('id', 'user_id', 'shop_id', 'total_amount', 'status', 'description',
                          'created_date', 'price', 'delivery_type', 'type_of_payment', 'address', 'coords')
                )
            }
        )

    def delete(self, order_id: int):
        order = abort_if_order_not_found(order_id)

        with db_session.create_session() as sess:
            sess.delete(order)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )

    def patch(self, order_id: int):
        order = abort_if_order_not_found(order_id)
        args = parser_patch_args.parse_args()

        with db_session.create_session() as sess:
            for key, value in args.items():
                if key == 'shop_id' and value is not None:
                    shop = sess.get(Shops, args['shop_id'])
                    if not shop:
                        abort(404, message=f'Shop with id {args["shop_id"]} not found')

                if key == 'user_id' and value is not None:
                    user = sess.get(User, args['user_id'])
                    if not user:
                        abort(404, message=f'User with id {args["user_id"]} not found')

                if value is not None:
                    setattr(order, key, value)

            sess.add(order)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )


class OrdersListResource(Resource):
    def get(self):
        with db_session.create_session() as sess:
            orders = sess.query(Orders).all()
        return jsonify(
            {
                'orders':
                    [
                        item.to_dict(
                            only=('id', 'user_id', 'shop_id', 'total_amount', 'status', 'description',
                                  'created_date', 'price', 'delivery_type', 'type_of_payment', 'address', 'coords')
                        )
                        for item in orders
                    ]
            }
        )

    def post(self):
        args = parser_post_args.parse_args()
        order_id = None

        with db_session.create_session() as sess:
            shop = sess.get(Shops, args['shop_id'])
            if not shop:
                abort(404, message=f'Shop with id {args["shop_id"]} not found')

            user = sess.get(User, args['user_id'])
            if not user:
                abort(404, message=f'User with id {args["user_id"]} not found')

            order = Orders(
                user_id=args['user_id'],
                shop_id=args['shop_id'],
                description=args['description'],
                total_amount=args['total_amount'],
                price=args['price'],
                delivery_type=args['delivery_type'],
                status=args['status'],
                created_date=args['created_date'],
                type_of_payment=args['type_of_payment'],
                address=args['address'],
                coords=args['coords']
            )
            sess.add(order)
            sess.commit()

            order_id = order.id

        return jsonify(
            {
                'id': order_id
            }
        )