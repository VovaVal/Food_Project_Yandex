from flask_restful import Resource, reqparse, abort
from flask import jsonify

from website.data import db_session
from website.data.orders import Orders
from website.data.products import Products
from website.data.order_items import OrderItems


parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('product_id', type=int, required=True)
parser_post_args.add_argument('order_id', type=int, required=True)
parser_post_args.add_argument('quantity', type=int, required=True)
parser_post_args.add_argument('price', type=int, required=True)

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('product_id', type=int)
parser_patch_args.add_argument('order_id', type=int)
parser_patch_args.add_argument('quantity', type=int)
parser_patch_args.add_argument('price', type=int)



def abort_if_order_item_not_found(order_item_id: int):
    with db_session.create_session() as sess:
        order_item = sess.get(OrderItems, order_item_id)

    if not order_item:
        abort(404, message=f'Order Item with id {order_item_id} not found')
    return order_item


class OrderItemsResource(Resource):
    def get(self, order_item_id: int):
        order_item = abort_if_order_item_not_found(order_item_id)
        return jsonify(
            {
                'order_item': order_item.to_dict(
                    only=('id', 'product_id', 'order_id', 'quantity', 'price')
                )
            }
        )

    def delete(self, order_item_id: int):
        order_item = abort_if_order_item_not_found(order_item_id)

        with db_session.create_session() as sess:
            sess.delete(order_item)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )

    def patch(self, order_item_id: int):
        order_item = abort_if_order_item_not_found(order_item_id)
        args = parser_patch_args.parse_args()

        with db_session.create_session() as sess:
            for key, value in args.items():
                if key == 'product_id' and value is not None:
                    product = sess.get(Products, args['product_id'])
                    if not product:
                        abort(404, message=f'Product with id {args["product_id"]} not found')

                if key == 'order_id' and value is not None:
                    order = sess.get(Orders, args['order_id'])
                    if not order:
                        abort(404, message=f'Order with id {args["order_id"]} not found')

                if value is not None:
                    setattr(order_item, key, value)

            sess.add(order_item)
            sess.commit()

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
                            only=('id', 'product_id', 'order_id', 'quantity', 'price')
                        )
                        for item in order_items
                    ]
            }
        )

    def post(self):
        args = parser_post_args.parse_args()
        order_item_id = None

        with db_session.create_session() as sess:
            product = sess.get(Products, args['product_id'])
            if not product:
                abort(404, message=f'Product with id {args["product_id"]} not found')

            order = sess.get(Orders, args['order_id'])
            if not order:
                abort(404, message=f'Order with id {args["order_id"]} not found')

            order_items = OrderItems(
                product_id=args['product_id'],
                order_id=args['order_id'],
                quantity=args['quantity'],
                price=args['price']
            )
            sess.add(order_items)
            sess.commit()

            order_item_id = order_items.id

        return jsonify(
            {
                'id': order_item_id
            }
        )