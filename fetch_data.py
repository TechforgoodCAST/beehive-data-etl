from __future__ import print_function
from pymongo import MongoClient
import argparse
import json
import os
import urllib.request
from beehive_schema.swap_funds import SWAP_FUNDS
from slugify import slugify
from pprint import pprint
import dateutil.parser
import flattentool
import datetime


def fetch_url(url, new_file):
    request = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0"
    })
    with urllib.request.urlopen(request) as f:
        with open(new_file, "wb") as new_f:
            new_f.write(f.read())


def fetch_register(db, data_register="http://data.threesixtygiving.org/data.json"):
    """
    Fetch list of files from the JSON feed of the data register and store them
    in a mongo-db instance
    """
    temp_file = 'data/dcat.json'
    print("Downloading from: %s" % data_register)
    fetch_url(data_register, temp_file)
    print("Saved as: %s" % temp_file)

    # open the file and save each record to DB
    with open(temp_file, encoding='utf8') as g:
        dcat = json.load(g)
        bulk = db.files.initialize_unordered_bulk_op()
        for k, i in enumerate(dcat):
            i["_id"] = i["identifier"]
            i["modified"] = dateutil.parser.parse(i["modified"], ignoretz=True)
            i["issued"] = dateutil.parser.parse(i["issued"], ignoretz=True)

            bulk.find({'_id': i["_id"]}).upsert().replace_one(i)

        print_mongo_bulk_result(bulk.execute(), "files")


def process_register(db, created_since=None, only_funders=None):
    conditions = {}

    # only modified since a certain time
    if created_since:
        conditions["modified"] = {"$gte": created_since}
        print("Looking for files modified since {}".format(created_since))

    if only_funders:
        if isinstance(only_funders, list):
            conditions["publisher.prefix"] = {"$in": only_funders}
        else:
            conditions["publisher.prefix"] = only_funders

    files = db.files.find(conditions)
    print("Found {} files to import".format(files.count()))
    print()

    for f in files:
        print("Importing data: {} (files: {})".format(f.get("publisher", {}).get("name"), len(f.get("distribution", []))))
        print("Data license: {}".format(f.get("license", "[Unknown]")))
        for k, d in enumerate(f.get("distribution", [])):
            filename = d.get("downloadURL")
            filetype = filename.split('.')[-1].lower()
            usefile = 'data/{}-{}.{}'.format(f.get("identifier"), k, filetype)
            usefile_json = 'data/{}-{}.{}'.format(f.get("identifier"), k, "json")
            print("Downloading from: %s" % filename)
            try:
                fetch_url(filename, usefile)
            except urllib.error.HTTPError as e:
                print()
                print("*****************")
                print("DOWNLOAD FAILED")
                print("URL: {}".format(filename))
                print("REASON: {}".format(str(e)))
                print("*****************")
                print()
                continue
            print("Saved as: %s" % usefile)

            if filetype != "json":
                convert_spreadsheet(usefile, usefile_json, filetype)
                os.remove(usefile)
                print("Converted to json: {}".format(usefile_json))
            print()

            db.downloads.replace_one({"_id": filename}, {
                "downloadFile": usefile_json,
                "downloadedOn": datetime.datetime.now()
            }, upsert=True)

            import_file(db, usefile_json)


# from: https://github.com/ThreeSixtyGiving/datagetter/blob/master/get.py#L53
def convert_spreadsheet(input_path, converted_path, file_type):
    encoding = 'utf-8'
    if file_type == 'csv':
        tmp_dir = tempfile.mkdtemp()
        destination = os.path.join(tmp_dir, 'grants.csv')
        shutil.copy(input_path, destination)
        try:
            with open(destination, encoding='utf-8') as main_sheet_file:
                main_sheet_file.read()
        except UnicodeDecodeError:
            try:
                with open(destination, encoding='cp1252') as main_sheet_file:
                    main_sheet_file.read()
                encoding = 'cp1252'
            except UnicodeDecodeError:
                encoding = 'latin_1'
        input_name = tmp_dir
    else:
        input_name = input_path
    flattentool.unflatten(
        input_name,
        output_name=converted_path,
        input_format=file_type,
        root_list_path='grants',
        root_id='',
        schema='https://raw.githubusercontent.com/ThreeSixtyGiving/standard/master/schema/360-giving-schema.json',
        convert_titles=True,
        encoding=encoding
    )


