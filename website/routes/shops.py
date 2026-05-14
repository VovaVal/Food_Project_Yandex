import datetime

import requests
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from website.bucket_requests import upload_logo_shop, upload_img_shop, delete_by_key, upload_img_user, \
    upload_img_product
from website.data import db_session
from website.data.order_items import OrderItems
from website.data.orders import Orders
from website.data.products import Products
from website.data.reviews_shop import ReviewsShop
from website.data.shops import Shops
from website.data.users import User
from website.forms.add_product import AddProduct
from website.forms.add_shop import AddShop
from website.forms.edit_product import EditProduct
from website.forms.edit_shop import EditShop
from website.config import BUCKET_CLIENT
from website.forms.edit_shop_user_settings import EditFormShopUser


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

    return render_template('shop/dashboard.html', user=current_user, shops=shops, title='Главная')


@login_required
@shop_bp.route('/add_shop', methods=['GET', 'POST'])
def add_shop():
    form = AddShop()

    if form.validate_on_submit():
        shop_name = form.shop_name.data
        logo = form.logo.data

        schedule = {
            'monday': {
                'from': '',
                'to': ''
            },
            'tuesday': {
                'from': '',
                'to': ''
            },
            'wednesday': {
                'from': '',
                'to': ''
            },
            'thursday': {
                'from': '',
                'to': ''
            },
            'friday': {
                'from': '',
                'to': ''
            },
            'saturday': {
                'from': '',
                'to': ''
            },
            'sunday': {
                'from': '',
                'to': ''
            },
        }

        data = {
            'name': shop_name,
            'user_id': current_user.id,
            'timetable': schedule
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
    api_url = 'http://127.0.0.1:5000/' + f'api/shops/{shop_id}'
    shop_data = requests.get(api_url, cookies=request.cookies, verify=False, allow_redirects=True)
    if shop_data.status_code != 200:
        redirect(url_for('shop.dashboard'))

    days_ru = {
        'monday': 'Понедельник',
        'tuesday': 'Вторник',
        'wednesday': 'Среда',
        'thursday': 'Четверг',
        'friday': 'Пятница',
        'saturday': 'Суббота',
        'sunday': 'Воскресенье'
    }

    with db_session.create_session() as sess:
        shop = sess.get(Shops, shop_id)

        if not shop:
            return redirect(url_for('shop.dashboard'))

        reviews = sess.query(ReviewsShop).filter(
            ReviewsShop.shop_id == shop_id
        ).options(joinedload(ReviewsShop.user)).all()
        reviews = sorted(reviews, key=lambda x: x.created_date, reverse=True)

    shop_data = shop_data.json()['shop']
    return render_template('shop/shop_settings.html', title=shop_data['name'],
                           shop=shop_data, days_ru=days_ru, is_shop_open=is_shop_open, get_next_closing_time=get_next_closing_time,
                           get_next_opening_time=get_next_opening_time, reviews=reviews)


def get_current_day_name():
    """Возвращает название текущего дня недели на английском"""
    days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    return days[datetime.datetime.now().weekday()]


def is_shop_open(shop):
    """Проверяет, открыт ли магазин прямо сейчас"""
    if not shop['timetable']:
        return False

    try:
        import json
        if isinstance(shop['timetable'], str):
            timetable = json.loads(shop['timetable'])
        else:
            timetable = shop['timetable']
    except:
        return False

    current_day = get_current_day_name()
    current_time = datetime.datetime.now().strftime('%H:%M')

    day_schedule = timetable.get(current_day, {})
    from_time = day_schedule.get('from', '')
    to_time = day_schedule.get('to', '')

    if not from_time or not to_time:
        return False
    if from_time == '' and to_time == '':
        return False
    if from_time == '00:00' and to_time == '23:59':
        return True

    return from_time <= current_time <= to_time


def get_next_closing_time(shop):
    """Возвращает время закрытия магазина"""
    if not shop['timetable']:
        return None

    try:
        import json
        if isinstance(shop['timetable'], str):
            timetable = json.loads(shop['timetable'])
        else:
            timetable = shop['timetable']
    except:
        return None

    current_day = get_current_day_name()
    day_schedule = timetable.get(current_day, {})
    return day_schedule.get('to', None)


def get_next_opening_time(shop):
    """Возвращает время следующего открытия"""
    if not shop['timetable']:
        return None

    try:
        import json
        if isinstance(shop['timetable'], str):
            timetable = json.loads(shop['timetable'])
        else:
            timetable = shop['timetable']
    except:
        return None

    days_order = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    current_day_index = datetime.datetime.now().weekday()

    # Проверяем сегодняшний день
    for i in range(8):
        check_index = (current_day_index + i) % 7
        day = days_order[check_index]
        day_schedule = timetable.get(day, {})
        from_time = day_schedule.get('from', '')

        if from_time and from_time != '':
            if i == 0:
                if is_shop_open(shop):
                    return f"сегодня в {from_time}"
                else:
                    continue
            elif i == 1:
                return f"завтра в {from_time}"
            else:
                days_ru = ['понедельник', 'вторник', 'среду', 'четверг', 'пятницу', 'субботу', 'воскресенье']
                return f"в {days_ru[check_index]} в {from_time}"

    return None


@shop_bp.context_processor
def utility_processor():
    def is_open_now(day, from_time, to_time):
        """Проверяет, открыт ли магазин прямо сейчас для конкретного дня"""
        if not from_time or not to_time:
            return False
        if from_time == '' and to_time == '':
            return False

        now = datetime.datetime.now()
        current_time = now.strftime('%H:%M')

        weekdays = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        current_day = weekdays[now.weekday()]

        if current_day != day:
            return False

        return from_time <= current_time <= to_time

    return dict(
        is_open_now=is_open_now,
        is_shop_open=is_shop_open,
        get_next_closing_time=get_next_closing_time,
        get_next_opening_time=get_next_opening_time
    )


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
        delivery_radius=abs(shop.delivery_radius)
    )

    if form.validate_on_submit():
        shop_name = form.shop_name.data
        delivery_radius = abs(form.delivery_radius.data)
        address = form.address.data
        coords = form.coords.data
        description = form.description.data
        logo = form.logo.data
        imgs = request.files.getlist('imgs')

        schedule = {
            'monday': {
                'from': request.form.get('monday_from'),
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
            'delivery_radius': float(delivery_radius),
            'timetable': schedule
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

        api_url = 'http://127.0.0.1:5000/' + f'api/shops/{shop_id}'
        shop_data = requests.patch(api_url, json=data, cookies=request.cookies, verify=False, allow_redirects=True)
        if shop_data.status_code != 200:
            print('Ошибка при изменении данных!!!')

        return redirect(url_for('shop.shop_id_settings', shop_id=shop_id))

    imgs = shop.imgs
    if imgs:
        imgs = imgs.split(',')
    else:
        imgs = []

    return render_template('shop/edit_shop_settings.html', title='Редактирование',
                           form=form, shop_id=shop_id, images=imgs, BUCKET_CLIENT=BUCKET_CLIENT, shop=shop)


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
@shop_bp.route('/delete_shop/<int:shop_id>')
def delete_shop(shop_id: int):
    api_url = 'http://127.0.0.1:5000/' + f'api/shops/{shop_id}'
    shop_data = requests.delete(api_url, cookies=request.cookies, verify=False, allow_redirects=True)

    if shop_data.status_code != 200:
        print(shop_data.status_code)
        print(shop_data.reason)

    return redirect(url_for('shop.dashboard'))


@login_required
@shop_bp.route('/update_avatar', methods=['POST'])
def update_avatar():
    file = request.files.get('avatar')

    if not file:
        return {"success": False}, 400

    img_name = upload_img_user(file)

    try:
        if img_name:
            with db_session.create_session() as sess:
                user = sess.get(User, current_user.id)
                user.img = img_name

                sess.add(user)
                sess.commit()

    except Exception as e:
        print(e)
        return {'success': False}

    return {"success": True}


@login_required
@shop_bp.route('/')
def index():
    return redirect(url_for('shop.dashboard'))


@login_required
@shop_bp.route('/settings')
def shop_owner_settings():
    return render_template('shop/owner_settings.html', title='Настройки')


@login_required
@shop_bp.route('/edit_settings', methods=['GET', 'POST'])
def edit_settings():
    form = EditFormShopUser(
        user_name=current_user.name,
        email=current_user.email
    )

    if form.validate_on_submit():
        user_name = form.user_name.data
        email = form.email.data
        avatar = form.avatar.data
        password = form.password.data
        repeat_password = form.repeat_password.data

        if password != repeat_password:
            flash(message='Пароли не совпадают!', category='danger')
            return render_template('shop/edit_settings.html', title='Редактирование', form=form)

        # Нужно будет добавить проверку почты

        change_data = {
            'name': user_name,
            'email': email
        }

        if password:
            change_data['password'] = password

        if avatar:
            img_name = upload_img_user(avatar)
            if img_name:
                change_data['img'] = img_name

        api_url = 'http://127.0.0.1:5000/' + f'api/users/{current_user.id}'
        resp = requests.patch(
            api_url,
            json=change_data,
            cookies=request.cookies,
            verify=False,
            allow_redirects=True
        )

        if resp.status_code == 200:
            flash(message='Вы изменили данные аккаунта!', category='success')
            return redirect(url_for('shop.shop_owner_settings'))

        else:
            error = resp.json().get('message', 'Ошибка регистрации')
            flash(error, category='danger')
            return render_template('shop/edit_settings.html', title='Редактирование', form=form)

    return render_template('shop/edit_settings.html', form=form, title='Редактирование')


@login_required
@shop_bp.route('/<int:shop_id>/products')
def products(shop_id: int):
    with db_session.create_session() as sess:
        shop = sess.get(Shops, shop_id)
        shop_products = shop.products

    if not shop:
        return redirect(url_for('shop.dashboard'))

    return render_template('shop/shop_products.html', title='Продукты', shop_products=shop_products,
                           shop_id=shop_id)


@login_required
@shop_bp.route('/<int:shop_id>/add_product', methods=['GET', 'POST'])
def add_product(shop_id: int):
    form = AddProduct()

    if form.validate_on_submit():
        name = form.product_name.data
        description = form.description.data
        quantity = form.quantity.data
        price = form.price.data
        product_type = form.product_type.data
        product_weight = form.product_weight.data
        type_of_count = form.type_of_count.data
        imgs = request.files.getlist('imgs')

        data = {
            'name': name,
            'description': description,
            'quantity': quantity,
            'price': price,
            'product_type': product_type,
            'shop_id': shop_id,
            'product_weight': product_weight,
            'type_of_count': type_of_count
        }

        img_names = []
        for img in imgs:
            print('name: ', img)
            img_name = upload_img_product(img)
            if img_name:
                img_names.append(img_name)

        if img_names:
            data['imgs'] = ','.join(img_names)
        else:
            data['imgs'] = 'products/imgs/product_img_default.png'

        with db_session.create_session() as sess:
            product = Products(
                **data
            )

            sess.add(product)
            sess.commit()

        return redirect(url_for('shop.products', shop_id=shop_id))

    return render_template('shop/add_product.html', title='Добавление', form=form, shop_id=shop_id)


@login_required
@shop_bp.route('/<int:shop_id>/delete_product_image/<int:product_id>', methods=['POST'])
def delete_product_image(product_id: int, shop_id: int):
    img = request.form.get('img_url')

    with db_session.create_session() as sess:
        product = sess.get(Products, product_id)

        if not product or not img:
            return redirect(url_for('shop.products', shop_id=shop_id))

        # удаляем из S3
        if img and img != 'products/imgs/product_img_default.png':
            delete_by_key(img)

        imgs = product.imgs.split(',') if product.imgs else []

        if img in imgs:
            imgs.remove(img)

        product.imgs = ','.join(imgs) if imgs else None

        sess.add(product)
        sess.commit()

    return redirect(url_for('shop.products', shop_id=shop_id))


@login_required
@shop_bp.route('/<int:shop_id>/upload_product_images/<int:product_id>', methods=['POST'])
def upload_product_images(product_id: int, shop_id: int):
    files = request.files.getlist('images')

    with db_session.create_session() as sess:
        product = sess.get(Products, product_id)

        if not product or not files:
            return {"success": False}

        imgs = product.imgs.split(',') if product.imgs else []

        for file in files:
            if file and file.filename:
                img_name = upload_img_product(file)

                if img_name:
                    imgs.append(img_name)

        product.imgs = ','.join(imgs)

        sess.add(product)
        sess.commit()

    return {"success": True}


@login_required
@shop_bp.route('/<int:shop_id>/delete_product/<int:product_id>')
def delete_product(shop_id: int, product_id: int):
    api_url = 'http://127.0.0.1:5000/' + f'api/products/{product_id}'
    product_data = requests.delete(api_url, cookies=request.cookies, verify=False, allow_redirects=True)

    if product_data.status_code != 200:
        print(product_data.status_code)
        print(product_data.reason)

    return redirect(url_for('shop.products', shop_id=shop_id))


@login_required
@shop_bp.route('/<int:shop_id>/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(shop_id: int, product_id: int):
    with db_session.create_session() as sess:
        product = sess.get(Products, product_id)

    form = EditProduct(
        product_name=product.name,
        description=product.description,
        quantity=product.quantity,
        price=product.price,
        product_type=product.product_type,
        product_weight=product.product_weight,
        type_of_count=product.type_of_count
    )

    if form.validate_on_submit():
        name = form.product_name.data
        description = form.description.data
        quantity = form.quantity.data
        price = form.price.data
        product_type = form.product_type.data
        product_weight = form.product_weight.data
        type_of_count = form.type_of_count.data
        imgs = request.files.getlist('imgs')

        data = {
            'name': name,
            'description': description,
            'quantity': quantity,
            'price': price,
            'product_type': product_type,
            'shop_id': shop_id,
            'product_weight': product_weight,
            'type_of_count': type_of_count
        }

        img_names = []
        for img in imgs:
            print('name: ', img)
            img_name = upload_img_product(img)
            if img_name:
                img_names.append(img_name)

        if img_names:
            data['imgs'] = (','.join('' if not product.imgs or product.imgs is None else product.imgs.split(',')) + ',' + ','.join(img_names)).strip(',')

        api_url = 'http://127.0.0.1:5000/' + f'api/products/{product_id}'
        resp = requests.patch(
            api_url,
            json=data,
            cookies=request.cookies,
            verify=False,
            allow_redirects=True
        )

        if resp.status_code == 200:
            flash(message='Вы изменили данные продукта!', category='success')
            return redirect(url_for('shop.products', shop_id=shop_id))

        else:
            print('Error!!!')
            print(resp.status_code)
            print(resp.reason)
            return render_template('shop/edit_product.html', form=form,
                                   title='Редактирование', shop_id=shop_id)

    return render_template('shop/edit_product.html', form=form,
                           title='Редактирование', shop_id=shop_id)


@login_required
@shop_bp.route('/<int:shop_id>/orders')
def orders(shop_id: int):
    with db_session.create_session() as sess:
        shop = sess.get(Shops, shop_id)

        if not shop:
            return redirect(url_for('shop.dashboard'))

        orders = sess.query(Orders).filter(Orders.shop_id == shop_id).order_by(Orders.created_date.desc()).all()

        return render_template('shop/shop_orders.html', title='Заказы',
                               orders=orders, shop_id=shop_id)


@login_required
@shop_bp.route('/<int:shop_id>/order/<int:order_id>')
def order_page(order_id: int, shop_id: int):
    with db_session.create_session() as sess:
        order = sess.query(Orders).options(
            joinedload(Orders.order_items).joinedload(OrderItems.product),
            joinedload(Orders.shop)
        ).filter(Orders.id == order_id, Orders.shop_id == shop_id).first()

        if not order:
            flash("Заказ не найден", "danger")
            return redirect(url_for('shop.orders'))

        return render_template('shop/shop_order_details.html',
                               title=f'Заказ №{order.id}',
                               order=order,
                               shop_id=shop_id
                               )


@login_required
@shop_bp.route('/<int:shop_id>/order/cancel/<int:order_id>', methods=['POST'])
def cancel_order(order_id: int, shop_id: int):
    with db_session.create_session() as sess:
        order = sess.query(Orders).filter(Orders.id == order_id, Orders.shop_id == shop_id).first()

        if not order:
            return jsonify({'success': False, 'message': 'Заказ не найден'}), 404

        if order.status != 'active':
            return jsonify({'success': False, 'message': 'Можно отменить только активный заказ'}), 400

        order.status = 'cancelled'

        user = sess.get(User, current_user.id)

        if user:
            user.user_bonuses += order.user_bonuses

        order_items = order.order_items
        for item in order_items:
            product = sess.get(Products, item.product_id)

            # возвращаем товары, которые заказали
            if product:
                product.quantity += item.quantity

                sess.add(product)

        sess.commit()

        return jsonify({'success': True})


@login_required
@shop_bp.route('/order/verify_code/<int:order_id>', methods=['POST'])
def verify_code(order_id):
    data = request.get_json()
    input_code = data.get('code')

    with db_session.create_session() as sess:
        order = sess.query(Orders).filter(Orders.id == order_id).first()

        if not order:
            return jsonify({'success': False, 'message': 'Заказ не найден'}), 404

        if order.status != 'active':
            return jsonify({'success': False, 'message': 'Заказ уже обработан'}), 400

        c_code = order.confirm_code

        if c_code.lower().strip() == input_code.lower().strip():
            order.status = 'completed'

            bonuses = int(order.price * 0.1)

            user = sess.get(User, order.user_id)
            if user:
                user.user_bonuses += bonuses
                sess.add(user)

            sess.add(order)
            sess.commit()
            return jsonify({'success': True})

        else:
            return jsonify({'success': False, 'message': 'Неверный код подтверждения'})