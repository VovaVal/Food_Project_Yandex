from flask_restful import Resource, reqparse, abort
from flask import jsonify

from werkzeug.security import generate_password_hash
from datetime import date

from website.data.users import User
from website.data import db_session


parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('name', required=True)
parser_post_args.add_argument('img', default='website/static/imgs/icon_user_account.png')
parser_post_args.add_argument('user_bonuses', type=int, default=0)
parser_post_args.add_argument('email', required=True)
parser_post_args.add_argument('password', required=True)
parser_post_args.add_argument('role', choices=['customer', 'shop'],
                              default='customer', help='Allowed roles: "customer" and "shop"')

parser_patch_args = reqparse.RequestParser()
parser_patch_args.add_argument('name')
parser_patch_args.add_argument('img')
parser_patch_args.add_argument('user_bonuses', type=int)
parser_patch_args.add_argument('email')
parser_patch_args.add_argument('password')
parser_patch_args.add_argument('role', choices=['customer', 'shop'],
                               help='Allowed roles: "customer" and "shop"')


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
                    only=('id', 'name', 'img', 'user_bonuses', 'email',
                          'hashed_password', 'created_date', 'role')
                )
            }
        )

    def delete(self, user_id: int):
        user = abort_if_user_not_found(user_id)

        with db_session.create_session() as sess:
            sess.delete(user)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )

    def patch(self, user_id: int):
        user = abort_if_user_not_found(user_id)
        args = parser_patch_args.parse_args()

        with db_session.create_session() as sess:
            for key, value in args.items():
                if key == 'password' and value is not None:
                    key = 'hashed_password'
                    value = generate_password_hash(value)

                if value is not None:
                    setattr(user, key, value)

            sess.add(user)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
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
                            only=('id', 'name', 'img', 'user_bonuses', 'email',
                                  'hashed_password', 'created_date', 'role')
                        )
                        for item in users
                    ]
            }
        )

    def post(self):
        args = parser_post_args.parse_args()
        hashed_password = generate_password_hash(args['password'])
        user_id = None

        with db_session.create_session() as sess:
            user_exist = sess.query(User).filter(User.email == args['email']).first()
            if user_exist:
                abort(400, message=f'User with email {args['email']} already exists')

            user = User(
                name=args['name'],
                img=args['img'],
                user_bonuses=args['user_bonuses'],
                email=args['email'],
                hashed_password=hashed_password,
                created_date=date.today(),
                role=args['role']
            )
            sess.add(user)
            sess.commit()

            user_id = user.id

        return jsonify(
            {
                'id': user_id
            }
        )