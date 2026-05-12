import datetime

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Cart(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'cart'

    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('users.id'),
        nullable=False
    )
    product_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('products.id'),
        nullable=False
    )
    # общее количество товаров
    quantity = sqlalchemy.Column(
        sqlalchemy.Integer,
        default=0
    )
    # активен ли товар(работает ли магазин в данный момент)
    active = sqlalchemy.Column(
        sqlalchemy.Boolean,
        default=True
    )

    product = orm.relationship('Products')