from flask_restful import Resource, reqparse, abort
from flask import jsonify
from flask_login import current_user, login_required

from datetime import date

from website.data.shops import Shops
from website.data.reviews_shop import ReviewsShop
from website.data import db_session


parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('shop_id', type=int, required=True)
parser_post_args.add_argument('review_text', required=True)

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('review_text')


def abort_if_review_shop_not_found(review_shop_id: int):
    with db_session.create_session() as sess:
        review_shop = sess.get(ReviewsShop, review_shop_id)

    if not review_shop:
        abort(404, message=f"Shops' Review with id {review_shop_id} not found")
    return review_shop


def is_users_review_or_admin(review: ReviewsShop):
    if current_user.id != review.user_id and current_user.role != 'admin':
        abort(403, message='Access denied: you can only delete/add/edit your own reviews')


class ReviewsShopResource(Resource):
    def get(self, review_shop_id: int):
        review_shop = abort_if_review_shop_not_found(review_shop_id)
        return jsonify(
            {
                'review_shop': review_shop.to_dict(
                    only=('id', 'shop_id', 'user_id', 'review_text', 'created_date')
                )
            }
        )

    @login_required
    def delete(self, review_shop_id: int):
        review_shop = abort_if_review_shop_not_found(review_shop_id)
        is_users_review_or_admin(review_shop)

        with db_session.create_session() as sess:
            sess.delete(review_shop)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )

    @login_required
    def patch(self, review_shop_id: int):
        review_shop = abort_if_review_shop_not_found(review_shop_id)
        is_users_review_or_admin(review_shop)

        args = parser_patch_args.parse_args()

        with db_session.create_session() as sess:
            for key, value in args.items():
                if value is not None:
                    setattr(review_shop, key, value)

            sess.add(review_shop)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )


class ReviewsShopListResource(Resource):
    def get(self):
        with db_session.create_session() as sess:
            reviews_shops = sess.query(ReviewsShop).all()
        return jsonify(
            {
                'reviews_shops':
                    [
                        item.to_dict(
                            only=('id', 'shop_id', 'user_id', 'review_text', 'created_date')
                        )
                        for item in reviews_shops
                    ]
            }
        )

    @login_required
    def post(self):
        if current_user.role == 'shop':
            abort(403, message='Access denied: shop owner can not write reviews to shops')

        args = parser_post_args.parse_args()
        reviews_shop_id = None

        with db_session.create_session() as sess:
            shop = sess.get(Shops, args['shop_id'])
            if not shop:
                abort(404, message=f'Shop with id {args["shop_id"]} not found')

            # в случае если пользователь уже оставил комментарий магазину(отзыв можно будет только редактировать)
            no_review_before = sess.query(ReviewsShop).filter(ReviewsShop.user_id == current_user.id,
                                                              ReviewsShop.shop_id == args['shop_id']).first()
            if no_review_before:
                abort(404, message=f"Review for Shop with id: {args['shop_id']};"
                                   f" by the user with id: {current_user.id} has already been written")

            reviews_shop = ReviewsShop(
                shop_id=args['shop_id'],
                user_id=current_user.id,
                review_text=args['review_text'],
                created_date=date.today()
            )
            sess.add(reviews_shop)
            sess.commit()

            reviews_shop_id = reviews_shop.id

        return jsonify(
            {
                'id': reviews_shop_id
            }
        )