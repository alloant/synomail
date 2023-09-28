# forms.py

from app.models.user import User

from wtforms import Form, BooleanField, StringField, PasswordField, validators

class LoginForm(Form):
    alias = StringField('User', [validators.Length(min=3, max=25)])
    password = PasswordField('Password', [validators.DataRequired()])

class RegistrationForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=40)])
    alias = StringField('User', [validators.Length(min=3, max=25)])
    email = StringField('Email Address')
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match')
    ])
    u_groups = StringField('Groups')
    active = BooleanField('User is active')
    admin_active = StringField('Admin mode on')
    confirm = PasswordField('Repeat Password')

class UserForm(Form):
    name = StringField('Name', [validators.Length(min=4, max=40)])
    alias = StringField('User', [validators.Length(min=3, max=25)])
    email = StringField('Email Address')
    u_groups = StringField('Groups')
    active = BooleanField('User is active')
    admin_active = StringField('Admin mode on')
    
