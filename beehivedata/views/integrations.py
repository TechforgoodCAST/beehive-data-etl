from flask import Blueprint, render_template, jsonify, request
from dateutil.relativedelta import relativedelta
from datetime import datetime
from flask_login import login_required

from ..db import get_db
from ..assets.queries.fund_summary import fund_summary_query, process_fund_summary
from ..assets.queries.amounts import amounts_query
from ..assets.queries.durations import durations_query
from ..assets.queries.themes import themes_query

integrations = Blueprint('integrations', __name__)


@integrations.route('/amounts')
@login_required
def amounts():
    db = get_db()
    amounts = db.grants.aggregate(amounts_query())
    return jsonify(list(amounts))


@integrations.route('/durations')
@login_required
def durations():
    db = get_db()
    durations = db.grants.aggregate(durations_query())
    return jsonify(list(durations))


@integrations.route('/themes')
@login_required
def themes():
    db = get_db()
    themes = db.grants.aggregate(themes_query())
    return jsonify(list(themes))


def get_fund_data(fund_slug=None, convert_dates=False):
    db = get_db()
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
    fund_summary = process_fund_summary(fund_summary, convert_dates)
    return fund_summary


@integrations.route('/fund_summary/<fund_slug>')
@login_required
def fund_summary(fund_slug=None):
    return jsonify(get_fund_data(fund_slug))


@integrations.route('/funders')
@login_required
def funds():
    db = get_db()

    conditions = {
        "grants_made": {"$gte": 100000},
        "activities": "MAKES GRANTS TO ORGANISATIONS",
        "active": True
    }

    if request.values.get("country"):
        conditions["areas.iso3166_1"] = {"$in": request.values.get("country").split(",")}

    for i in ["beneficiaries", "activities", "purpose"]:
        if request.values.get(i):
            conditions[i] = {"$in": request.values.get(i).split(",")}

    grant_makers = db.charities.find(conditions, sort=[("grants_made", -1)], limit=50)
    return jsonify(list(grant_makers))
