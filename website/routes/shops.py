from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

shop_bp = Blueprint(
    'shop',
    __name__
)

@shop_bp.before_request
def check_role():
    if not current_user.is_authenticated or current_user.role != 'shop':
        return redirect(url_for('auth.login'))

@shop_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('shop/dashboard.html', user=current_user)

@shop_bp.route('/products')
@login_required
def products():
    return render_template('shop/products.html')