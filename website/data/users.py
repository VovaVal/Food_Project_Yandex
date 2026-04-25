import datetime

import sqlalchemy
from sqlalchemy import orm
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin
from werkzeug.security import generate_password_hash, check_password_hash

from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'users'

    # общие для пользователя и для магазина
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
        sqlalchemy.Date,
        default=datetime.date.today
    )
    # customer или shop
    role = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=False,
        default='customer'
    )

    # только для пользователя
    # баллы пользователя(их можно использовать для оплаты покупок)
    user_bonuses = sqlalchemy.Column(
        sqlalchemy.Integer,
        default=0
    )

    orders = orm.relationship('Orders', back_populates='user')
    product_reviews = orm.relationship('ReviewsProduct', back_populates='user')
    shop_reviews = orm.relationship('ReviewsShop', back_populates='user')
    shops = orm.relationship('Shops', back_populates='user')

    def set_password(self, password):
        self.hashed_password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.hashed_password, password)

    def is_shop(self):
        return self.role == 'shop'

    def is_customer(self):
        return self.role == 'customer'