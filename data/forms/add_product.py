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
        ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'),('5', '5'),
        ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'),
        ('11', '11'), ('12', '12'),
    ], coerce=int, validators=[DataRequired()])
    sowing_month_end = SelectField('Sowing_month_end', choices=[
        ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
        ('6', '6'), ('7', '7'), ('8', '8'), ('9', '9'), ('10', '10'),
        ('11', '11'), ('12', '12'),
    ], coerce=int, validators=[DataRequired()])
    submit = SubmitField('Create product')


