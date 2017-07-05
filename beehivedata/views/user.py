from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, session
from flask_login import login_user, logout_user, login_required

from ..login import User, register_user
from .forms import LoginForm, RegisterForm
from ..db import get_db

user = Blueprint('user', __name__)


@user.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        db = get_db()
        user = db[current_app.config['USERS_COLLECTION']].find_one({"email": form.email.data})
        if user and User.validate_login(user['password'], form.password.data):
            user_obj = User(user['_id'], user)
            login_user(user_obj)
            flash("Logged in successfully!", category='success')
            return redirect(request.args.get("next") or url_for("home.index"))
        flash("Wrong username or password!", category='error')
    return render_template('login.html', title='login', form=form)


@user.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if request.method == 'POST' and form.validate_on_submit():
        db = get_db()
        try:
            register_user(form.email.data, form.password.data, form.name.data)
            flash("User created", category='success')
        except DuplicateKeyError:
            flash("User already exists with that email address", category='error')
    return render_template('register.html', title='register', form=form)


@user.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('user.login'))
