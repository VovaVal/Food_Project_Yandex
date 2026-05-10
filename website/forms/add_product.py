from flask_wtf import FlaskForm
from flask_wtf.file import MultipleFileField, FileAllowed
from wtforms import SubmitField
from wtforms.fields.choices import SelectField
from wtforms.fields.numeric import IntegerField
from wtforms.fields.simple import StringField
from wtforms.validators import Optional, DataRequired, NumberRange, InputRequired


class AddProduct(FlaskForm):
    product_name = StringField('Название продукта', validators=[DataRequired()])
    description = StringField('Описание продукта', validators=[Optional()])
    quantity = IntegerField('Кол.-во продукта',
                            validators=[
                                InputRequired(message='Введите количество'),
                                NumberRange(min=0, message='Кол.-во не может быть отрицательным')
                            ],
                            default=0)  # кол.-во товара
    price = IntegerField('Цена продукта',
                         validators=[
                             InputRequired(message='Введите цену'),
                             NumberRange(min=0, message='Цена не может быть отрицательной')
                         ],
                         default=100)
    # Тип товара
    product_type = SelectField('Тип продукта',
                       choices=[('drink', 'напиток'), ('bakery', 'выпечка'),
                                ('dessert', 'десерт'), ('other', 'другое')],
                       default='other')
    imgs = MultipleFileField('Фотографии продукта',
                             validators=[
                                 Optional(),
                                 FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'webp'],
                                             'Только изображения!')
                             ])
    save = SubmitField('Добавить')