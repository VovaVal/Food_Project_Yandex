from flask_wtf import FlaskForm
from wtforms import PasswordField, SubmitField, EmailField, FileField
from wtforms.fields.simple import StringField
from wtforms.validators import Optional, EqualTo, Email, Length, DataRequired


class EditFormUser(FlaskForm):
    user_name = StringField('Имя пользователя', validators=[Optional()])
    email = EmailField('Почта', validators=[Optional(), Email()])
    address = StringField('Адрес дома', validators=[DataRequired(message='Адрес обязателен')])
    coords = StringField('Координаты дома', validators=[DataRequired(message='Координаты обязательны')])
    avatar = FileField('Аватар', validators=[Optional()])
    password = PasswordField('Пароль', validators=[Optional(), Length(min=6)])
    repeat_password = PasswordField('Повторите пароль', validators=[Optional(), EqualTo('password', message='Пароли должны совпадать')])
    save = SubmitField('Сохранить')