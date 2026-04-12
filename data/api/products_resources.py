from flask import jsonify
from flask_restful import abort, Resource
from data import db_session
from data.products import Product
from flask import request


def abort_if_product_not_found(product_id):
    session = db_session.create_session()
    products = session.query(Product).get(product_id)
    if not products:
        abort(404, message=f"Product {product_id} not found")


class ProductsResource(Resource):
    def get(self, product_id):
        abort_if_product_not_found(product_id)
        db_sess = db_session.create_session()
        products = db_sess.get(Product, product_id)
        return jsonify({'products': products.to_dict()})

    def delete(self, product_id):
        abort_if_product_not_found(product_id)
        db_sess = db_session.create_session()
        products = db_sess.get(Product, product_id)
        db_sess.delete(products)
        db_sess.commit()
        return jsonify({'success': 'OK'})

    '''def put(self, product_id): #Доделать когда будешь делать редактирование продукта
        abort_if_product_not_found(product_id)
        db_sess = db_session.create_session()
        products = db_sess.get(User, user_id)
        args = parser.parse_args()
        products.surname = args['surname']
        products.name = args['name']
        products.age = args['age']
        products.email = args['email']
        products.set_password(args['password'])
        products.is_admin = args['is_admin']
        products.image_path = args['image_path']
        products.total_spent = args['total_spent']
        products.total_orders_count = args['total_order_count']
        db_sess.commit()
        return jsonify({'success': 'OK'})'''


class ProductsListResource(Resource):
    def get(self):
        db_sess = db_session.create_session()
        query = db_sess.query(Product)

        '''in_stock = request.args.get('in_stock', 'false').lower() == 'true'
        if in_stock:
            query = query.filter(Product.stock > 0)'''

        '''category_id = request.args.get('category_id', 0)
        if category_id:
            query = query.filter(Product.category_id == category_id)'''

        products = query.all()
        return jsonify({'products': [product.to_dict() for product in products]})


