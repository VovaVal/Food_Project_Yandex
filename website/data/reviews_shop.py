import datetime

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class ReviewsShop(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'reviews_shop'

    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True
    )
    shop_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('shops.id')
    )
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('users.id')
    )
    # текст отзыва
    review_text = sqlalchemy.Column(
        sqlalchemy.String
    )
    created_date = sqlalchemy.Column(
        sqlalchemy.Date,
        default=datetime.date.today
    )
    rate = sqlalchemy.Column(
        sqlalchemy.Integer,
        default=4
    )

    shop = orm.relationship('Shops', back_populates='reviews')
    user = orm.relationship('User', back_populates='shop_reviews')