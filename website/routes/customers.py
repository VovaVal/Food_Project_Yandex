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

@customer_bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('customer/dashboard.html', user=current_user)

@customer_bp.route('/orders')
@login_required
def orders():
    return render_template('customer/orders.html')