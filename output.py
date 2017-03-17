from __future__ import print_function
from grant import Grant
import json
from pymongo import MongoClient
import argparse

def main():

    parser = argparse.ArgumentParser(description='Process grantnav grants')
    parser.add_argument('--mongo-port', '-p', type=int, default=27017, help='Port for mongo db instance')
    parser.add_argument('--mongo-host', '-mh', default='localhost', help='Host for mongo db instance')
    parser.add_argument('--grant-db', '-gdb', default='360giving', help='Database containing grantnav data')
    parser.add_argument('--charity-db', '-cdb', default='charity-base', help='Database containing charity data')
    parser.add_argument('--output-db', '-odb', default='beehive-data', help='Database to output data for Beehive')
    parser.add_argument('--limit', '-l', type=int, default=10000, help='Size of chunks imported in bulk')
    parser.add_argument('--skip', '-s', type=int, default=0, help='Records to skip from the start')
    args = parser.parse_args()

    client = MongoClient(args.mongo_host, args.mongo_port)
    print("Connected to mongo [host: %s, port: %s]" % (args.mongo_host, args.mongo_port))
    print("Using databases: [grants: %s, charities: %s, output: %s]" % (args.grant_db, args.charity_db, args.output_db))
    db = client[args.grant_db]

    # iterate through every grant in 360giving database
#    for k,g in enumerate(db.grants.aggregate([{"$sample":{"size":20}}])):
    bulk = client[args.output_db].grants.initialize_unordered_bulk_op()
    bulk_count = 0
    k=0
    for k,g in enumerate(db.grants.find(no_cursor_timeout=True).skip(args.skip)):
        g = Grant(g, client[args.charity_db]) # generate grant object
        g.process_grant() # process the grant details
        g_output = g.beehive_output() # produce output in Beehive format
        bulk.find({"grant_identifier": g_output["grant_identifier"]}).upsert().replace_one(g_output) # add to MongoDB collection
        bulk_count+=1
        #print(json.dumps(g_output, indent=4))
        if (k+1) % 1000 == 0:
            print("Processed %s grants" % str(k+1))
        if bulk_count >= args.limit:
            bulk.execute()
            print("Persisted %s records to database" % bulk_count)
            bulk = client[args.output_db].grants.initialize_unordered_bulk_op()
            bulk_count =0
    if bulk_count>0:
        bulk.execute()
        print("Persisted %s records to database" % bulk_count)
    print("Finished processing %s grants" % str(k+1))


if __name__ == '__main__':
    main()
