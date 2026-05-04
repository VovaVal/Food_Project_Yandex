from flask_wtf import FlaskForm
from wtforms import SubmitField, FileField
from wtforms.fields.simple import StringField
from wtforms.validators import Optional, DataRequired


class AddShop(FlaskForm):
    shop_name = StringField('Название магазина', validators=[DataRequired()])
    logo = FileField('Лого', validators=[Optional()])
    save = SubmitField('Добавить')