import datetime

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Shops(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'shops'

    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True
    )
    name = sqlalchemy.Column(
        sqlalchemy.String
    )
    email = sqlalchemy.Column(
        sqlalchemy.String,
        index=True,
        unique=True
    )
    address = sqlalchemy.Column(
        sqlalchemy.String
    )
    # рейтинг магазина
    rate = sqlalchemy.Column(
        sqlalchemy.Float,
        default=0
    )
    # изображения магазина(их могут и не быть)
    imgs = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True
    )
    # описание магазина(может быть пустым)
    description = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True
    )
    # расписание работы магазина
    timetable = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True
    )
    # координаты разделены запятой(широта и долгота)
    coords = sqlalchemy.Column(
        sqlalchemy.String
    )
    hashed_password = sqlalchemy.Column(
        sqlalchemy.String
    )
    created_date = sqlalchemy.Column(
        sqlalchemy.DateTime,
        default=datetime.datetime.now
    )

    products = orm.relationship('Products', back_populates='shop')
    orders = orm.relationship('Orders', back_populates='shop')
    reviews = orm.relationship('ReviewsShop', back_populates='shop')