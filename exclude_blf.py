from __future__ import print_function
import json
import argparse
import os
from urllib.request import urlretrieve

def main():

    parser = argparse.ArgumentParser(description='Process grantnav grants')
    parser.add_argument('--grantnav', '-g', default='http://grantnav.threesixtygiving.org/api/grants.json', help='Location of grantnav file downloaded from <http://grantnav.threesixtygiving.org/api/grants.json>')
    parser.add_argument('--output', '-o', default='beehive_grants.json', help='File to output data for Beehive')
    parser.add_argument('--exclude', '-e', default=[], nargs='*', help='Funders to exclude from the file')
    args = parser.parse_args()

    print(args)

    if os.path.isfile(args.grantnav):
        grantnav = args.grantnav
        print("Using existing file: %s" % args.grantnav)
    else:
        grantnav = "grants.json"
        print("Downloading from: %s" % args.grantnav)
        urlretrieve(args.grantnav, grantnav)
        print("Saved as: %s" % grantnav)

    with open(grantnav) as g:
        grants = json.load(g)

    new_grants = []
    excluded = 0
    included = 0

    # iterate through every grant in 360giving database
    for k,g in enumerate(grants["grants"]):
        if g.get("fundingOrganization", [{}])[0].get("id") in args.exclude:
            excluded += 1
        else:
            new_grants.append(g)
            included += 1

    print("Included %s grants" % included)
    print("Excluded %s grants" % excluded)

    grants["grants"] = new_grants
    with open(args.output, "w") as gno:
        json.dump(grants, gno, indent=4)#, default=json_serial)
        print("Saved to output file: %s" % (args.output))

if __name__ == '__main__':
    main()
