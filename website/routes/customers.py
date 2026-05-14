import datetime
import uuid

import requests
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload

from website.data.cart import Cart
from website.data.order_items import OrderItems
from website.data.orders import Orders
from website.data.products import Products
from website.data.reviews_product import ReviewsProduct
from website.data.reviews_shop import ReviewsShop
from website.data.shops import Shops
from website.data.users import User
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
        cookies=request.cookies,
        verify=False
    )

    if resp.status_code == 200:
        data = resp.json()
        shops = data.get('shops', [])
        shops1 = []
        for shop in shops:
            if (not shop['address'] or shop['address'] is None) or (not shop['coords'] or shop['coords'] is None):
                continue
            else:
                shops1.append(shop)

        shops = shops1

        return render_template('customer/dashboard.html', title='Главно окно', user=current_user, shops=shops)
    else:
        return render_template('errors/error.html', title='Ошибка',
                               error_code=500, error_message='Internal server error'), 500


@login_required
@customer_bp.route('/shop_page/<int:shop_id>')
def shop_page(shop_id: int):
    api_url = request.url_root + f'api/shops/{shop_id}'
    resp = requests.get(
        api_url,
        cookies=request.cookies,
        verify=False
    )
    print(resp)

    days_ru = {
        'monday': 'Понедельник',
        'tuesday': 'Вторник',
        'wednesday': 'Среда',
        'thursday': 'Четверг',
        'friday': 'Пятница',
        'saturday': 'Суббота',
        'sunday': 'Воскресенье'
    }

    if resp.status_code == 200:
        shop = resp.json()['shop']
        fl = False  # есть ли отзыв

        if (not shop['address'] or shop['address'] is None) or (not shop['coords'] or shop['coords'] is None):
            return redirect(url_for('customer.dashboard'))

        with db_session.create_session() as sess:
            user = sess.get(User, shop['user_id'])

            reviews = sess.query(ReviewsShop).filter(
                ReviewsShop.shop_id == shop_id
            ).options(joinedload(ReviewsShop.user)).all()

            reviews = sorted(
                reviews,
                key=lambda x: (x.user_id != current_user.id, x.created_date),
                reverse=True
            )

            p_review = sess.query(ReviewsShop).filter(
                ReviewsShop.shop_id == shop_id, ReviewsShop.user_id == current_user.id
            ).first()

            if p_review:
                fl = True

        if shop.get('coords'):
            try:
                coords = shop['coords'].split(',')
                shop['lat'] = float(coords[0].strip())
                shop['lng'] = float(coords[1].strip())
            except:
                # Москва
                shop['lat'] = 55.751244
                shop['lng'] = 37.618423
        else:
            # Москва
            shop['lat'] = 55.751244
            shop['lng'] = 37.618423

        return render_template('customer/shop_page.html', title=shop['name'], reviews=reviews,
                               shop=shop, email=user.email, days_ru=days_ru, is_shop_open=is_shop_open, fl=fl,
                               get_next_closing_time=get_next_closing_time, get_next_opening_time=get_next_opening_time)
    else:
        print('Error occurred!!!')
        print(resp.status_code)
        print(resp.reason)
        return redirect(url_for('customer.dashboard'))


@login_required
@customer_bp.route('/shop_products/<int:shop_id>')
def shop_products(shop_id: int):
    with db_session.create_session() as sess:
        shop = sess.get(Shops, shop_id)

        if not shop:
            return redirect(url_for('customer.dashboard'))

        shop_products = shop.products

        cart_items = sess.query(Cart).filter(Cart.user_id == current_user.id).all()
        user_cart = {item.product_id: item.quantity for item in cart_items}

    if not shop:
        return redirect(url_for('customer.dashboard'))

    if (not shop.address or shop.address is None) or (not shop.coords or shop.coords is None):
        return redirect(url_for('customer.dashboard'))

    return render_template('customer/shop_products.html', title='Товары', shop_id=shop_id,
                           shop_products=shop_products, user_cart=user_cart)


