from flask import jsonify
from flask_restful import abort, Resource
from data.db_session import create_session
from data.users import User
from .arg_parser_user import parser


def abort_if_user_not_found(user_id):
    with create_session() as db_sess:
        user = db_sess.query(User).get(user_id)
        if not user:
            abort(404, message=f"Users {user_id} not found")


class UsersResource(Resource):
    def get(self, user_id):
        abort_if_user_not_found(user_id)
        with create_session() as db_sess:
            users = db_sess.get(User, user_id)
        return jsonify({'users': users.to_dict()})

    def delete(self, user_id):
        abort_if_user_not_found(user_id)
        with create_session() as db_sess:
            user = db_sess.get(User, user_id)
            db_sess.delete(user)
            db_sess.commit()
        return jsonify({'success': 'OK'})

    def put(self, user_id):
        abort_if_user_not_found(user_id)
        with create_session() as db_sess:
            users = db_sess.get(User, user_id)
            args = parser.parse_args()
            users.surname = args['surname']
            users.name = args['name']
            users.age = args['age']
            users.email = args['email']
            users.set_password(args['password'])
            users.is_admin = args['is_admin']
            users.image_path = args['image_path']
            users.total_spent = args['total_spent']
            users.total_orders_count = args['total_order_count']
            db_sess.commit()
        return jsonify({'success': 'OK'})


class UsersListResource(Resource):
    def get(self):
        with create_session() as db_sess:
            users = db_sess.query(User).all()
            return jsonify({
                'users': [item.to_dict() for item in users]
            })
