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
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('users.id')
    )
    address = sqlalchemy.Column(
        sqlalchemy.String,
        default=''
    )
    # рейтинг магазина
    rate = sqlalchemy.Column(
        sqlalchemy.Float,
        default=0
    )
    # изображения магазина(их могут и не быть)
    imgs = sqlalchemy.Column(
        sqlalchemy.String,
        default='shops/imgs/shop_img_default.jpg'
    )
    # Логотип магазина
    logo = sqlalchemy.Column(
        sqlalchemy.String,
        default='shops/logos/default_logo.svg'
    )
    # описание магазина(может быть пустым)
    description = sqlalchemy.Column(
        sqlalchemy.String,
        default=''
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
    created_date = sqlalchemy.Column(
        sqlalchemy.Date,
        default=datetime.date.today
    )
    updated_date = sqlalchemy.Column(
        sqlalchemy.DateTime,
        default=datetime.datetime.now
    )

    products = orm.relationship('Products', back_populates='shop')
    orders = orm.relationship('Orders', back_populates='shop')
    reviews = orm.relationship('ReviewsShop', back_populates='shop')
    user = orm.relationship('User', back_populates='shops')