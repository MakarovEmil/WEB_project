from flask_restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument('surname', required=True, type=str)
parser.add_argument('name', required=True, type=str)
parser.add_argument('age', required=True, type=int)
parser.add_argument('email', required=True, type=str)
parser.add_argument('password', required=True, type=str)
parser.add_argument('image_path', required=True, type=str)
parser.add_argument('is_admin', required=True, default=False, type=bool)
parser.add_argument('total_orders_count', required=True, default=0, type=int)
parser.add_argument('total_spent', required=True, default=0, type=int)
