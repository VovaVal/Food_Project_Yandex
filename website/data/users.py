import datetime

import sqlalchemy
from sqlalchemy import orm
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True
    )
    name = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True
    )
    img = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True
    )
    # баллы пользователя(их можно использовать для оплаты покупок)
    user_bonuses = sqlalchemy.Column(
        sqlalchemy.Integer,
        default=0
    )
    email = sqlalchemy.Column(
        sqlalchemy.String,
        index=True,
        unique=True
    )
    hashed_password = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True
    )
    created_date = sqlalchemy.Column(
        sqlalchemy.DateTime,
        default=datetime.datetime.now
    )

    orders = orm.relationship('Orders', back_populates='user')
    product_reviews = orm.relationship('ReviewsProduct', back_populates='user')
    shop_reviews = orm.relationship('ReviewsShop', back_populates='user')