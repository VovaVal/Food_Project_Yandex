from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user


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
    return render_template('customer/dashboard.html', user=current_user)

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
@customer_bp.route('/edit_settings')
def edit_settings():
    ...