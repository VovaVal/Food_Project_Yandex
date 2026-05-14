from flask_restful import Resource, reqparse, abort
from flask import jsonify
from flask_login import current_user, login_required

from website.data import db_session
from website.data.orders import Orders
from website.data.products import Products
from website.data.order_items import OrderItems
from website.data.shops import Shops

parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('product_id', type=int, required=True)
parser_post_args.add_argument('order_id', type=int, required=True)
parser_post_args.add_argument('quantity', type=int, required=True)

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('quantity', type=int)


def abort_if_order_item_not_found(order_item_id: int):
    with db_session.create_session() as sess:
        order_item = sess.get(OrderItems, order_item_id)

    if not order_item:
        abort(404, message=f'Order Item with id {order_item_id} not found')
    return order_item


def check_order_item_access(order_item: OrderItems):
    """Проверка, что пользователь имеет доступ к позиции заказа"""
    with db_session.create_session() as sess:
        order = sess.get(Orders, order_item.order_id)
        if not order:
            abort(404, message='Order not found')

        # Покупатель: только свои заказы
        if current_user.role == 'customer':
            if order.user_id != current_user.id:
                abort(403, message='You can only access your own orders')

        # Магазин: только заказы своего магазина
        elif current_user.role == 'shop':
            shop = sess.query(Shops).filter(Shops.user_id == current_user.id).first()
            if not shop or order.shop_id != shop.id:
                abort(403, message='You can only access orders from your own shop')

        # Нельзя изменять завершённые или отменённые заказы
        if order.status in ['finished', 'cancelled'] and current_user.role != 'admin':
            abort(403, message='Cannot modify finished or cancelled orders')


def recalc_order_total(order_id: int):
    """Пересчитать общую сумму заказа"""
    with db_session.create_session() as sess:
        items = sess.query(OrderItems).filter(OrderItems.order_id == order_id).all()
        total_amount = sum(item.quantity for item in items)
        price = 0

        for item in items:
            product = sess.get(Products, item.product_id)
            if product:
                price += item.quantity * product.price

        order = sess.get(Orders, order_id)
        order.price = price
        order.total_amount = total_amount

        sess.add(order)
        sess.commit()


class OrderItemsResource(Resource):
    def get(self, order_item_id: int):
        order_item = abort_if_order_item_not_found(order_item_id)
        check_order_item_access(order_item)

        return jsonify(
            {
                'order_item': order_item.to_dict(
                    only=('id', 'product_id', 'order_id', 'quantity')
                )
            }
        )

    @login_required
    def delete(self, order_item_id: int):
        order_item = abort_if_order_item_not_found(order_item_id)
        check_order_item_access(order_item)

        with db_session.create_session() as sess:
            sess.delete(order_item)
            sess.commit()

        recalc_order_total(order_item.order_id)

        return jsonify(
            {
                'success': 'OK'
            }
        )

    @login_required
    def patch(self, order_item_id: int):
        order_item = abort_if_order_item_not_found(order_item_id)
        check_order_item_access(order_item)

        args = parser_patch_args.parse_args()

        with db_session.create_session() as sess:
            for key, value in args.items():
                if key == 'quantity' and value is not None:
                    if args['quantity'] <= 0:
                        abort(400, message='Quantity must be positive')

                if value is not None:
                    setattr(order_item, key, value)

            sess.add(order_item)
            sess.commit()

        recalc_order_total(order_item.order_id)

        return jsonify(
            {
                'success': 'OK'
            }
        )


class OrderItemsListResource(Resource):
    def get(self):
        with db_session.create_session() as sess:
            order_items = sess.query(OrderItems).all()
        return jsonify(
            {
                'order_items':
                    [
                        item.to_dict(
                            only=('id', 'product_id', 'order_id', 'quantity')
                        )
                        for item in order_items
                    ]
            }
        )

    @login_required
    def post(self):
        args = parser_post_args.parse_args()
        order_item_id = None

        with db_session.create_session() as sess:
            product = sess.get(Products, args['product_id'])
            if not product:
                abort(404, message=f'Product with id {args["product_id"]} not found')

            if product.quantity < args['quantity']:
                abort(400, message='Not enough stock')

            order = sess.get(Orders, args['order_id'])
            if not order:
                abort(404, message=f'Order with id {args["order_id"]} not found')

            # Проверка доступа к заказу
            if current_user.role == 'customer' and order.user_id != current_user.id:
                abort(403, message='You can only add items to your own orders')

            if current_user.role == 'shop':
                shop = sess.query(Shops).filter(Shops.user_id == current_user.id).first()
                if not shop or order.shop_id != shop.id:
                    abort(403, message='You can only add items to orders from your own shop')

            # Проверка, что заказ активен
            if order.status not in ['active', 'pending', 'cooking']:
                abort(403, message='Cannot add items to finished or cancelled orders')

            # Проверка, что товар принадлежит магазину заказа
            if product.shop_id != order.shop_id:
                abort(400, message='Product does not belong to this shop')

            existing = sess.query(OrderItems).filter(
                OrderItems.order_id == order.id,
                OrderItems.product_id == product.id
            ).first()

            if existing:
                # Если уже есть — увеличиваем количество
                existing.quantity += args['quantity']
                order_items = existing

            else:
                order_items = OrderItems(
                    product_id=args['product_id'],
                    order_id=args['order_id'],
                    quantity=args['quantity']
                )

            product.quantity -= args['quantity']

            sess.add(product)
            sess.add(order_items)
            sess.commit()

            recalc_order_total(order.id)

            order_item_id = order_items.id

        return jsonify(
            {
                'id': order_item_id
            }
        )