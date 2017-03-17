from __future__ import print_function
from pymongo import MongoClient
import argparse
import json
import os
import urllib.request

def main():

    parser = argparse.ArgumentParser(description='Import grantnav file to mongo db')
    parser.add_argument('--grantnav', default='http://grantnav.threesixtygiving.org/api/grants.json', help='Location of grantnav file downloaded from <http://grantnav.threesixtygiving.org/api/grants.json>')
    parser.add_argument('--mongo-port', '-p', type=int, default=27017, help='Port for mongo db instance')
    parser.add_argument('--mongo-host', '-mh', default='localhost', help='Host for mongo db instance')
    parser.add_argument('--mongo-db', '-db', default='360giving', help='Database to import data to')
    parser.add_argument('--limit', '-l', type=int, default=10000, help='Size of chunks imported in bulk')
    args = parser.parse_args()

    client = MongoClient(args.mongo_host, args.mongo_port)
    db = client[args.mongo_db]
    print("Connected to '%s' mongo database [host: %s, port: %s]" % (args.mongo_db, args.mongo_host, args.mongo_port))

    if os.path.isfile(args.grantnav):
        grantnav = args.grantnav
        print("Using existing file: %s" % args.grantnav)
    else:
        grantnav = "grants.json"
        print("Downloading from: %s" % args.grantnav)
        urllib.request.urlretrieve(args.grantnav, grantnav)
        print("Saved as: %s" % grantnav)

    with open(grantnav) as g:
        grants = json.load(g)

    bulk = []
    for k, i in enumerate(grants["grants"]):
        bulk.append(i)
        if len(bulk)>=args.limit:
            db.grants.insert_many(bulk)
            print("%s records inserted, %s total" % (len(bulk), k))
            bulk = []

    if len(bulk)>0:
        db.grants.insert_many(bulk)
        print("%s records inserted, %s total" % (len(bulk), k))

if __name__ == '__main__':
    main()
