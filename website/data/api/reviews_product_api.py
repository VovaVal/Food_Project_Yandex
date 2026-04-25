from flask_restful import Resource, reqparse, abort
from flask import jsonify

from datetime import date

from website.data.products import Products
from website.data.reviews_product import ReviewsProduct
from website.data import db_session
from website.data.users import User


parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('user_id', type=int, required=True)
parser_post_args.add_argument('product_id', type=int, required=True)
parser_post_args.add_argument('review_text', required=True)

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('user_id', type=int)
parser_patch_args.add_argument('product_id', type=int)
parser_patch_args.add_argument('review_text')


def abort_if_review_product_not_found(review_product_id: int):
    with db_session.create_session() as sess:
        review_product = sess.get(ReviewsProduct, review_product_id)

    if not review_product:
        abort(404, message=f"Products' Review with id {review_product_id} not found")
    return review_product


class ReviewsProductResource(Resource):
    def get(self, review_product_id: int):
        review_product = abort_if_review_product_not_found(review_product_id)
        return jsonify(
            {
                'review_product': review_product.to_dict(
                    only=('id', 'product_id', 'user_id', 'review_text', 'created_date')
                )
            }
        )

    def delete(self, review_product_id: int):
        review_product = abort_if_review_product_not_found(review_product_id)

        with db_session.create_session() as sess:
            sess.delete(review_product)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )

    def patch(self, review_product_id: int):
        review_product = abort_if_review_product_not_found(review_product_id)
        args = parser_patch_args.parse_args()

        with db_session.create_session() as sess:
            for key, value in args.items():
                if key == 'user_id' and value is not None:
                    user = sess.get(User, value)
                    if not user:
                        abort(404, message=f'User with id {args["user_id"]} not found')

                if key == 'product_id' and value is not None:
                    product = sess.get(Products, value)
                    if not product:
                        abort(404, message=f'Product with id {args["product_id"]} not found')

                if value is not None:
                    setattr(review_product, key, value)

            sess.add(review_product)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )


class ReviewsProductListResource(Resource):
    def get(self):
        with db_session.create_session() as sess:
            reviews_products = sess.query(ReviewsProduct).all()
        return jsonify(
            {
                'reviews_products':
                    [
                        item.to_dict(
                            only=('id', 'product_id', 'user_id', 'review_text', 'created_date')
                        )
                        for item in reviews_products
                    ]
            }
        )

    def post(self):
        args = parser_post_args.parse_args()
        reviews_product_id = None

        with db_session.create_session() as sess:
            user = sess.get(User, args['user_id'])
            if not user:
                abort(404, message=f'User with id {args["user_id"]} not found')

            product = sess.get(Products, args['product_id'])
            if not product:
                abort(404, message=f'Product with id {args["product_id"]} not found')

            # в случае если пользователь уже оставил комментарий товару(отзыв можно будет только редактировать)
            no_review_before = sess.query(ReviewsProduct).filter(ReviewsProduct.user_id == args['user_id'],
                                                              ReviewsProduct.product_id == args['product_id']).first()
            if no_review_before:
                abort(404, message=f'Review for Product with id: {args['product_id']};'
                                   f' by the user with id: {args['user_id']} has already been written')

            reviews_product = ReviewsProduct(
                product_id=args['product_id'],
                user_id=args['user_id'],
                review_text=args['review_text'],
                created_date=date.today()
            )
            sess.add(reviews_product)
            sess.commit()

            reviews_product_id = reviews_product.id

        return jsonify(
            {
                'id': reviews_product_id
            }
        )