@login_required
@customer_bp.route('/shop_products/<int:shop_id>/product/<int:product_id>')
def product_page(shop_id: int, product_id: int):
    fl = False

    with db_session.create_session() as sess:
        product = sess.get(Products, product_id)

        if not product:
            return redirect(url_for('customer.dashboard'))

        shop = sess.get(Shops, product.shop_id)

        if not shop:
            return redirect(url_for('customer.dashboard'))

        if (not shop.address or shop.address is None) or (not shop.coords or shop.coords is None):
            return redirect(url_for('customer.dashboard'))

        if shop.id != product.shop_id:
            return redirect(url_for('customer.dashboard'))

        shop = sess.get(Shops, shop_id)

        if not shop:
            return redirect(url_for('customer.dashboard'))

        if (not shop.address or shop.address is None) or (not shop.coords or shop.coords is None):
            return redirect(url_for('customer.dashboard'))

        if shop.id != product.shop_id:
            return redirect(url_for('customer.dashboard'))

        reviews = sess.query(ReviewsProduct).filter(
            ReviewsProduct.product_id == product_id
        ).options(joinedload(ReviewsProduct.user)).all()

        reviews = sorted(
            reviews,
            key=lambda x: (x.user_id != current_user.id, x.created_date),
            reverse=True
        )

        p_review = sess.query(ReviewsProduct).filter(
            ReviewsProduct.product_id == product_id, ReviewsProduct.user_id == current_user.id
        ).first()

        if p_review:
            fl = True

        cart_item = sess.query(Cart).filter(Cart.user_id == current_user.id,
                                             Cart.product_id == product_id).first()
        quantity = cart_item.quantity if cart_item else 0
        user_cart = {product_id: quantity}

        return render_template('customer/product_page.html', shop_id=shop_id,
                               product=product, title=product.name, user_cart=user_cart,
                               fl=fl, reviews=reviews)


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
        email=current_user.email,
        address=current_user.address,
        coords=current_user.coords
    )

    if form.validate_on_submit():
        email = form.email.data
        user_name = form.user_name.data
        address = form.address.data
        coords = form.coords.data
        avatar = form.avatar.data
        password = form.password.data
        repeat_password = form.repeat_password.data

        if password != repeat_password:
            flash(message='Пароли не совпадают!', category='danger')
            return render_template('customer/edit_settings.html', title='Редактирование', form=form)

        # Нужно будет добавить проверку почты

        change_data = {
            'address': address,
            'coords': coords
        }

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
            cookies=request.cookies,
            verify=False
        )

        if resp.status_code == 200:
            flash(message='Вы изменили данные аккаунта!', category='success')
            return redirect(url_for('customer.user_settings'))

        else:
            error = resp.json().get('message', 'Ошибка регистрации')
            flash(error, category='danger')
            return render_template('customer/edit_settings.html', title='Редактирование', form=form)

    return render_template('customer/edit_settings.html', title='Редактирование', form=form)


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


@customer_bp.context_processor
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


@customer_bp.route('/upload_avatar', methods=['POST'])
@login_required
def upload_avatar():
    '''Загружает аватар'''
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


@customer_bp.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json()
    product_id = data.get('product_id')
    quantity = data.get('quantity', 0)

    with db_session.create_session() as sess:
        product = sess.get(Products, product_id)
        if not product:
            return jsonify({'success': False, 'message': 'Товар не обнаружен'})

        cart_item = sess.query(Cart).filter(
            Cart.user_id == current_user.id,
            Cart.product_id == product_id
        ).first()

        # Если количество 0 — удаляем товар из корзины
        if quantity <= 0:
            if cart_item:
                sess.delete(cart_item)
                sess.commit()
            return jsonify({'success': True, 'message': 'Товар удален из корзины'})

        if quantity > product.quantity:
            return jsonify({'success': False, 'message': f'Доступно только {product.quantity} шт.'})

        if cart_item:
            cart_item.quantity = quantity

        else:
            cart_item = Cart(
                user_id=current_user.id,
                product_id=product_id,
                quantity=quantity
            )
            sess.add(cart_item)

        sess.commit()

    return jsonify({'success': True})


