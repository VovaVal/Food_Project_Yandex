from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField, SelectField
from wtforms.validators import DataRequired


class Register(FlaskForm):
    email = EmailField('Почта', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    repeat_password = PasswordField('Повторите пароль', validators=[DataRequired()])
    role = SelectField('Ваш статус',
                       choices=[('customer', 'покупатель'), ('shop', 'владелец заведения')],
                       default='customer')
    submit = SubmitField('Отправить')