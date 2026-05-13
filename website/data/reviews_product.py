import datetime

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class ReviewsProduct(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'reviews_product'

    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True
    )
    product_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('products.id')
    )
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('users.id')
    )
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

    product = orm.relationship('Products', back_populates='reviews')
    user = orm.relationship('User', back_populates='product_reviews')