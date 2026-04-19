from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, IntegerField
from wtforms.validators import DataRequired


class AddProductForm(FlaskForm):
    name = StringField('Name of product', validators=[DataRequired()])
    price = IntegerField('Price', validators=[DataRequired()])
    stock = IntegerField('Stock', validators=[DataRequired()])
    description = StringField('Description', validators=[DataRequired()])
    category_id = SelectField('Категория', coerce=int, validators=[DataRequired()])
    difficulty = SelectField('Сложность', choices=[
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    ], validators=[DataRequired()])
    sowing_month_start = SelectField('Sowing_month_start', choices=[
        ('1', 'Январь'), ('2', 'Февраль'), ('3', 'Март'), ('4', 'Апрель'),('5', 'Май'),
        ('6', 'Июнь'), ('7', 'Июль'), ('8', 'Август'), ('9', 'Сентябрь'), ('10', 'Октябрь'),
        ('11', 'Ноябрь'), ('12', 'Декабрь'),
    ], coerce=int, validators=[DataRequired()])
    sowing_month_end = SelectField('Sowing_month_end', choices=[
        ('1', 'Январь'), ('2', 'Февраль'), ('3', 'Март'), ('4', 'Апрель'),('5', 'Май'),
        ('6', 'Июнь'), ('7', 'Июль'), ('8', 'Август'), ('9', 'Сентябрь'), ('10', 'Октябрь'),
        ('11', 'Ноябрь'), ('12', 'Декабрь'),
    ], coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create product')


