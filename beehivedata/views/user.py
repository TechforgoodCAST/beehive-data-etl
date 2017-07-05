from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_user, logout_user, login_required

from ..login import User
from .forms import LoginForm
from ..db import get_db

user = Blueprint('user', __name__)


@user.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'POST' and form.validate_on_submit():
        db = get_db()
        user = db[current_app.config['USERS_COLLECTION']].find_one({"email": form.email.data})
        if user and User.validate_login(user['password'], form.password.data):
            user_obj = User(str(user['_id']), user["email"])
            login_user(user_obj)
            flash("Logged in successfully!", category='success')
            return redirect(request.args.get("next") or url_for("home.index"))
        flash("Wrong username or password!", category='error')
    return render_template('login.html', title='login', form=form)


@user.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))
