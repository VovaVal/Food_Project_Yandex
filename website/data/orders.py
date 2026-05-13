import datetime

import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Orders(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'orders'

    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True
    )
    user_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('users.id')
    )
    shop_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('shops.id')
    )
    # описание доставки(может быть пустым)
    description = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True
    )
    # общее количество товаров
    total_amount = sqlalchemy.Column(
        sqlalchemy.Integer,
        default=0
    )
    # общая сумма заказа
    price = sqlalchemy.Column(
        sqlalchemy.Integer,
        default=0
    )
    # способ доставки(самовывоз(pickup) или доставка(delivery))
    delivery_type = sqlalchemy.Column(
        sqlalchemy.String,
        default='pickup'
    )
    # статус заказа(active, cooking, cancelled или finished)
    status = sqlalchemy.Column(
        sqlalchemy.String,
        default='active'
    )
    created_date = sqlalchemy.Column(
        sqlalchemy.DateTime,
        default=datetime.datetime.now
    )
    # тип оплаты(наличные(cash), карта(card) или бонусы(bonus))
    type_of_payment = sqlalchemy.Column(
        sqlalchemy.String,
        default='cash'
    )
    address = sqlalchemy.Column(
        sqlalchemy.String
    )
    coords = sqlalchemy.Column(
        sqlalchemy.String
    )
    confirm_code = sqlalchemy.Column(
        sqlalchemy.String
    )
    # бонусы пользователя, которые мы использовали
    user_bonuses = sqlalchemy.Column(
        sqlalchemy.Integer,
        default=0
    )

    order_items = orm.relationship('OrderItems', back_populates='order')
    shop = orm.relationship('Shops', back_populates='orders')
    user = orm.relationship('User', back_populates='orders')