@login_required
@customer_bp.route('/cart_page')
def cart_page():
    with db_session.create_session() as sess:
        # Загружаем корзину вместе с продуктами
        cart_items = sess.query(Cart).options(
            joinedload(Cart.product)
        ).filter(Cart.user_id == current_user.id).all()

        grouped_cart = {}

        for item in cart_items:
            if item.product:
                _ = item.product.name
                shop = sess.get(Shops, item.product.shop_id)

                if shop:
                    shop_data_for_check = {
                        'timetable': shop.timetable
                    }
                    is_open = is_shop_open(shop_data_for_check)

                    if shop.id not in grouped_cart:
                        grouped_cart[shop.id] = {
                            'shop_name': shop.name,
                            'is_active': is_open,
                            'timetable': shop.timetable,
                            'radius': shop.delivery_radius,
                            'items': []
                        }

                    if item.active != is_open:
                        item.active = is_open

                    grouped_cart[shop.id]['items'].append(item)

        sess.commit()

        # Сортируем: сначала активные магазины, потом закрытые
        sorted_grouped_cart = dict(sorted(
            grouped_cart.items(),
            key=lambda x: x[1]['is_active'],
            reverse=True
        ))

        return render_template('customer/cart_page.html',
                               grouped_cart=sorted_grouped_cart,
                               title='Корзина', is_shop_open=is_shop_open)


@login_required
@customer_bp.route('/checkout')
def checkout():
    with db_session.create_session() as sess:
        cart_items = sess.query(Cart).options(
            joinedload(Cart.product)
        ).filter(Cart.user_id == current_user.id).all()

        grouped_cart = {}
        is_product_active = False  # есть ли хотя бы один активный товар(открыт ли магазин сейчас)

        for item in cart_items:
            if item.product:
                _ = item.product.name
                shop = sess.get(Shops, item.product.shop_id)

                if shop:
                    shop_data_for_check = {
                        'timetable': shop.timetable
                    }
                    is_open = is_shop_open(shop_data_for_check)

                    if shop.id not in grouped_cart:
                        if shop.coords:
                            try:
                                coords = shop.coords.split(',')
                                lat = float(coords[0].strip())
                                lng = float(coords[1].strip())
                            except:
                                # Москва
                                lat = 55.751244
                                lng = 37.618423
                        else:
                            # Москва
                            lat = 55.751244
                            lng = 37.618423

                        grouped_cart[shop.id] = {
                            'shop_name': shop.name,
                            'is_active': is_open,
                            'timetable': shop.timetable,
                            'radius': shop.delivery_radius,
                            'items': [],
                            'lat': lat,
                            'lng': lng
                        }

                    if item.active != is_open:
                        item.active = is_open

                    if item.active:
                        is_product_active = True

                    grouped_cart[shop.id]['items'].append(item)

        sess.commit()

        if not is_product_active:  # если нет активных товаров
            return redirect(url_for('customer.cart_page'))

        return render_template('customer/checkout.html',
                               grouped_cart=grouped_cart,
                               title='Заказ')


