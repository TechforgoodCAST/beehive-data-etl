from __future__ import print_function
from pymongo import MongoClient
import argparse
import dateutil.relativedelta
from beehive_schema.cc_aoo import CC_AOO_CODES
from beehive_schema.beneficiaries import *
from update_beneficiaries import classify_grant
from fetch_data import print_mongo_bulk_result

# convert charity commission classification categories to beehive ones
cc_to_beehive = {
    105: "poverty",
    108: "religious",
    111: "animals",
    203: "disabilities",
    204: "ethnic",
    205: "organisations",
    207: "public",
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
    regno = regno.replace("SCO", "SC0")
    regno = regno.replace("GB-CHC-", "")
    regno = regno.replace(" ", "")
    regno = regno.replace(" (charity no)", "")
    return regno


def main():

    parser = argparse.ArgumentParser(description='Update Charity data for grants in database')
    parser.add_argument('--mongo-port', '-p', type=int, default=27017, help='Port for mongo db instance')
    parser.add_argument('--mongo-host', '-mh', default='localhost', help='Host for mongo db instance')
    parser.add_argument('--mongo-db', '-db', default='360giving', help='Database to import data to')
    parser.add_argument('--charitybase-db', '-cdb', default='charity-base', help='Charity Base database')
    args = parser.parse_args()

    client = MongoClient(args.mongo_host, args.mongo_port)
    db = client[args.mongo_db]
    cdb = client[args.charitybase_db]
    print("Connected to '%s' mongo database [host: %s, port: %s]" % (args.mongo_db, args.mongo_host, args.mongo_port))
    print("Connected to '%s' charitybase database [host: %s, port: %s]" % (args.charitybase_db, args.mongo_host, args.mongo_port))

    bulk = db.grants.initialize_unordered_bulk_op()

    for grant in db.grants.find({"recipientOrganization": {"$elemMatch": {"charityNumber": {"$exists": True}}}}):
        grant.setdefault("beehive", {})
        for r in grant["recipientOrganization"]:
            charityNumber = clean_charity_number(r["charityNumber"])
            if not charityNumber or charityNumber == "":
                continue

            charity = cdb.charities.find_one({"charityNumber": charityNumber})
            r.setdefault("beehive", {})
            r["beehive"].setdefault("beneficiaries", [])

            if not charity:
                print("Charity {} not found".format(r["charityNumber"]))
                continue

            # work out how long charity was operating for
            r["regDate"] = charity.get("registration", [{}])[0].get("regDate")
            if r["regDate"]:
                grant["beehive"]["operating_for"] = float((grant["awardDate"] - r["regDate"]).days) / 365

            # get financial data
            max_i = None
            use_i = None
            for i in charity.get("financial", []):
                if not i.get("fyEnd"):
                    continue
                if not i.get("fyStart"):
                    i["fyStart"] = i["fyEnd"] - dateutil.relativedelta.relativedelta(months=12)

                if i["income"] and i["spending"]:
                    if grant["awardDate"] <= i["fyEnd"] and grant["awardDate"] >= i["fyStart"]:
                        use_i = i["fyEnd"]
                    if max_i is None or i["fyEnd"] > max_i:
                        max_i = i["fyEnd"]

            if use_i is None:
                use_i = max_i

            for i in charity.get("financial", []):
                if i["fyEnd"] == use_i:
                    grant["beehive"]["financial_fye"] = str(i["fyEnd"])
                    grant["beehive"]["income"] = i["income"]
                    grant["beehive"]["spending"] = i["spending"]

            # get employee and volunteer data
            max_i = None
            use_i = None
            for i in charity.get("partB", []):
                if not i.get("fyEnd"):
                    continue
                if not i.get("fyStart"):
                    i["fyStart"] = i["fyEnd"] - dateutil.relativedelta.relativedelta(months=12)

                if i.get("people"):
                    if grant["awardDate"] <= i["fyEnd"] and grant["awardDate"] >= i["fyStart"]:
                        use_i = i["fyEnd"]
                    if max_i is None or i["fyEnd"] > max_i:
                        max_i = i["fyEnd"]

            if use_i is None:
                use_i = max_i

            for i in charity.get("partB", []):
                if i["fyEnd"] == use_i:
                    grant["beehive"]["partb_fye"] = str(i["fyEnd"])
                    grant["beehive"]["employees"] = i.get("people", {}).get("employees")
                    grant["beehive"]["volunteers"] = i.get("people", {}).get("volunteers")

            # add beneficiary data to recipient organisation

            # Charity Commission beneficiaries
            for c in charity.get("class", []):
                if c in cc_to_beehive:
                    r["beehive"]["beneficiaries"].append(cc_to_beehive[c])

            # OSCR beneficiaries
            for i in charity.get("beta", {}):
                for c in charity.get("beta", {})[i]:
                    if c in oscr_to_beehive:
                        r["beehive"]["beneficiaries"].append(oscr_to_beehive[c])

            # regex on objects
            for o in charity.get("objects", []):
                if o:
                    r["beehive"]["beneficiaries"] += classify_grant(o, ben_regexes)

            r["beehive"]["beneficiaries"] = list(set(r["beehive"]["beneficiaries"]))

            # add recipient districts and countries
            r["beehive"]["countries"] = []
            r["beehive"]["districts"] = []
            r["beehive"]["multi_national"] = False
            for i in charity.get("areaOfOperation", []):
                area = None
                for a in CC_AOO_CODES:
                    if a[0] == i["aooType"] and a[1] == i["aooKey"]:
                        area = a

                if not area:
                    continue

                if i["aooType"] == "D":
                    r["beehive"]["countries"].append(area[7])
                elif i["aooType"] == "E":
                    r["beehive"]["multi_national"] = True
                elif area[6]:
                    r["beehive"]["districts"].append(area[6])

            if len(r["beehive"]["districts"]) > 0 and len(r["beehive"]["countries"]) == 0:
                r["beehive"]["countries"] = ["GB"]

            if len(r["beehive"]["countries"]) > 1:
                r["beehive"]["multi_national"] = True

        bulk.find({'_id': grant["_id"]}).replace_one(grant)

    print_mongo_bulk_result(bulk.execute(), "grants")

if __name__ == '__main__':
    main()
