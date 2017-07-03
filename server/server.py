from __future__ import print_function
from pymongo import MongoClient
from flask import Flask, request, session, g, redirect, url_for, abort, \
    render_template, flash, jsonify
from flaskext.sass import sass
from dateutil.relativedelta import relativedelta

from queries.fund_summary import fund_summary_query, process_fund_summary
from queries.funders import funders_query
from queries.amounts import amounts_query
from queries.durations import durations_query

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

# styling
sass(app, input_dir='assets/scss', output_dir='css')
#app.add_url_rule('/favicon.ico',
#                 redirect_to=url_for('static', filename='favicon.ico'))


@app.route('/')
def index():
    return render_template('index.html', ga_key=app.config['GA_KEY'])


@app.route('/examples')
def examples():
    return render_template('examples.html', ga_key=app.config['GA_KEY'])





@app.route('/grant/<grant_id>')
def grant(grant_id=None):
    grant = db.grants.find_one({"_id": grant_id})
    return jsonify(grant)


@app.route('/funders')
def funder():
    funders = db.grants.aggregate(funders_query())
    return jsonify(list(funders))


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
    latest_date = db.grants.aggregate([
        {"$match": {
            "fund_slug": fund_slug,
        }},
        {"$group": {
            "_id": "$fund_slug",
            "period_end": {"$max": "$awardDate"},
        }}
    ])
    latest_date = list(latest_date)[0]["period_end"]
    one_year_before = latest_date - relativedelta(months=12)

    grants = db.grants.aggregate(fund_summary_query(fund_slug, one_year_before))
    fund_summary = list(grants)[0]
    fund_summary = process_fund_summary(fund_summary)
    return jsonify(fund_summary)
