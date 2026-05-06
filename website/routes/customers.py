import io

import requests
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from PIL import Image

from website.data.shops import Shops
from website.forms.edit_user_settings import EditFormUser
from website.data import db_session
from website.bucket_requests import upload_img_user


customer_bp = Blueprint(
    'customer',
    __name__
)


@customer_bp.before_request
def check_role():
    if not current_user.is_authenticated or current_user.role != 'customer':
        return redirect(url_for('auth.login'))

@login_required
@customer_bp.route('/dashboard')
def dashboard():
    api_url = request.url_root + f'api/shops/'
    resp = requests.get(
        api_url,
        cookies=request.cookies
    )

    if resp.status_code == 200:
        data = resp.json()
        shops = data.get('shops', [])

        return render_template('customer/dashboard.html', user=current_user, shops=shops)
    else:
        return render_template('errors/error.html', title='Ошибка',
                               error_code=500, error_message='Internal server error'), 500


@login_required
@customer_bp.route('/orders')
def orders():
    return render_template('customer/orders.html')


@login_required
@customer_bp.route('/')
def index():
    return redirect(url_for('shop.dashboard'))


@login_required
@customer_bp.route('/settings')
def user_settings():
    '''Настройки пользователя, а также его персональный данные'''
    return render_template('customer/settings.html', title='Настройки')


@login_required
@customer_bp.route('/edit_settings', methods=['GET', 'POST'])
def edit_settings():
    form = EditFormUser(
        user_name=current_user.name,
        email=current_user.email
    )

    if form.validate_on_submit():
        email = form.email.data
        user_name = form.user_name.data
        avatar = form.avatar.data
        password = form.password.data
        repeat_password = form.repeat_password.data

        if password != repeat_password:
            flash(message='Пароли не совпадают!', category='danger')
            return render_template('customer/edit_settings.html', title='Редактирование', form=form)

        # Нужно будет добавить проверку почты

        change_data = {}

        if password:
            change_data['password'] = password

        if user_name:
            change_data['name'] = user_name

        if avatar:
            img_name = upload_img_user(avatar)
            if img_name:
                change_data['img'] = img_name

        if email and current_user.email != email.strip():
            change_data['email'] = email

        api_url = request.url_root + f'api/users/{current_user.id}'
        resp = requests.patch(
            api_url,
            json=change_data,
            cookies=request.cookies
        )

        if resp.status_code == 200:
            flash(message='Вы изменили данные аккаунта!', category='success')
            return redirect(url_for('customer.index'))

        else:
            error = resp.json().get('message', 'Ошибка регистрации')
            flash(error, category='danger')
            return render_template('customer/edit_settings.html', title='Редактирование', form=form)

    return render_template('customer/edit_settings.html', title='Редактирование', form=form)