@login_required
@customer_bp.route('/final_checkout', methods=['GET', 'POST'])
def final_checkout():
    '''Последний этап заказа'''
    if request.method == 'POST':
        delivery_data = request.get_json()
        print(delivery_data)

        session['delivery_data'] = delivery_data

        return jsonify({'success': True, 'redirect_url': url_for('customer.final_checkout')})

    with db_session.create_session() as sess:
        cart_items = sess.query(Cart).options(
            joinedload(Cart.product)
        ).filter(Cart.user_id == current_user.id).all()

        grouped_cart = {}
        is_product_active = False  # есть ли хотя бы один активный товар(открыт ли магазин сейчас)

        for item in cart_items:
            if item.product:
                _ = item.product.name
                shop = sess.get(Shops, item.product.shop_id)

                if shop:
                    shop_data_for_check = {
                        'timetable': shop.timetable
                    }
                    is_open = is_shop_open(shop_data_for_check)

                    if shop.id not in grouped_cart:
                        if shop.coords:
                            try:
                                coords = shop.coords.split(',')
                                lat = float(coords[0].strip())
                                lng = float(coords[1].strip())
                            except:
                                # Москва
                                lat = 55.751244
                                lng = 37.618423
                        else:
                            # Москва
                            lat = 55.751244
                            lng = 37.618423

                        grouped_cart[shop.id] = {
                            'shop_name': shop.name,
                            'is_active': is_open,
                            'timetable': shop.timetable,
                            'radius': shop.delivery_radius,
                            'items': [],
                            'lat': lat,
                            'lng': lng
                        }

                    if item.active != is_open:
                        item.active = is_open

                    if item.active:
                        is_product_active = True

                    grouped_cart[shop.id]['items'].append(item)

        sess.commit()

        if not is_product_active:
            return redirect(url_for('customer.cart_page'))

        delivery_data = session.get('delivery_data', {})
        print(delivery_data)
        return render_template('customer/final_checkout.html', delivery_data=delivery_data,
                               title='Заказ', grouped_cart=grouped_cart)


@customer_bp.route('/create_order', methods=['POST'])
@login_required
def create_order():
    data = request.get_json()
    delivery_data = session.get('delivery_data', {})
    print(data)

    if not delivery_data:
        return jsonify({'success': False, 'message': 'Данные о доставке потеряны'})

    with db_session.create_session() as sess:
        cart_items = sess.query(Cart).filter(Cart.user_id == current_user.id,
                                             Cart.active == True).all()
        if not cart_items:
            return jsonify({'success': False, 'message': 'Корзина пуста'})

        items_by_shop = {}
        for item in cart_items:
            sid = item.product.shop_id
            if sid not in items_by_shop:
                items_by_shop[sid] = []
            items_by_shop[sid].append(item)

        user = sess.get(User, current_user.id)
        discount_to_use = float(data.get('discount_used', 0))
        if discount_to_use > user.user_bonuses:
            discount_to_use = user.user_bonuses

        user.user_bonuses -= discount_to_use
        sess.add(user)

        created_orders = []
        for shop_id, items in items_by_shop.items():
            shop_total = 0

            for item in items:
                shop_total += item.quantity * item.product.price
                product = sess.get(Products, item.product.id)

                # уменьшаем кол.-во товаров
                if product:
                    product.quantity -= item.quantity
                    sess.add(product)

            method = delivery_data.get(str(shop_id), 'pickup')

            if discount_to_use <= shop_total:
                bonuses = discount_to_use
                discount_to_use = 0
                shop_total -= bonuses
            else:
                bonuses = shop_total
                discount_to_use -= bonuses
                shop_total = 0

            description = data['description'].get(str(shop_id), '')

            if current_user.coords:
                order = Orders(
                    user_id=current_user.id,
                    shop_id=shop_id,
                    price=shop_total,
                    status='active',
                    delivery_type=method,
                    created_date=datetime.datetime.now(),
                    type_of_payment='cash',
                    address=current_user.address,
                    coords=current_user.coords,
                    confirm_code=uuid.uuid4().hex[:6],
                    user_bonuses=bonuses,
                    description=description
                )
            else:
                order = Orders(
                    user_id=current_user.id,
                    shop_id=shop_id,
                    price=shop_total,
                    status='active',
                    delivery_type=method,
                    created_date=datetime.datetime.now(),
                    type_of_payment='cash',
                    confirm_code=uuid.uuid4().hex[:6],
                    user_bonuses=bonuses,
                    description=description
                )

            sess.add(order)
            sess.flush()

            for cart_item in items:
                order_item = OrderItems(
                    product_id=cart_item.product_id,
                    order_id=order.id,
                    quantity=cart_item.quantity,
                    name=cart_item.product.name,
                    price=cart_item.product.price
                )
                sess.add(order_item)

            created_orders.append(order)

        sess.query(Cart).filter(Cart.user_id == current_user.id, Cart.active == True).delete()

        session.pop('delivery_data', None)  # удаляем из сесси инфо о доставке
        sess.commit()

    return jsonify({'success': True})


