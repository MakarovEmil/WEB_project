from flask import jsonify
from flask_restful import abort, Resource
from data.db_session import create_session
from data.products import Product


def abort_if_product_not_found(product_id):
    with create_session() as db_sess:
        products = db_sess.query(Product).get(product_id)
        if not products:
            abort(404, message=f"Product {product_id} not found")


class ProductsResource(Resource):
    def get(self, product_id):
        abort_if_product_not_found(product_id)
        with create_session() as db_sess:
            products = db_sess.get(Product, product_id)
        return jsonify({'products': products.to_dict()})

    def delete(self, product_id):
        abort_if_product_not_found(product_id)
        with create_session() as db_sess:
            products = db_sess.get(Product, product_id)
            db_sess.delete(products)
            db_sess.commit()
        return jsonify({'success': 'OK'})


class ProductsListResource(Resource):
    def get(self):
        with create_session() as db_sess:
            query = db_sess.query(Product)

            products = query.all()
        return jsonify({'products': [product.to_dict() for product in products]})


