from __future__ import print_function
from pymongo import MongoClient
import argparse
from beehive_schema.beneficiaries import *
import re
from fetch_data import print_mongo_bulk_result


def classify_grant(desc, regexes):
    """
    Use regexes to return a list of possible beneficiaries
    """
    return list(set([r for r in regexes if re.search(regexes[r], desc, re.I)]))


def classify_grant_ages(desc):
    """
    Get an age range from a text string - something like "10-19 years old" or
    "aged 24-64".
    """
    agesre = r'\b(age(d|s)? ?(of|betweee?n)?|adults)? ?([0-9]{1,2}) ?(\-|to) ?([0-9]{1,2}) ?\-?(year\'?s?[ -](olds)?|y\.?o\.?)?\b'
    match = re.search(agesre, desc, re.I)
    if match:
        # only return if one of the age ranges has been included
        if match.group(1) or match.group(2) or match.group(3) or match.group(7) or match.group(8) or match.group(5) == "to":
            return (int(match.group(4)), int(match.group(6)))


def age_to_category(ages):
    """
    turn an age produced by `classify_grant_ages` into a category
    """
    cats = {}
    for age in ages:
        for i in age_categories:
            if age[0] <= i["age_to"] and i["age_from"] <= age[1] and i["label"] != "All ages":
                cats[i["label"]] = i

    if len(cats) == 0:
        for i in age_categories:
            if i["label"] == "All ages":
                cats[i["label"]] = i

    return list(cats.values())


def main():

    parser = argparse.ArgumentParser(description='Update Charity data for grants in database')
    parser.add_argument('--mongo-port', '-p', type=int, default=27017, help='Port for mongo db instance')
    parser.add_argument('--mongo-host', '-mh', default='localhost', help='Host for mongo db instance')
    parser.add_argument('--mongo-db', '-db', default='360giving', help='Database to import data to')
    args = parser.parse_args()

    client = MongoClient(args.mongo_host, args.mongo_port)
    db = client[args.mongo_db]
    print("Connected to '%s' mongo database [host: %s, port: %s]" % (args.mongo_db, args.mongo_host, args.mongo_port))

    bulk = db.grants.initialize_unordered_bulk_op()

    for grant in db.grants.find():
        grant.setdefault("beehive", {})
        grant["beehive"].setdefault("beneficiaries", [])
        grant["beehive"].setdefault("ages", [])
        grant["beehive"].setdefault("gender", "All genders")
        grant["beehive"].setdefault("affect_people", False)
        grant["beehive"].setdefault("affect_other", False)

        desc = grant.get("title", "") + " " + grant.get("description", "")

        # add beneficiaries
        grant["beehive"]["beneficiaries"] += classify_grant(desc, ben_regexes)

        # if no beneficiaries found then add charity beneficiaries
        if len(grant["beehive"]["beneficiaries"]) == 0:
            for r in grant["recipientOrganization"]:
                if len(r.get("beehive", {}).get("beneficiaries", [])) > 0:
                    grant["beehive"]["beneficiaries"] += r.get("beehive", {}).get("beneficiaries", [])

        # make sure we've got no duplicates
        grant["beehive"]["beneficiaries"] = list(set(grant["beehive"]["beneficiaries"]))

        # get genders
        regex_genders = classify_grant(desc, gender_regexes)
        genders = []
        if "men" in regex_genders:
            genders.append("Male")
        if "women" in regex_genders:
            genders.append("Female")
        if "transgender" in regex_genders:
            genders.append("Transgender")
        if len(genders) == 1:
            grant["beehive"]["gender"] = genders[0]

        # get ages
        regex_ages = classify_grant(desc, age_regexes)
        ages = [age_bens[b] for b in regex_ages if b in age_bens]

        age_category = classify_grant_ages(desc)
        if age_category is not None:
            ages.append(age_category)

        grant["beehive"]["ages"] = age_to_category(ages)

        # work out affect_people or affect_other
        for b in grant["beehive"]["beneficiaries"]:
            if ben_categories.get(b, {}).get("group") == "People":
                grant["beehive"]["affect_people"] = True
            elif ben_categories.get(b, {}).get("group") == "Other":
                grant["beehive"]["affect_other"] = True

        bulk.find({'_id': grant["_id"]}).replace_one(grant)

    print_mongo_bulk_result(bulk.execute(), "grants")

if __name__ == '__main__':
    main()