@login_required
@customer_bp.route('/orders')
def orders():
    with db_session.create_session() as sess:
        orders = sess.query(Orders).filter(Orders.user_id == current_user.id).order_by(Orders.created_date.desc()).all()

        return render_template('customer/orders_page.html', title='Заказы', orders=orders)


@login_required
@customer_bp.route('/order/<int:order_id>')
def order_page(order_id: int):
    with db_session.create_session() as sess:
        order = sess.query(Orders).options(
            joinedload(Orders.order_items).joinedload(OrderItems.product),
            joinedload(Orders.shop)
        ).filter(Orders.id == order_id, Orders.user_id == current_user.id).first()

        if not order:
            flash("Заказ не найден", "danger")
            return redirect(url_for('customer.orders'))

        return render_template('customer/order_details.html',
                               title=f'Заказ №{order.id}',
                               order=order,
                               secret_code=order.confirm_code)


@login_required
@customer_bp.route('/order/cancel/<int:order_id>', methods=['POST'])
def cancel_order(order_id: int):
    with db_session.create_session() as sess:
        order = sess.query(Orders).filter(Orders.id == order_id, Orders.user_id == current_user.id).first()

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
@customer_bp.route('/order/arrived/<int:order_id>', methods=['POST'])
def order_arrived(order_id):
    print(order_id, 'order_id')
    with db_session.create_session() as sess:
        order = sess.query(Orders).filter(Orders.id == order_id, Orders.user_id == current_user.id).first()
        if order:
            order.delivery_arrived = True  # если курьер доехал
            sess.commit()

            return {"success": True}

        return {"success": False, "message": "Order not found"}, 404


@login_required
@customer_bp.route('/order/update_comment/<int:order_id>', methods=['POST'])
def update_order_comment(order_id):
    data = request.get_json()
    new_description = data.get('description', '')

    with db_session.create_session() as sess:
        order = sess.query(Orders).filter(
            Orders.id == order_id,
            Orders.user_id == current_user.id
        ).first()

        if not order:
            return jsonify({'success': False, 'message': 'Заказ не найден'}), 404

        if order.status != 'active':
             return jsonify({'success': False, 'message': 'Нельзя менять комментарий завершенного заказа'}), 400

        order.description = new_description

        sess.add(order)
        sess.commit()

    return jsonify({'success': True})


@login_required
@customer_bp.route('/api/shops/<int:shop_id>/reviews', methods=['POST'])
def add_shop_review(shop_id):
    data = request.get_json()
    text = data.get('review_text')
    rating = data.get('rating', 5)

    if not text:
        return jsonify({'success': False, 'message': 'Текст пустой'}), 400

    with db_session.create_session() as sess:
        shop = sess.get(Shops, shop_id)
        if not shop:
            return jsonify({'success': False})

        user_already_has_review = sess.query(ReviewsShop).filter(ReviewsShop.user_id == current_user.id,
                                                                 ReviewsShop.shop_id == shop_id).first()

        if user_already_has_review:
            return jsonify({'success': False})

        new_review = ReviewsShop(
            shop_id=shop_id,
            user_id=current_user.id,
            review_text=text,
            rate=int(rating)
        )

        sess.add(new_review)
        sess.commit()

    recount_shop_rate(shop_id)

    return jsonify({'success': True})


