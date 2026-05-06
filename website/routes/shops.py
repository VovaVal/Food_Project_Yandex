import datetime

import requests
from flask import Blueprint, render_template, redirect, url_for, request
from flask_login import login_required, current_user

from website.bucket_requests import upload_logo_shop, upload_img_shop, delete_by_key
from website.data import db_session
from website.data.shops import Shops
from website.forms.add_shop import AddShop
from website.forms.edit_shop import EditShop
from website.config import BUCKET_CLIENT

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
@shop_bp.route('/<int:shop_id>')
def shop_id_settings(shop_id: int):
    api_url = request.url_root + f'api/shops/{shop_id}'
    shop_data = requests.get(api_url, cookies=request.cookies)
    if shop_data.status_code != 200:
        redirect(url_for('shop.dashboard'))

    shop_data = shop_data.json()['shop']
    return render_template('shop/shop_settings.html', title=shop_data['name'], shop=shop_data)


@login_required
@shop_bp.route('/edit_settings_shop/<int:shop_id>', methods=['GET', 'POST'])
def edit_settings_shop(shop_id: int):
    with db_session.create_session() as sess:
        shop = sess.get(Shops, shop_id)

    form = EditShop(
        shop_name=shop.name,
        address=shop.address,
        description=shop.description,
        coords=shop.coords,
        delivery_radius=shop.delivery_radius
    )

    if form.validate_on_submit():
        shop_name = form.shop_name.data
        delivery_radius = form.delivery_radius.data
        address = form.address.data
        coords = form.coords.data
        description = form.description.data
        logo = form.logo.data
        imgs = request.files.getlist('imgs')

        schedule = {
            'monday': {
                'from': request.form.get('monday_from'),  # '08:00', '00:00' или ''
                'to': request.form.get('monday_to')
            },
            'tuesday': {
                'from': request.form.get('tuesday_from'),
                'to': request.form.get('tuesday_to')
            },
            'wednesday': {
                'from': request.form.get('wednesday_from'),
                'to': request.form.get('wednesday_to')
            },
            'thursday': {
                'from': request.form.get('thursday_from'),
                'to': request.form.get('thursday_to')
            },
            'friday': {
                'from': request.form.get('friday_from'),
                'to': request.form.get('friday_to')
            },
            'saturday': {
                'from': request.form.get('saturday_from'),
                'to': request.form.get('saturday_to')
            },
            'sunday': {
                'from': request.form.get('sunday_from'),
                'to': request.form.get('sunday_to')
            },
        }
        print(schedule)

        data = {
            'name': shop_name,
            'address': address,
            'coords': coords,
            'description': description,
            'delivery_radius': int(delivery_radius) if delivery_radius.is_integer() else 0
        }

        if logo:
            img_name = upload_logo_shop(logo, shop)
            if img_name:
                data['logo'] = img_name

        img_names = []
        for img in imgs:
            print('name: ', img)
            img_name = upload_img_shop(img)
            if img_name:
                img_names.append(img_name)

        if img_names:
            data['imgs'] = (','.join('' if not shop.imgs or shop.imgs is None else shop.imgs.split(',')) + ',' + ','.join(img_names)).strip(',')

        api_url = request.url_root + f'api/shops/{shop_id}'
        shop_data = requests.patch(api_url, json=data, cookies=request.cookies)
        if shop_data.status_code != 200:
            print('Ошибка при изменении данных!!!')

        return redirect(url_for('shop.shop_id_settings', shop_id=shop_id))

    imgs = shop.imgs
    if imgs:
        imgs = imgs.split(',')
    else:
        imgs = []

    print(imgs)
    return render_template('shop/edit_shop_settings.html', title='Редактирование',
                           form=form, shop_id=shop_id, images=imgs, BUCKET_CLIENT=BUCKET_CLIENT)


@shop_bp.route('/delete_image/<int:shop_id>', methods=['POST'])
@login_required
def delete_shop_image(shop_id):
    img = request.form.get('img')

    with db_session.create_session() as sess:
        shop = sess.get(Shops, shop_id)

        if not shop or not img:
            return redirect(url_for('shop.shop_id_settings', shop_id=shop_id))

        # удаляем из S3
        if img != 'shops/imgs/shop_img_default.jpg':
            delete_by_key(img)

        imgs = shop.imgs.split(',') if shop.imgs else []

        if img in imgs:
            imgs.remove(img)

        shop.imgs = ','.join(imgs) if imgs else None
        shop.updated_date = datetime.datetime.now()

        sess.commit()

    return redirect(url_for('shop.shop_id_settings', shop_id=shop_id))


@shop_bp.route('/upload_images/<int:shop_id>', methods=['POST'])
@login_required
def upload_shop_images(shop_id):
    files = request.files.getlist('imgs')

    with db_session.create_session() as sess:
        shop = sess.get(Shops, shop_id)

        imgs = shop.imgs.split(',') if shop.imgs else []

        for file in files:
            if file and file.filename:
                img_name = upload_img_shop(file)
                if img_name:
                    imgs.append(img_name)

        shop.imgs = ','.join(imgs)
        shop.updated_date = datetime.datetime.now()
        sess.commit()

    return {"success": True}


@shop_bp.route('/upload_logo/<int:shop_id>', methods=['POST'])
@login_required
def upload_logo(shop_id):
    file = request.files.get('logo')

    if not file:
        return {"success": False}, 400

    with db_session.create_session() as sess:
        shop = sess.get(Shops, shop_id)

        if not shop:
            return {"success": False}, 404

        img_name = upload_logo_shop(file, shop)

        if img_name:
            shop.logo = img_name
            shop.updated_date = datetime.datetime.now()
            sess.commit()

    return {"success": True}


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
def shop_owner_settings():
    return render_template('shop/owner_settings.html')


@login_required
@shop_bp.route('/edit_settings')
def edit_settings():
    return render_template('shop/edit_settings.html')