from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Required, Email, EqualTo


class LoginForm(FlaskForm):
    """Login form to access writing and settings pages"""

    email = StringField('Email', validators=[Required(), Email()])
    password = PasswordField('Password', validators=[Required()])


class RegisterForm(FlaskForm):
    """Form to register a new user"""

    name = StringField('Name', validators=[Required()])
    email = StringField('Email', validators=[Required(), Email()])
    password = PasswordField('Password', [Required(), EqualTo('confirm', message='Passwords must match')])
    confirm = PasswordField('Confirm password')
