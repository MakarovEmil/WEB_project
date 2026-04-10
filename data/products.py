import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin


class Product(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'products'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    category_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('categories.id'))
    price = sqlalchemy.Column(sqlalchemy.Integer)
    stock = sqlalchemy.Column(sqlalchemy.Integer)
    image_path = sqlalchemy.Column(sqlalchemy.String)
    description = sqlalchemy.Column(sqlalchemy.String)
    sowing_month_start = sqlalchemy.Column(sqlalchemy.Integer)
    sowing_month_end = sqlalchemy.Column(sqlalchemy.Integer)
    difficulty = sqlalchemy.Column(sqlalchemy.String)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    order_items = orm.relationship("OrderItem", back_populates='product')
    category = orm.relationship("Category")