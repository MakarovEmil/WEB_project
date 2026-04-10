import datetime
import sqlalchemy
from sqlalchemy import orm
from .db_session import SqlAlchemyBase
from flask_login import UserMixin
from sqlalchemy_serializer import SerializerMixin


class Order(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'orders'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    order_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    total_amount = sqlalchemy.Column(sqlalchemy.Integer)
    discount_percent = sqlalchemy.Column(sqlalchemy.Integer)
    user = orm.relationship("User")
    items = orm.relationship("OrderItem", back_populates='order')