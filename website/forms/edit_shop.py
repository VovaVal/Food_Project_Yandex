from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import SubmitField, FileField
from wtforms.fields.datetime import TimeField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField
from wtforms.validators import Optional, DataRequired, Length, NumberRange, InputRequired


class EditShop(FlaskForm):
    shop_name = StringField('Название магазина',
                            validators=[
                                DataRequired(message='Название обязательно'),
                                Length(max=100, message='Максимум 100 символов')
                            ])
    delivery_radius = IntegerField('Радиус доставки магазина(в метрах)',
                          validators=[
                              InputRequired(message='Введите радиус доставки'),
                              NumberRange(min=0, message='Радиус не может быть отрицательным')
                          ])
    address = StringField('Адрес магазина', validators=[DataRequired(message='Адрес обязателен')])
    coords = StringField('Координаты магазина', validators=[DataRequired(message='Координаты обязательны')])
    description = StringField('Описание магазина',
                              validators=[
                                  Optional(),
                                  Length(max=500, message='Максимум 500 символов')
                              ])
    monday_from = TimeField('Понедельник: с', validators=[Optional()])
    monday_to = TimeField('Понедельник: до', validators=[Optional()])

    tuesday_from = TimeField('Вторник: с', validators=[Optional()])
    tuesday_to = TimeField('Вторник: до', validators=[Optional()])

    wednesday_from = TimeField('Среда: с', validators=[Optional()])
    wednesday_to = TimeField('Среда: до', validators=[Optional()])

    thursday_from = TimeField('Четверг: с', validators=[Optional()])
    thursday_to = TimeField('Четверг: до', validators=[Optional()])

    friday_from = TimeField('Пятница: с', validators=[Optional()])
    friday_to = TimeField('Пятница: до', validators=[Optional()])

    saturday_from = TimeField('Суббота: с', validators=[Optional()])
    saturday_to = TimeField('Суббота: до', validators=[Optional()])

    sunday_from = TimeField('Воскресенье: с', validators=[Optional()])
    sunday_to = TimeField('Воскресенье: до', validators=[Optional()])

    logo = FileField('Лого',
                     validators=[
                         Optional(),
                         FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Только изображения!')
                     ])
    imgs = MultipleFileField('Фотографии кофейни',
                             validators=[
                                 Optional(),
                                 FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'], 'Только изображения!')
                             ])
    save = SubmitField('Сохранить')