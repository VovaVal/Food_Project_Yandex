import datetime

from flask_restful import Resource, reqparse, abort
from flask import jsonify
from flask_login import current_user, login_required

from website.data import db_session
from website.data.orders import Orders
from website.data.shops import Shops
from website.data.users import User


parser_post_args = reqparse.RequestParser()
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
# если пользователь выбрал самовывоз, то ему не нужно указывать свой адрес
parser_post_args.add_argument('address')
parser_post_args.add_argument('coords')

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('description')
parser_patch_args.add_argument('total_amount', type=int)
parser_patch_args.add_argument('price', type=int)
parser_patch_args.add_argument('delivery_type', choices=['pickup', 'delivery'],
                               help='Allowed delivery types: "pickup" and "delivery"')
parser_patch_args.add_argument('status', choices=['active', 'finished', 'cancelled'],
                               help='Allowed status types: "active", "cancelled" and "finished"')
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


def check_order_access(order: Orders):
    """Проверка, имеет ли пользователь доступ к просмотру заказа"""
    if current_user.role == 'admin':
        return True

    if current_user.role == 'customer':
        if current_user.id != order.user_id:
            abort(403, message='You can only view your own orders')
        return True

    if current_user.role == 'shop':
        with db_session.create_session() as sess:
            shop = sess.query(Shops).filter(Shops.user_id == current_user.id).first()
            if not shop or order.shop_id != shop.id:
                abort(403, message='You can only view orders from your own shop')
        return True

    abort(403, message='Access denied')


def can_update_order(order: Orders):
    """Проверка, может ли пользователь обновлять статус заказа"""
    if current_user.role == 'admin':
        return True

    if current_user.role == 'shop':
        with db_session.create_session() as sess:
            shop = sess.query(Shops).filter(Shops.user_id == current_user.id).first()
            if shop and order.shop_id == shop.id:
                return True
        abort(403, message='Only the shop can update this order')

    if current_user.role == 'customer':
        if current_user.id != order.user_id:
            abort(403, message='You can only update your own orders')
        return True

    abort(403, message='You cannot update this order')


class OrdersResource(Resource):
    def get(self, order_id: int):
        order = abort_if_order_not_found(order_id)
        check_order_access(order)
        return jsonify(
            {
                'order': order.to_dict(
                    only=('id', 'user_id', 'shop_id', 'total_amount', 'status', 'description',
                          'created_date', 'price', 'delivery_type', 'type_of_payment', 'address', 'coords')
                )
            }
        )

    @login_required
    def delete(self, order_id: int):
        order = abort_if_order_not_found(order_id)

        if current_user.role != 'admin':
            abort(403, message='Only admin can delete orders')

        with db_session.create_session() as sess:
            sess.delete(order)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )

    @login_required
    def patch(self, order_id: int):
        order = abort_if_order_not_found(order_id)
        args = parser_patch_args.parse_args()

        # только админ может изменять заказ после того как он был либо доставлен, либо отменён
        if order.status in ['cancelled', 'finished'] and current_user.role != 'admin':
            abort(403, message='Access denied: order has already been delivered or cancelled')

        can_update_order(order)

        with db_session.create_session() as sess:
            if current_user.role == 'customer':
                if args['address'] is not None:
                    setattr(order, 'address', args['address'])
                if args['coords'] is not None:
                    setattr(order, 'coords', args['coords'])
                if args['type_of_payment'] is not None:
                    setattr(order, 'type_of_payment', args['type_of_payment'])
                if args['description'] is not None:
                    setattr(order, 'description', args['description'])

            elif current_user.role == 'shop':
                if args['address'] is not None:
                    setattr(order, 'address', args['address'])
                if args['coords'] is not None:
                    setattr(order, 'coords', args['coords'])
                if args['delivery_type'] is not None:
                    setattr(order, 'delivery_type', args['delivery_type'])
                if args['type_of_payment'] is not None:
                    setattr(order, 'type_of_payment', args['type_of_payment'])
                if args['status'] is not None:
                    setattr(order, 'status', args['status'])

            elif current_user.role == 'admin':
                for key, value in args.items():
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
    @login_required
    def get(self):
        """Список заказов с фильтрацией по роли"""
        with db_session.create_session() as sess:
            if current_user.role == 'admin':
                orders = sess.query(Orders).all()
            elif current_user.role == 'customer':
                orders = sess.query(Orders).filter(Orders.user_id == current_user.id).all()
            else:
                shop = sess.query(Shops).filter(Shops.user_id == current_user.id).first()
                if not shop:
                    orders = []
                else:
                    orders = sess.query(Orders).filter(Orders.shop_id == shop.id).all()

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

    @login_required
    def post(self):
        if current_user.role == 'shop':
            abort(403, message='Only customers can create orders')

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
                user_id=current_user.id,
                shop_id=args['shop_id'],
                description=args['description'],
                total_amount=args['total_amount'],
                price=args['price'],
                delivery_type=args['delivery_type'],
                status=args['status'],
                type_of_payment=args['type_of_payment'],
                address=args['address'],
                coords=args['coords'],
                created_date=datetime.datetime.now()
            )
            sess.add(order)
            sess.commit()

            order_id = order.id

        return jsonify(
            {
                'id': order_id
            }
        )