from __future__ import print_function
import dateutil.relativedelta
import re

from ..db import get_db
from .fetch_data import print_mongo_bulk_result, process_grant


def update_organisations():
    db = get_db()

    bulk = db.grants.initialize_unordered_bulk_op()

    for grant in db.grants.find():
        grant.setdefault("beehive", {})
        grant = process_grant(grant)
        for r in grant["recipientOrganization"]:

            # check combinations of charity number and company number
            charityNumber = r.get("charityNumber")
            companyNumber = r.get("companyNumber")
            if charityNumber == "":
                charityNumber = None
            if companyNumber == "":
                companyNumber = None

            if charityNumber and companyNumber:
                grant["beehive"]["org_type"] = 3
            elif charityNumber:
                grant["beehive"]["org_type"] = 1
            elif companyNumber:
                grant["beehive"]["org_type"] = 2
            elif re.search(r'\b(school|college|university|council|academy|borough)\b', r["name"], flags=re.I):
                grant["beehive"]["org_type"] = 4

            # check if a Community Interest Company
            # nb needs to be after the company number check
            if r["name"].lower().endswith(("community interest company", " cic", "c.i.c", "c.i.c.")):
                grant["beehive"]["org_type"] = 5

            # check for individuals in the big lottery data
            if r["name"].startswith("This is a programme for individual veterans"):
                grant["beehive"]["org_type"] = -1

        bulk.find({'_id': grant["_id"]}).replace_one(grant)

    print_mongo_bulk_result(bulk.execute(), "grants")
