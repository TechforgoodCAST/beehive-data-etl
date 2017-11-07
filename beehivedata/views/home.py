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


@home.route('/sources')
def sources():
    db = get_db()
    sharealike_files = db.files.find(
        {"license": "https://creativecommons.org/licenses/by-sa/4.0/"})
    sources = db.files.find()
    charities = db.charities.aggregate([
        {"$group": {"_id": "$source", "count": {"$sum": 1}}}
    ])
    charities = list(charities)
    num_charities = sum([c["count"] for c in charities])

    regulators = [
        {
            "name": "Charity Commission for England and Wales",
            "source": "http://data.charitycommission.gov.uk/",
            "license": {
                "name": "Open Government Licence v3.0",
                "url": "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
            }
        },
        {
            "name": "Office of the Scottish Charity Regulator",
            "source": "https://www.oscr.org.uk/charities/search-scottish-charity-register/charity-register-download",
            "license": {
                "name": "Open Government Licence v2.0",
                "url": "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/2/",
            }
        },
        {
            "name": "Charity Commission Northern Ireland",
            "source": "http://www.charitycommissionni.org.uk/charity-search/"
        },
    ]
    for r in regulators:
        r["charities"] = sum([c["count"] for c in charities if c["_id"] == r["name"]])

    return render_template('sources.html', sources=list(sources), 
                                           sharealike_files=list(sharealike_files), 
                                           num_charities=num_charities,
                                           regulators=regulators)
