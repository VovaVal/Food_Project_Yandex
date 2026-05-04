from flask_restful import Resource, reqparse, abort
from flask import jsonify
from flask_login import login_required, current_user

from werkzeug.security import generate_password_hash
from datetime import date

from website.data.users import User
from website.data import db_session


parser_post_args = reqparse.RequestParser()
parser_post_args.add_argument('name', default='Пользователь')
parser_post_args.add_argument('img', default='users/imgs/default_icon_user_account.png')
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


def is_admin_or_user(user_id: int):
    # Дополнительная проверка: пользователь может смотреть только себя
    if current_user.id != user_id and current_user.role != 'admin':
        abort(403, message='Access denied: you can only view/delete/edit your own profile')


def is_admin():
    if current_user.role != 'admin':
        abort(403, message='Access denied: you can only view/delete/edit your own profile')


class UsersResource(Resource):
    @login_required
    def get(self, user_id: int):
        is_admin_or_user(user_id)

        user = abort_if_user_not_found(user_id)
        return jsonify(
            {
                'user': user.to_dict(
                    only=('id', 'name', 'img', 'user_bonuses', 'email',
                          'hashed_password', 'created_date', 'role')
                )
            }
        )

    @login_required
    def delete(self, user_id: int):
        is_admin_or_user(user_id)

        user = abort_if_user_not_found(user_id)

        with db_session.create_session() as sess:
            sess.delete(user)
            sess.commit()

        return jsonify(
            {
                'success': 'OK'
            }
        )

    @login_required
    def patch(self, user_id: int):
        is_admin_or_user(user_id)

        user = abort_if_user_not_found(user_id)
        args = parser_patch_args.parse_args()

        with db_session.create_session() as sess:
            for key, value in args.items():
                if key == 'password' and value is not None:
                    if len(value) < 6:
                        abort(400, message='Password must be at least 6 characters')

                    key = 'hashed_password'
                    value = generate_password_hash(value)

                if key == 'email' and value is not None:
                    email_exist = sess.query(User).filter(User.email == value.strip()).first()

                    if email_exist:
                        abort(400, message='Пользователь с такой почтой уже существует!')

                if key == 'img' and value is not None and value.strip() == '':
                    value = 'users/imgs/default_icon_user_account.png'

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
    @login_required
    def get(self):
        is_admin()

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
                abort(400, message=f'Пользователь с почтой {args['email']} уже существует!')

            if len(args['password']) < 6:
                abort(400, message='Пароль должен быть не менее 6 символов длиной!')

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