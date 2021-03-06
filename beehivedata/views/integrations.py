from flask import Blueprint, render_template, jsonify, request
from dateutil.relativedelta import relativedelta
from datetime import datetime
from flask_login import login_required
import re

from ..db import get_db
from ..assets.beneficiaries import theme_regexes
from ..assets.queries.fund_summary import fund_summary_query, process_fund_summary
from ..assets.queries.amounts import amounts_query
from ..assets.queries.durations import durations_query
from ..assets.queries.themes import themes_query
from ..assets.name_parse import parse_name

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

    conditions = [
        {"grants_made": {"$gte": int(request.values.get("min_size", 100000))}},
        {"activities": "MAKES GRANTS TO ORGANISATIONS"},
        {"active": True}
    ]

    limit = max(int(request.values.get("limit", 50)),1000)

    if request.values.get("country"):
        conditions.append({"areas.iso3166_1": {"$in": request.values.get("country").split(",")}})

    for i in ["beneficiaries", "activities", "purpose"]:
        if request.values.get(i):
            conditions.append({i: {"$in": request.values.get(i).split(",")}})

    grant_makers = db.charities.find({"$and": conditions}, sort=[("grants_made", -1)], limit=limit)

    grant_makers = [get_funder_info(g) for g in grant_makers]

    return jsonify(grant_makers)


def get_funder_info(funder):

    funder["name"] = parse_name(funder["name"])

    new_funder = {
        "name": funder["name"],
        "reg_number": funder["reg_number"],
        "website": funder.get("web"),
        "countries": list(set([a["iso3166_1"] for a in funder.get("areas", [])])),
        "districts": list(set([a["oldCode"] for a in funder.get("areas", []) if a.get("oldCode", "") != ""])),
        "geo_area": funder.get("geo_area")
    }

    description = ""

    # location
    location = funder.get("geo_area", funder["operating_location"].lower())
    if location is None:
        location = funder.get("operating_location", "").lower()
    elif location.lower() == "worldwide":
        location = "worldwide"
    else:
        location = "in {}".format(location)

    # purposes
    purposes = ""
    if len(funder.get("purpose", [])) == 1:
        purposes = " on {}.".format(funder["purpose"][0].lower())
    elif len(funder.get("purpose", [])) > 1:
        purposes = "\r\n".join([" - {}".format(i[0].upper() + i[1:].lower())
                for i in funder["purpose"]])
        purposes = " on the following themes: \r\n\r\n{}\r\n".format(purposes)

    description += "{} works {}{}\r\n\r\n".format(
        funder["name"], 
        location,
        purposes
    )

    # grant amounts
    description += "In the year ending {:%B %Y} they made grants worth £{:,.0f}.".format(funder["fye"], funder["grants_made"])
    new_funder["description"] = description

    # themes
    new_funder["themes"] = list(
        set([r for r in theme_regexes if re.search(theme_regexes[r], description, re.I)]))

    return new_funder
