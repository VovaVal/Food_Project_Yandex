from flask_restful import Resource, reqparse, abort
from flask import jsonify
from flask_login import login_required, current_user

from datetime import date

from website.data.products import Products
from website.data.reviews_product import ReviewsProduct
from website.data import db_session


parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('product_id', type=int, required=True)
parser_post_args.add_argument('review_text', required=True)

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('review_text')


def abort_if_review_product_not_found(review_product_id: int):
    with db_session.create_session() as sess:
        review_product = sess.get(ReviewsProduct, review_product_id)

    if not review_product:
        abort(404, message=f"Products' Review with id {review_product_id} not found")
    return review_product


def is_users_review_or_admin(review: ReviewsProduct):
    if current_user.id != review.user_id and current_user.role != 'admin':
        abort(403, message='Access denied: you can only manage your own reviews')


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

    @login_required
    def delete(self, review_product_id: int):
        review_product = abort_if_review_product_not_found(review_product_id)
        is_users_review_or_admin(review_product)

        with db_session.create_session() as sess:
            sess.delete(review_product)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )

    @login_required
    def patch(self, review_product_id: int):
        review_product = abort_if_review_product_not_found(review_product_id)
        is_users_review_or_admin(review_product)

        args = parser_patch_args.parse_args()

        with db_session.create_session() as sess:
            for key, value in args.items():
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

    @login_required
    def post(self):
        if current_user.role == 'shop':
            abort(403, message='Access denied: shop owner can not write reviews to products')

        args = parser_post_args.parse_args()
        reviews_product_id = None

        with db_session.create_session() as sess:
            product = sess.get(Products, args['product_id'])
            if not product:
                abort(404, message=f'Product with id {args["product_id"]} not found')

            # в случае если пользователь уже оставил комментарий товару(отзыв можно будет только редактировать)
            no_review_before = sess.query(ReviewsProduct).filter(ReviewsProduct.user_id == current_user.id,
                                                              ReviewsProduct.product_id == args['product_id']).first()
            if no_review_before:
                abort(400, message=f'Review for Product with id: {args['product_id']};'
                                   f' by the user with id: {args['user_id']} has already been written')

            reviews_product = ReviewsProduct(
                product_id=args['product_id'],
                user_id=current_user.id,
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