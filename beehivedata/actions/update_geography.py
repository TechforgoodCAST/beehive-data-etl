from __future__ import print_function
import re
import csv
import os

from ..db import get_db
from .fetch_data import print_mongo_bulk_result


def get_countries(csvfile="assets/countries.csv"):
    with open(csvfile, encoding='utf-8') as a:
        r = csv.DictReader(a)
        countries = [country for country in r]
    return countries


def update_geography():
    db = get_db()

    bulk = db.grants.initialize_unordered_bulk_op()

    f = os.path.join(os.path.dirname(__file__), '..', 'assets', 'countries.csv')
    all_countries = get_countries(f)
    c_search = {
        country["alpha2"]: re.compile(r'\b({})\b'.format("|".join(
            filter(None, country["altnames"].split(",") + [country["name"]]))
        )) for country in all_countries
    }

    for grant in db.grants.find():
        grant.setdefault("beehive", {})
        desc = grant.get("title", "") + " " + grant.get("description", "")

        # get any countries mentioned in the grant title / description
        # Using regexes

        # special case for Northern Ireland
        country_desc = re.sub(r'\bNorthern Ireland\b', '', desc, re.IGNORECASE)
        grant["beehive"]["countries"] = [code for code in c_search if c_search[code].search(country_desc)]

        if len(grant["beehive"]["countries"]) == 0:
            grant["beehive"]["countries"] = ['GB']

        grant["beehive"]["districts"] = []

        if len(grant["beehive"]["countries"]) > 1:
            grant["beehive"]["geographic_scale"] = 3
        elif len(grant["beehive"]["countries"]) == 1 and len(grant["beehive"]["districts"]) == 0:
            grant["beehive"]["geographic_scale"] = 2
        elif len(grant["beehive"]["districts"]) > 1:
            grant["beehive"]["geographic_scale"] = 1
        else:
            grant["beehive"]["geographic_scale"] = 0

        bulk.find({'_id': grant["_id"]}).replace_one(grant)

    print_mongo_bulk_result(bulk.execute(), "grants", [])
