from flask import Blueprint, render_template, jsonify
from pymongo import ASCENDING, DESCENDING

from ..db import get_db
from ..assets.queries.funders import funders_query

api = Blueprint('api', __name__)


@api.route('/charity/<charity_no>')
@api.route('/charity/<charity_no>.json')
def charity(charity_no):
    db = get_db()
    grants = db.grants.find({'recipientOrganization.charityNumber': charity_no})\
               .sort("awardDate", DESCENDING)
    return jsonify(list(grants))


@api.route('/charity/<charity_no>.html')
def charity_html(charity_no):
    db = get_db()
    grants = db.grants.find({'recipientOrganization.charityNumber': charity_no})\
               .sort("awardDate", DESCENDING)
    grants = list(grants)
    charity = charity_no
    names = [g.get("recipientOrganization", [{}])[0].get("name") for g in grants]
    names = [n for n in names if n is not None]
    if len(names) > 0:
        charity = names[0]
    return render_template('charity.html', grants=grants, charity=charity)


@api.route('/grant/<grant_id>')
@api.route('/grant/<grant_id>.json')
def grant(grant_id=None):
    db = get_db()
    grant = db.grants.find_one({"_id": grant_id})
    return jsonify(grant)


@api.route('/funders')
def funders():
    db = get_db()
    funders = db.grants.aggregate(funders_query())
    return jsonify(list(funders))


@api.route('/funders.html')
def funders_html():
    db = get_db()
    funders = db.grants.aggregate(funders_query())
    return render_template('funders.html', funders=list(funders))


@api.route('/funder/<funder_id>')
@api.route('/funder/<funder_id>.json')
def funder(funder_id=None):
    db = get_db()
    grants = db.grants.find({'fundingOrganization.id': funder_id})\
               .sort("awardDate", DESCENDING)
    return jsonify(list(grants))
