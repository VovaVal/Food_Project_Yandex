from flask import Blueprint, redirect, url_for
from flask_login import current_user, login_required


bp_common = Blueprint(
    'common',
    __name__
)

@bp_common.route('/')
def index():
    if current_user.is_authenticated:
        match current_user.role:
            case 'customer':
                return redirect(url_for('customer.dashboard'))
            case 'shop':
                return redirect(url_for('shop.dashboard'))
            case 'admin':
                return redirect(url_for('admin.dashboard'))
    else:
        return redirect(url_for('auth.login'))


@login_required
@bp_common.route('/settings')
def settings():
    if current_user.is_authenticated:
        match current_user.role:
            case 'customer':
                return redirect(url_for('customer.user_settings'))
            case 'shop':
                return redirect(url_for('shop.shop_settings'))


@login_required
@bp_common.route('/dashboard')
def dashboard():
    if current_user.is_authenticated:
        match current_user.role:
            case 'customer':
                return redirect(url_for('customer.dashboard'))
            case 'shop':
                return redirect(url_for('shop.dashboard'))
    else:
        return redirect(url_for('auth.login'))