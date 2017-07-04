from flask import Blueprint, render_template

home = Blueprint('home', __name__)


@home.route('/')
def index():
    return render_template('index.html')


@home.route('/examples')
def examples():
    return render_template('examples.html')
