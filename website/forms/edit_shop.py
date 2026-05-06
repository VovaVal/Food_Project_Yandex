from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, MultipleFileField
from wtforms import SubmitField, FileField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField
from wtforms.validators import Optional, DataRequired, Length


class EditShop(FlaskForm):
    shop_name = StringField('Название магазина',
                            validators=[
                                DataRequired(message='Название обязательно'),
                                Length(max=100, message='Максимум 100 символов')
                            ])
    delivery_radius = IntegerField('Радиус доставки магазина',
                          validators=[
                              DataRequired(message='Введите радиус доставки')
                          ])
    address = StringField('Адрес магазина', validators=[DataRequired(message='Адрес обязателен')])
    coords = StringField('Координаты магазина', validators=[DataRequired(message='Координаты обязательны')])
    description = StringField('Описание магазина',
                              validators=[
                                  Optional(),
                                  Length(max=500, message='Максимум 500 символов')
                              ])
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