import sqlalchemy
from sqlalchemy import orm
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Products(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'products'

    id = sqlalchemy.Column(
        sqlalchemy.Integer,
        primary_key=True,
        autoincrement=True
    )
    name = sqlalchemy.Column(
        sqlalchemy.String
    )
    shop_id = sqlalchemy.Column(
        sqlalchemy.Integer,
        sqlalchemy.ForeignKey('shops.id')
    )
    # рейтинг товара
    rate = sqlalchemy.Column(
        sqlalchemy.Float,
        default=0
    )
    # изображения товара(их могут и не быть)
    imgs = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True
    )
    # описание товара(может быть пустым)
    description = sqlalchemy.Column(
        sqlalchemy.String,
        nullable=True
    )
    # количество товаров
    quantity = sqlalchemy.Column(
        sqlalchemy.Integer
    )
    price = sqlalchemy.Column(
        sqlalchemy.Integer
    )
    product_weight = sqlalchemy.Column(
        sqlalchemy.Float,
        default=100
    )
    type_of_count = sqlalchemy.Column(
        sqlalchemy.String,
        default='g'
    )
    # тип продукта(напиток, мучная продукция и тд.)
    product_type = sqlalchemy.Column(
        sqlalchemy.String
    )

    shop = orm.relationship('Shops', back_populates='products')
    order_items = orm.relationship('OrderItems', back_populates='product')
    reviews = orm.relationship('ReviewsProduct', back_populates='product')