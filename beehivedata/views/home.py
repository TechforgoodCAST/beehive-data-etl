from flask import Blueprint, render_template, jsonify
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
    grants = sum([f["count"] for f in funds])
    return render_template('status.html', funds=list(funds), fields=FIELDS_TO_CHECK, funders=funders, grants=grants)


@home.route('/datasets')
def datasets():
    db = get_db()
    files = db.files.find()
    return render_template('datasets.html', files=list(files))


@home.route('/datasets/<fileid>.json')
def dataset(fileid):
    db = get_db()
    grants = db.grants.find({'dataset.id': fileid})
    return jsonify({"grants": list(grants)})


@home.route('/sharealike_data')
def sharealike():
    db = get_db()
    files = db.files.find(
        {"license": "https://creativecommons.org/licenses/by-sa/4.0/"})
    return render_template('sharealike.html', files=list(files))
