from flask import Blueprint, redirect, url_for
from flask_login import current_user

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