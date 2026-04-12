from flask_restful import reqparse

parser = reqparse.RequestParser()
parser.add_argument('name', required=True, type=str)
parser.add_argument('category_id', required=True, type=int)
parser.add_argument('price', required=True, type=int)
parser.add_argument('stock', required=True, type=int)
parser.add_argument('image_path', required=True, type=str)
parser.add_argument('description', type=str)
parser.add_argument('sowing_month_start', required=True, type=int)
parser.add_argument('sowing_month_end', required=True, type=int)
parser.add_argument('difficulty', required=True, type=str)









