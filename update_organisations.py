from __future__ import print_function
from pymongo import MongoClient
import argparse
import dateutil.relativedelta
from fetch_data import print_mongo_bulk_result, process_grant
import re


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

if __name__ == '__main__':
    main()
