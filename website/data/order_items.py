import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class OrderItems(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'order_items'

    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True
    )
    product_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('products.id')
    )
    order_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('orders.id')
    )
    # количество товара
    quantity = sqlalchemy.Column(
        sqlalchemy.Integer
    )

    order = orm.relationship('Orders', back_populates='order_items')
    product = orm.relationship('Products', back_populates='order_items')