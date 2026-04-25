from flask_restful import Resource, reqparse, abort
from flask import jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import check_password_hash

from website.data.users import User
from website.data import db_session


parser_login = reqparse.RequestParser()
parser_login.add_argument('email', required=True)
parser_login.add_argument('password', required=True)


class LoginResource(Resource):
    def post(self):
        args = parser_login.parse_args()

        with db_session.create_session() as sess:
            user = sess.query(User).filter(User.email == args['email']).first()

            if not user or not check_password_hash(user.hashed_password, args['password']):
                abort(401, message='Invalid email or password')

        login_user(user, remember=True)

        return jsonify(
            {
                'message': 'Login successful',
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'role': user.role
                }
            }
        )


class LogoutResource(Resource):
    @login_required
    def post(self):
        logout_user()
        return jsonify({'message': 'Logout successful'})


class CurrentUserResource(Resource):
    @login_required
    def get(self):
        return jsonify({
            'user': current_user.to_dict(
                only=('id', 'name', 'img', 'email', 'role', 'user_bonuses', 'created_date')
            )
        })