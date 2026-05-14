import requests
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, login_user, logout_user, current_user

from website.data import db_session
from website.data.users import User
from website.forms.login import LoginForm
from website.forms.register import Register

auth_bp = Blueprint(
    'auth',
    __name__,
    template_folder='templates'
)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('common.index'))

    form = LoginForm()

    if form.validate_on_submit():
        with db_session.create_session() as sess:
            user = sess.query(User).filter(User.email == form.email.data).first()

            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                flash(message='Вы вошли в аккаунт!', category='success')
                return redirect(url_for('common.index'))

        flash(message='Неправильный логин или пароль', category='danger')
        return render_template('auth/login.html', title='Авторизация', form=form)

    return render_template('auth/login.html', title='Авторизация', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('common.index'))

    form = Register()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        repeat_password = form.repeat_password.data
        role = form.role.data

        if password != repeat_password:
            flash(message='Пароли не совпадают!', category='danger')
            return render_template('auth/register.html', title='Регистрация', form=form)

        api_url = request.url_root + 'api/users'
        resp = requests.post(
            api_url,
            json={
                'email': email,
                'password': password,
                'role': role
            },
            verify=False,
            allow_redirects=True
        )
        print(resp.json())

        if resp.status_code == 200:
            user_id = resp.json()['id']

            with db_session.create_session() as sess:
                user = sess.get(User, user_id)
                login_user(user, remember=True)
                flash(message='Вы зарегистрированы!', category='success')
                return redirect(url_for('common.index'))

        else:
            error = resp.json().get('message', 'Ошибка регистрации')
            flash(error, category='danger')
            return render_template('auth/register.html', title='Регистрация', form=form)


    return render_template('auth/register.html', title='Регистрация', form=form)


@login_required
@auth_bp.route('/logout')
def logout():
    logout_user()
    return redirect('/')


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('common.index'))
    else:
        return redirect('login')