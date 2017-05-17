from __future__ import print_function
from grant import Grant
from pymongo import MongoClient
import argparse
import json
import os
import urllib.request

# From http://stackoverflow.com/a/22238613
from datetime import datetime

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, datetime):
        serial = obj.isoformat()
        return serial
    #raise TypeError ("Type not serializable")
    return str(obj)

def main():


    parser = argparse.ArgumentParser(description='Import grantnav file and add recipient data')
    parser.add_argument('--grantnav', default='http://grantnav.threesixtygiving.org/api/grants.json', help='Location of grantnav file downloaded from <http://grantnav.threesixtygiving.org/api/grants.json>')
    parser.add_argument('--output', default='grants_step_1.json', help='File that contains the output data')
    parser.add_argument('--mongo-port', '-p', type=int, default=27017, help='Port for mongo db instance')
    parser.add_argument('--mongo-host', '-mh', default='localhost', help='Host for mongo db instance')
    parser.add_argument('--charity-db', '-cdb', default='charity-base', help='Database containing charity data')
    parser.add_argument('--limit', '-l', type=int, default=10000, help='Size of chunks imported in bulk')
    args = parser.parse_args()

    client = MongoClient(args.mongo_host, args.mongo_port)
    print("Connected to mongo [host: %s, port: %s]" % (args.mongo_host, args.mongo_port))

    if os.path.isfile(args.grantnav):
        grantnav = args.grantnav
        print("Using existing file: %s" % args.grantnav)
    else:
        grantnav = "grants.json"
        print("Downloading from: %s" % args.grantnav)
        urllib.request.urlretrieve(args.grantnav, grantnav)
        print("Saved as: %s" % grantnav)

    with open(grantnav) as gn:
        grants = json.load(gn)

    for k, g in enumerate(grants["grants"]):
        g = Grant(g, client[args.charity_db]) # generate grant object
        g.fetch_recipients()
        print(g.grant.get("recipientOrganization", [{}])[0].get("beneficiaries", []))
        grants["grants"][k] = g.grant

    with open(args.output, "w") as gno:
        json.dump(grants, gno, indent=4, default=json_serial)

if __name__ == '__main__':
    main()
