from flask_restful import Resource, reqparse, abort
from flask import jsonify

from datetime import date

from website.data.shops import Shops
from website.data.reviews_shop import ReviewsShop
from website.data import db_session
from website.data.users import User


parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('user_id', type=int, required=True)
parser_post_args.add_argument('shop_id', type=int, required=True)
parser_post_args.add_argument('review_text', required=True)

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('user_id', type=int)
parser_patch_args.add_argument('shop_id', type=int)
parser_patch_args.add_argument('review_text')


def abort_if_review_shop_not_found(review_shop_id: int):
    with db_session.create_session() as sess:
        review_shop = sess.get(ReviewsShop, review_shop_id)

    if not review_shop:
        abort(404, message=f"Shops' Review with id {review_shop_id} not found")
    return review_shop


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

    def delete(self, review_shop_id: int):
        review_shop = abort_if_review_shop_not_found(review_shop_id)

        with db_session.create_session() as sess:
            sess.delete(review_shop)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )

    def patch(self, review_shop_id: int):
        review_shop = abort_if_review_shop_not_found(review_shop_id)
        args = parser_patch_args.parse_args()

        with db_session.create_session() as sess:
            for key, value in args.items():
                if key == 'user_id' and value is not None:
                    user = sess.get(User, value)
                    if not user:
                        abort(404, message=f'User with id {args["user_id"]} not found')

                if key == 'shop_id' and value is not None:
                    shop = sess.get(Shops, value)
                    if not shop:
                        abort(404, message=f'Shop with id {args["shop_id"]} not found')

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

    def post(self):
        args = parser_post_args.parse_args()
        reviews_shop_id = None

        with db_session.create_session() as sess:
            user = sess.get(User, args['user_id'])
            if not user:
                abort(404, message=f'User with id {args["user_id"]} not found')

            shop = sess.get(Shops, args['shop_id'])
            if not shop:
                abort(404, message=f'Shop with id {args["shop_id"]} not found')

            # в случае если пользователь уже оставил комментарий магазину(отзыв можно будет только редактировать)
            no_review_before = sess.query(ReviewsShop).filter(ReviewsShop.user_id == args['user_id'],
                                                              ReviewsShop.shop_id == args['shop_id']).first()
            if no_review_before:
                abort(404, message=f'Review for Shop with id: {args['shop_id']};'
                                   f' by the user with id: {args['user_id']} has already been written')

            reviews_shop = ReviewsShop(
                shop_id=args['shop_id'],
                user_id=args['user_id'],
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