def import_file(db, filename, inner="grants"):
    if os.path.isfile(filename):
        usefile = filename
        print("Using existing file: %s" % usefile)
    else:
        usefile = "data/grants.json"
        print("Downloading from: %s" % filename)
        fetch_url(filename, usefile)
        print("Saved as: %s" % usefile)

    with open(usefile, encoding='utf8') as g:
        grants = json.load(g)

    if inner and inner in grants:
        grants = grants[inner]

    bulk = db.grants.initialize_unordered_bulk_op()

    print("Using {:,.0f} grants from {}".format(len(grants), usefile))

    for k, i in enumerate(grants):
        i = process_grant(i)
        i["_id"] = i["id"]
        bulk.find({'_id': i["_id"]}).upsert().replace_one(i)

    print_mongo_bulk_result(bulk.execute(), "grants")


def process_grant(i):

    # work out fund slug
    i.setdefault("grantProgramme", [{}])
    # default grant programme is "main fund"
    grantprogramme = i.get("grantProgramme", [{}])[0].get("title", "Main Fund")
    funder = i["fundingOrganization"][0]["name"]
    # check whether we're swapping the fund name
    if funder in SWAP_FUNDS:
        if SWAP_FUNDS[funder] == "":
            grantprogramme = "Main Fund"
        elif grantprogramme in SWAP_FUNDS[funder]:
            grantprogramme = SWAP_FUNDS[funder][grantprogramme]
    # slugify the funder and grant programme
    funder = slugify(funder)
    i["fundingOrganization"][0]["slug"] = funder
    grantprogramme = slugify(grantprogramme)
    i["grantProgramme"][0]["slug"] = grantprogramme
    i["fund_slug"] = "{}-{}".format(funder, grantprogramme)

    # transform dates
    for d in ["awardDate", "dateModified"]:
        if d in i and isinstance(i[d], str):
            i[d] = dateutil.parser.parse(i[d], ignoretz=True, dayfirst=True)
    if "plannedDates" in i:
        for pd in i["plannedDates"]:
            for d in ["endDate", "startDate"]:
                if d in pd and isinstance(pd[d], str):
                    pd[d] = dateutil.parser.parse(pd[d], ignoretz=True, dayfirst=True)
            if "duration" in pd and isinstance(pd["duration"], str):
                if pd["duration"] == "Undefined":
                    pd["duration"] = None
                else:
                    try:
                        pd["duration"] = int(pd["duration"].replace(" months", ""))
                    except:
                        pass

    # Sort out charity & company numbers
    if "recipientOrganization" in i:
        for r in i["recipientOrganization"]:
            if not r.get("charityNumber") or r["charityNumber"] == "":
                if r.get("id", "").startswith("GB-CHC-"):
                    r["charityNumber"] = r["id"].replace("GB-CHC-", "")

            if not r.get("companyNumber") or r["companyNumber"] == "":
                if r.get("id", "").startswith("GB-COH-"):
                    r["companyNumber"] = r["id"].replace("GB-COH-", "")

            if r.get("charityNumber", "").strip().lower() in ["n/a", "-", "no", ""]:
                r["charityNumber"] = None

    return i


def print_mongo_bulk_result(result, name="records"):
    for i in ["Inserted", "Matched", "Modified", "Removed", "Upserted"]:
        print("{:,.0f} {} {}".format(result["n" + i], name, i.lower()))


def main():

    parser = argparse.ArgumentParser(description='Import grantnav file to mongo db')
    parser.add_argument('--mongo-port', '-p', type=int, default=27017, help='Port for mongo db instance')
    parser.add_argument('--mongo-host', '-mh', default='localhost', help='Host for mongo db instance')
    parser.add_argument('--mongo-db', '-db', default='360giving', help='Database to import data to')
    parser.add_argument('--registry', default="http://data.threesixtygiving.org/data.json", help="URL to download the data registry from")
    parser.add_argument('--files-since', default=None, help="Look only for files modified since this date (in format YYYY-MM-DD)")
    parser.add_argument('--funders', default=None, help="Only update from these funders (comma separated list of funder prefixes)")
    args = parser.parse_args()

    client = MongoClient(args.mongo_host, args.mongo_port)
    db = client[args.mongo_db]
    print("Connected to '%s' mongo database [host: %s, port: %s]" % (args.mongo_db, args.mongo_host, args.mongo_port))

    if args.files_since:
        args.files_since = dateutil.parser.parse(args.files_since, ignoretz=True)
    if args.funders:
        args.funders = args.funders.split(",")

    fetch_register(db, args.registry)
    process_register(db, args.files_since, args.funders)

if __name__ == '__main__':
    main()
