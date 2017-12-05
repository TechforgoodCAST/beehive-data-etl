from __future__ import print_function
from pymongo import MongoClient
import dateutil.relativedelta
from flask import current_app

from ..db import get_db
from ..assets.cc_aoo import CC_AOO_CODES
from ..assets.beneficiaries import *
from .update_beneficiaries import classify_grant
from .fetch_data import print_mongo_bulk_result, get_grant_conditions

# convert charity commission classification categories to beehive ones
cc_to_beehive = {
    "THE PREVENTION OR RELIEF OF POVERTY": "poverty",
    "RELIGIOUS ACTIVITIES": "religious",
    "ANIMALS": "animals",
    "PEOPLE WITH DISABILITIES": "disabilities",
    "PEOPLE OF A PARTICULAR ETHNIC OR RACIAL ORIGIN": "ethnic",
    "OTHER CHARITIES OR VOLUNTARY BODIES": "organisations",
    "THE GENERAL PUBLIC/MANKIND": "public",
}

# convert OSCR classification categories to beehive ones
oscr_to_beehive = {
    "No specific group, or for the benefit of the community": "public",
    "People with disabilities or health problems": "disabilities",
    "The advancement of religion": "religious",
    "People of a particular ethnic or racial origin": "ethnic",
    "The advancement of animal welfare": "animals",
    "The advancement of environmental protection or improvement": "environment",
    "Other charities / voluntary bodies": "organisations",
    "The prevention or relief of poverty": "poverty",
}


def clean_charity_number(regno):
    if not regno:
        return regno
    regno = regno.upper()
    regno = regno.strip()
    if str(regno)=="0" or str(regno)=="":
        return None
    regno = regno.replace("SCO", "SC0")
    regno = regno.replace("NIC", "NI")
    regno = regno.replace("GB-CHC-", "")
    regno = regno.replace(" ", "")
    regno = regno.replace(" (charity no)", "")
    return regno


def update_charity(funders=None, skip_funders=None):

    db = get_db()

    missing_charities = []

    bulk = db.grants.initialize_unordered_bulk_op()

    conditions = get_grant_conditions(funders, skip_funders)
    conditions["recipientOrganization"] = {"$elemMatch": {"charityNumber": {"$exists": True}}}

    for grant in db.grants.find(conditions):
        grant.setdefault("beehive", {})
        for r in grant["recipientOrganization"]:
            charityNumber = clean_charity_number(r["charityNumber"])
            if not charityNumber or charityNumber == "":
                continue

            charity = db.charities.find_one({"_id": charityNumber})
            r.setdefault("beehive", {})
            r["beehive"].setdefault("beneficiaries", [])

            if not charity:
                r["charityStatus"] = "not found"
                missing_charities.append(charityNumber)
                continue

            r["charityStatus"] = "found"

            # work out how long charity was operating for
            r["regDate"] = charity.get("date_registered")
            if r["regDate"]:
                grant["beehive"]["operating_for"] = float((grant["awardDate"] - r["regDate"]).days) / 365

            # get company number if present
            if r.get("companyNumber", "") == "":
                if charity.get("company_number", "") != "":
                    r["companyNumber"] = charity.get("company_number")
                    grant["beehive"]["org_type"] = 3

            # get financial data
            grant["beehive"]["financial_fye"] = charity.get("fye")
            grant["beehive"]["income"] = charity.get("income")
            grant["beehive"]["spending"] = charity.get("expend")
            grant["beehive"]["employees"] = charity.get("employees")
            grant["beehive"]["volunteers"] = charity.get("volunteers")

            # add beneficiary data to recipient organisation

            # Charity Commission & oscr beneficiaries
            for i in ["beneficiaries", "activities", "purpose"]:
                for c in charity.get(i, []):
                    if c in cc_to_beehive:
                        r["beehive"]["beneficiaries"].append(cc_to_beehive[c])
                    if c in oscr_to_beehive:
                        r["beehive"]["beneficiaries"].append(oscr_to_beehive[c])

            # regex on objects
            if charity.get("objects"):
                r["beehive"]["beneficiaries"] += classify_grant(
                    charity.get("objects"), ben_regexes)

            r["beehive"]["beneficiaries"] = list(set(r["beehive"]["beneficiaries"]))

            # add recipient districts and countries
            r["beehive"]["countries"] = list(set(
                [a["iso3166_1"] for a in charity.get("areas", []) if a["iso3166_1"] != ""]))
            r["beehive"]["districts"] = list(set(
                [a["iso3166_2_GB"] for a in charity.get("areas", []) if a["iso3166_2_GB"] != ""]))
            r["beehive"]["multi_national"] = False

            if len(r["beehive"]["districts"]) > 0 and len(r["beehive"]["countries"]) == 0:
                r["beehive"]["countries"] = ["GB"]

            if len(r["beehive"]["countries"]) > 1:
                r["beehive"]["multi_national"] = True

        bulk.find({'_id': grant["_id"]}).replace_one(grant)

    print_mongo_bulk_result(bulk.execute(), "grants", messages=[
        "** Updating Charities **",
        "{:,.0f} charities not found".format(len(missing_charities))
    ])
