from __future__ import print_function
from pymongo import MongoClient, ASCENDING, DESCENDING
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, jsonify
from flaskext.sass import sass
from dateutil.relativedelta import relativedelta
from datetime import datetime

from queries.fund_summary import fund_summary_query, process_fund_summary
from queries.funders import funders_query
from queries.amounts import amounts_query
from queries.durations import durations_query

from recommender import Recommender

app = Flask(__name__)  # create the application instance :)
app.config.from_object(__name__)  # load config from this file , flaskr.py

# Load default config and override config from an environment variable
app.config.update(dict(
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    MONGO_PORT=27017,
    MONGO_HOST='localhost',
    MONGO_DB='360giving',
    GA_KEY='UA-30021098-3'
))
app.config.from_envvar('FLASKR_SETTINGS', silent=True)

client = MongoClient(app.config["MONGO_HOST"], app.config["MONGO_PORT"])
db = client[app.config["MONGO_DB"]]
app.logger.info("Connected to '%s' mongo database [host: %s, port: %s]" % (
    app.config["MONGO_DB"],
    app.config["MONGO_HOST"],
    app.config["MONGO_PORT"]
))

recommender = Recommender(db=db)

# styling
sass(app, input_dir='assets/scss', output_dir='css')
# app.add_url_rule('/favicon.ico',
#                  redirect_to=url_for('static', filename='favicon.ico'))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/examples')
def examples():
    return render_template('examples.html')


@app.route('/charity/<charity_no>')
@app.route('/charity/<charity_no>.json')
def charity(charity_no):
    grants = db.grants.find({'recipientOrganization.charityNumber': charity_no})\
               .sort("awardDate", DESCENDING)
    return jsonify(list(grants))


@app.route('/charity/<charity_no>.html')
def charity_html(charity_no):
    grants = db.grants.find({'recipientOrganization.charityNumber': charity_no})\
               .sort("awardDate", DESCENDING)
    grants = list(grants)
    charity = charity_no
    names = [g.get("recipientOrganization", [{}])[0].get("name") for g in grants]
    names = [n for n in names if n is not None]
    if len(names) > 0:
        charity = names[0]
    return render_template('charity.html', grants=grants, charity=charity)


@app.route('/grant/<grant_id>')
@app.route('/grant/<grant_id>.json')
def grant(grant_id=None):
    grant = db.grants.find_one({"_id": grant_id})
    return jsonify(grant)


@app.route('/funders')
def funders():
    funders = db.grants.aggregate(funders_query())
    return jsonify(list(funders))


@app.route('/funders.html')
def funders_html():
    funders = db.grants.aggregate(funders_query())
    return render_template('funders.html', funders=list(funders))


@app.route('/funder/<funder_id>')
@app.route('/funder/<funder_id>.json')
def funder(funder_id=None):
    grants = db.grants.find({'fundingOrganization.id': funder_id})\
               .sort("awardDate", DESCENDING)
    return jsonify(list(grants))


@app.route('/integrations/amounts')
def amounts():
    amounts = db.grants.aggregate(amounts_query())
    return jsonify(list(amounts))


@app.route('/integrations/durations')
def durations():
    durations = db.grants.aggregate(durations_query())
    return jsonify(list(durations))


@app.route('/integrations/fund_summary/<fund_slug>')
def fund_summary(fund_slug=None):
    latest_date = list(db.grants.aggregate([
        {"$match": {
            "fund_slug": fund_slug,
        }},
        {"$group": {
            "_id": "$fund_slug",
            "period_end": {"$max": "$awardDate"},
        }}
    ]))
    if len(latest_date) > 0:
        latest_date = latest_date[0]["period_end"]
    else:
        latest_date = datetime.now()
    one_year_before = latest_date - relativedelta(months=12)

    grants = db.grants.aggregate(fund_summary_query(fund_slug, one_year_before))
    fund_summary = list(grants)[0]
    fund_summary = process_fund_summary(fund_summary)
    return jsonify(fund_summary)


# Beehive insight
@app.route('/insight/beneficiaries', methods=['POST'])
# @auth.login_required
def insight_beneficiaries():
    data = request.json['data']
    result = recommender.check_beneficiaries(data)
    return jsonify(result)


@app.route('/insight/amounts', methods=['POST'])
# @auth.login_required
def insight_amounts():
    data = request.json['data']['amount']
    result = recommender.check_amounts(data)
    return jsonify(result)


@app.route('/insight/durations', methods=['POST'])
# @auth.login_required
def insight_durations():
    data = request.json['data']['duration']
    result = recommender.check_durations(data)
    return jsonify(result)


@app.route('/insight/all', methods=['POST'])
# @auth.login_required
def insight_all():
    bens = recommender.check_beneficiaries(request.json['data'].get("beneficiaries", {}))
    amounts = recommender.check_amounts(request.json['data'].get("amount", None))
    durations = recommender.check_durations(request.json['data'].get("duration", None))
    funds = set(list(bens.keys()) + list(amounts.keys()) + list(durations.keys()))
    return jsonify({f: {
        "beneficiaries": bens.get(f, 0),
        "amounts": amounts.get(f, 0),
        "durations": durations.get(f, 0),
    } for f in funds})
