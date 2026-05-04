from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user

from website.bucket_requests import upload_logo_shop
from website.data import db_session
from website.data.shops import Shops
from website.forms.add_shop import AddShop

shop_bp = Blueprint(
    'shop',
    __name__
)

@shop_bp.before_request
def check_role():
    if not current_user.is_authenticated or current_user.role != 'shop':
        return redirect(url_for('auth.login'))

@login_required
@shop_bp.route('/dashboard')
def dashboard():
    with db_session.create_session() as sess:
        shops = sess.query(Shops).filter(Shops.user_id == current_user.id)

    return render_template('shop/dashboard.html', user=current_user, shops=shops)


@login_required
@shop_bp.route('/add_shop', methods=['GET', 'POST'])
def add_shop():
    form = AddShop()

    if form.validate_on_submit():
        shop_name = form.shop_name.data
        logo = form.logo.data

        data = {
            'name': shop_name,
            'user_id': current_user.id
        }

        with db_session.create_session() as sess:
            shop = Shops(
                **data
            )

            sess.add(shop)
            sess.commit()

            if logo:
                img_name = upload_logo_shop(logo, shop)
                if img_name:
                    shop.logo = img_name
                    sess.commit()

        return redirect(url_for('shop.dashboard'))

    return render_template('shop/add_shop.html', title='Создание магазина', form=form)


@login_required
@shop_bp.route('/products')
def products():
    return render_template('shop/products.html')


@login_required
@shop_bp.route('/')
def index():
    return redirect(url_for('shop.dashboard'))


@login_required
@shop_bp.route('/settings')
def shop_settings():
    return render_template('shop/settings.html')


@login_required
@shop_bp.route('/edit_settings')
def edit_settings():
    return render_template('shop/edit_settings.html')