from flask import Blueprint, render_template
from flask_login import login_required

from ..db import get_db
from ..assets.queries.status import status_query, FIELDS_TO_CHECK, process_fund

home = Blueprint('home', __name__)


@home.route('/')
def index():
    return render_template('index.html')


@home.route('/examples')
def examples():
    return render_template('examples.html')


@home.route('/status')
@login_required
def status():
    db = get_db()
    funds = db.grants.aggregate(status_query())
    funds = [process_fund(f) for f in funds]
    funders = set([f["funder"] for f in funds])
    return render_template('status.html', funds=list(funds), fields=FIELDS_TO_CHECK, funders=funders)
