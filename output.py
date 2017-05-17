from __future__ import print_function
from grant import Grant
import json
from pymongo import MongoClient
import argparse
import os

def main():

    parser = argparse.ArgumentParser(description='Process grantnav grants')
    parser.add_argument('--grantnav', '-g', default='http://grantnav.threesixtygiving.org/api/grants.json', help='Location of grantnav file downloaded from <http://grantnav.threesixtygiving.org/api/grants.json>')
    parser.add_argument('--output', '-o', default='beehive_grants.json', help='File to output data for Beehive')
    parser.add_argument('--mongo-port', '-p', type=int, default=27017, help='Port for mongo db instance')
    parser.add_argument('--mongo-host', '-mh', default='localhost', help='Host for mongo db instance')
    parser.add_argument('--charity-db', '-cdb', default='charity-base', help='Database containing charity data')
    parser.add_argument('--skip', '-s', type=int, default=0, help='Records to skip from the start')
    args = parser.parse_args()


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

    client = MongoClient(args.mongo_host, args.mongo_port)
    print("Connected to mongo [host: %s, port: %s]" % (args.mongo_host, args.mongo_port))
    print("Using database: [charities: %s]" % (args.charity_db))

    new_grants = []

    # iterate through every grant in 360giving database
    for k,g in enumerate(grants["grants"]):
        if k < args.skip:
            continue
        
        g = Grant(g, client[args.charity_db]) # generate grant object
        g.process_grant() # process the grant details
        g_output = g.beehive_output() # produce output in Beehive format
        new_grants.append(g_output)
        if (k+1) % 1000 == 0:
            if args.skip > 0:
                print("Processed %s grants (skipped %s grants)" % ( str( (k+1)-args.skip ), args.skip ) )
            else:
                print("Processed %s grants" % str( k+1 ) )
    print("Finished processing %s grants" % str(k+1))

    with open(args.output, "w") as gno:
        json.dump(new_grants, gno, indent=4)#, default=json_serial)
        print("Saved to output file: %s" % (args.output))


if __name__ == '__main__':
    main()