@login_required
@customer_bp.route('/api/reviews/<int:review_id>/edit', methods=['POST'])
def edit_review(review_id):
    data = request.get_json()
    text = data.get('review_text')
    rating = data.get('rating')

    with db_session.create_session() as sess:
        review = sess.get(ReviewsShop, review_id)

        if review and review.user_id == current_user.id:
            review.review_text = text

            if rating:
                review.rate = int(rating)

            shop_id = review.shop_id

            sess.add(review)
            sess.commit()

            recount_shop_rate(shop_id)

            return jsonify({'success': True})

    return jsonify({'success': False}), 403


@login_required
@customer_bp.route('/api/reviews/<int:review_id>/delete', methods=['POST'])
def delete_review(review_id):
    with db_session.create_session() as sess:
        review = sess.get(ReviewsShop, review_id)

        if review and review.user_id == current_user.id:
            sess.delete(review)
            sess.commit()

            shop_id = review.shop_id

            recount_shop_rate(shop_id)

            return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'Доступ запрещен или отзыв не найден'}), 403


def recount_shop_rate(shop_id: int):
    with db_session.create_session() as sess:
        shop = sess.get(Shops, shop_id)

        if not shop:
            return jsonify({'success': False})

        reviews = shop.reviews
        if len(reviews) == 0:
            rate = 0
        else:
            rate = round(sum(i.rate for i in reviews) / len(reviews), 1)

        shop.rate = rate
        sess.add(shop)
        sess.commit()

    return jsonify({'success': True})


@login_required
@customer_bp.route('/api/products/<int:product_id>/reviews', methods=['POST'])
def add_product_review(product_id):
    data = request.get_json()
    text = data.get('review_text')
    rating = data.get('rating', 5)

    if not text:
        return jsonify({'success': False, 'message': 'Текст пустой'}), 400

    with db_session.create_session() as sess:
        product = sess.get(Products, product_id)
        if not product:
            return jsonify({'success': False})

        user_already_has_review = sess.query(ReviewsProduct).filter(ReviewsProduct.user_id == current_user.id,
                                                                 ReviewsProduct.product_id == product_id).first()

        if user_already_has_review:
            return jsonify({'success': False})

        new_review = ReviewsProduct(
            product_id=product_id,
            user_id=current_user.id,
            review_text=text,
            rate=int(rating)
        )

        sess.add(new_review)
        sess.commit()

    recount_product_rate(product_id)

    return jsonify({'success': True})


@login_required
@customer_bp.route('/api/product/reviews/<int:review_id>/edit', methods=['POST'])
def edit_product_review(review_id):
    data = request.get_json()
    text = data.get('review_text')
    rating = data.get('rating')

    with db_session.create_session() as sess:
        review = sess.get(ReviewsProduct, review_id)

        if review and review.user_id == current_user.id:
            review.review_text = text

            if rating:
                review.rate = int(rating)

            product_id = review.product_id

            sess.add(review)
            sess.commit()

            recount_product_rate(product_id)

            return jsonify({'success': True})

    return jsonify({'success': False}), 403


@login_required
@customer_bp.route('/api/product/reviews/<int:review_id>/delete', methods=['POST'])
def delete_product_review(review_id):
    with db_session.create_session() as sess:
        review = sess.get(ReviewsProduct, review_id)

        if review and review.user_id == current_user.id:
            sess.delete(review)
            sess.commit()

            product_id = review.product_id

            recount_product_rate(product_id)

            return jsonify({'success': True})

    return jsonify({'success': False, 'message': 'Доступ запрещен или отзыв не найден'}), 403


def recount_product_rate(product_id: int):
    with db_session.create_session() as sess:
        product = sess.get(Products, product_id)

        if not product:
            return jsonify({'success': False})

        reviews = product.reviews
        if len(reviews) == 0:
            rate = 0
        else:
            rate = round(sum(i.rate for i in reviews) / len(reviews), 1)

        product.rate = rate
        sess.add(product)
        sess.commit()

    return jsonify({'success': True})