import datetime
import io

import requests
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from PIL import Image

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
        cookies=request.cookies
    )

    if resp.status_code == 200:
        data = resp.json()
        shops = data.get('shops', [])

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
        cookies=request.cookies
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

        with db_session.create_session() as sess:
            user = sess.get(User, shop['user_id'])

        if shop.get('coords'):
            try:
                coords = shop['coords'].split(',')
                shop['lat'] = float(coords[0].strip())
                shop['lng'] = float(coords[1].strip())
            except:
                shop['lat'] = 55.751244
                shop['lng'] = 37.618423
        else:
            shop['lat'] = 55.751244
            shop['lng'] = 37.618423

        return render_template('customer/shop_page.html', title=shop['name'],
                               shop=shop, email=user.email, days_ru=days_ru, is_shop_open=is_shop_open,
                               get_next_closing_time=get_next_closing_time, get_next_opening_time=get_next_opening_time)
    else:
        print('Error occurred!!!')
        print(resp.status_code)
        print(resp.reason)
        return redirect('customer.dashboard')


@login_required
@customer_bp.route('/shop_products/<int:shop_id>')
def shop_products(shop_id: int):
    ...


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
            cookies=request.cookies
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
    for i in range(7):
        check_index = (current_day_index + i) % 7
        day = days_order[check_index]
        day_schedule = timetable.get(day, {})
        from_time = day_schedule.get('from', '')

        if from_time and from_time != '':
            if i == 0:
                return f"сегодня в {from_time}"
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