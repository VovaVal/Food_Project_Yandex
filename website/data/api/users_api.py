from flask_restful import Resource, reqparse, abort
from flask import jsonify

from werkzeug.security import generate_password_hash
import datetime

from website.data.users import User
from website.data import db_session


def abort_if_user_not_found(user_id: int):
    with db_session.create_session() as sess:
        user = sess.get(User, user_id)

    if not user:
        abort(404, message=f'User with id {user_id} not found')
    # если удачно, то возвращаем класс пользователя
    return user


class UsersResource(Resource):
    def get(self, user_id: int):
        user = abort_if_user_not_found(user_id)
        return jsonify(
            {
                'user': user.to_dict(
                    only=('id', 'name', 'img', 'user_bonuses', 'email', 'hashed_password', 'created_date')
                )
            }
        )


class UsersListResource(Resource):
    def get(self):
        with db_session.create_session() as sess:
            users = sess.query(User).all()
        return jsonify(
            {
                'users':
                    [
                        item.to_dict(
                            only=('id', 'name', 'img', 'user_bonuses', 'email', 'hashed_password', 'created_date')
                        )
                        for item in users
                    ]
            }
        )