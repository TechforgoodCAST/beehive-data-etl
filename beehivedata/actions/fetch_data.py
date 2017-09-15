from __future__ import print_function
import json
import os
import urllib.request
from urllib.parse import urlparse
import dateutil.parser
import datetime
import tempfile
import shutil

from slugify import slugify
import flattentool
from flask import current_app

from ..db import get_db
from ..assets.swap_funds import SWAP_FUNDS

CONTENT_TYPES = {
    "application/json": "json",
    "text/csv": "csv",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/vnd.ms-excel": "xls",
}

ACCEPTABLE_LICENSES = [
    "https://creativecommons.org/licenses/by/4.0/",
    "http://www.opendefinition.org/licenses/odc-pddl",
    "https://creativecommons.org/publicdomain/zero/1.0/",
    "https://www.nationalarchives.gov.uk/doc/open-government-licence/version/2/",
    "http://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/",
    "",
]

DEFAULT_REGISTRY = "http://data.threesixtygiving.org/data.json"


def get_filetype(url):
    parts = urlparse(url)
    filetype = parts.path.split('.')[-1].lower()
    if filetype in ["json", "csv", "xlsx", "xls"]:
        return filetype
    return None


def parse_date(datestr):
    if "/" in datestr:
        return dateutil.parser.parse(datestr, ignoretz=True, dayfirst=True)
    return dateutil.parser.parse(datestr, ignoretz=True)


def fetch_url(url, new_file=None, filetype=None):
    # check if it's a file first
    if os.path.isfile(url):
        if new_file is None or new_file == url:
            return (url, filetype)

        # rename the file if needed
        with open(url, "rb") as f:
            with open(new_file, "wb") as new_f:
                new_f.write(f.read())
        return (new_file, filetype)

    # otherwise download and save
    request = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0"
    })
    print("Downloading from: %s" % url)
    with urllib.request.urlopen(request) as f:
        if filetype is None:
            if f.getheader("Content-Type") in CONTENT_TYPES:
                filetype = CONTENT_TYPES[f.getheader("Content-Type")]
                print("Guessing filetype as {}".format(filetype))
                new_file += "." + filetype

            elif f.getheader("Content-Disposition"):
                import cgi
                v, p = cgi.parse_header(f.getheader('Content-Disposition'))
                if "filename" in p:
                    filename = p['filename'].split(".")
                    filetype = filename[-1]
                    print("Guessing filetype as {}".format(filetype))
                    new_file += "." + filetype

        with open(new_file, "wb") as new_f:
            new_f.write(f.read())
            print("Saved as: %s" % new_file)

        return (new_file, filetype)


def fetch_register(filename=DEFAULT_REGISTRY, save_dir="data"):
    """
    Fetch list of files from the JSON feed of the data register and store them
    in a mongo-db instance
    """
    db = get_db()
    if os.path.isfile(filename):
        usefile = filename
    else:
        usefile = os.path.join(save_dir, 'dcat.json')
    fetch_url(filename, usefile, "json")

    # open the file and save each record to DB
    with open(usefile, encoding='utf8') as g:
        dcat = json.load(g)
        bulk = db.files.initialize_unordered_bulk_op()
        for k, i in enumerate(dcat):
            i["_id"] = i["identifier"]
            i["modified"] = parse_date(i["modified"])
            i["issued"] = parse_date(i["issued"])
            i["publisher"]["slug"] = slugify(i["publisher"]["name"])

            bulk.find({'_id': i["_id"]}).upsert().replace_one(i)

        print_mongo_bulk_result(bulk.execute(), "files", ["** Fetching register **"])


def fetch_new(filename=DEFAULT_REGISTRY, created_since=None, save_dir="data"):
    """
    Find the registry and display any new funders, along with their slug and
    the license for the data
    """
    db = get_db()
    existing_files = db.files.find(projection={"_id": True})
    existing_files = [i["_id"] for i in existing_files]
    fetch_register(filename, save_dir)
    messages = ["** Finding new files **"]
    print(created_since)
    for i in db.files.find().sort("modified"):
        if created_since:
            if i["modified"] < dateutil.parser.parse(created_since):
                continue
        elif i["_id"] in existing_files:
            continue
        messages.append("{} [{}] (Modified: {})".format(i["publisher"]["name"],
                                                        i["license"],
                                                        i["modified"].date().isoformat()
                                                        ))
    current_app.logger.info("\r\n".join(messages))


def get_conditions(created_since=None, only_funders=None, skip_funders=None):

    conditions = {}

    # only modified since a certain time
    if created_since:
        conditions["modified"] = {"$gte": created_since}
        print("Looking for files modified since {}".format(created_since))

    # only including particular funders
    if only_funders:
        if isinstance(only_funders, list):
            only_funders = {"$in": only_funders}
        conditions["$or"] = [
            {"publisher.prefix": only_funders},
            {"publisher.name": only_funders},
            {"publisher.slug": only_funders},
        ]

    if skip_funders:
        if isinstance(skip_funders, list):
            skip_funders = {"$nin": skip_funders}
        else:
            skip_funders = {"$ne": skip_funders}
        conditions["$and"] = [
            {"publisher.prefix": skip_funders},
            {"publisher.name": skip_funders},
            {"publisher.slug": skip_funders},
        ]

    return conditions


def get_grant_conditions(only_funders=None, skip_funders=None):

    conditions = {}

    # only including particular funders
    if only_funders:
        if isinstance(only_funders, list):
            only_funders = {"$in": only_funders}
        conditions["$or"] = [
            {"fundingOrganization.name": only_funders},
            {"fundingOrganization.slug": only_funders},
        ]

    if skip_funders:
        if isinstance(skip_funders, list):
            skip_funders = {"$nin": skip_funders}
        else:
            skip_funders = {"$ne": skip_funders}
        conditions["$and"] = [
            {"fundingOrganization.name": skip_funders},
            {"fundingOrganization.slug": skip_funders},
        ]

    return conditions


def process_register(created_since=None, only_funders=None, skip_funders=None, save_dir="data"):
    db = get_db()
    conditions = get_conditions(created_since, only_funders, skip_funders)
    results = {
        "files_imported": [],
        "grants_imported": 0,
        "unacceptable_license": [],
        "download_failed": []
    }

    files = db.files.find(conditions)
    print("Found {} files to import".format(files.count()))
    print()

    for f in files:
        print("Importing from publisher: {} (files: {})".format(
            f.get("publisher", {}).get("name"),
            len(f.get("distribution", []))
        ))
        print("Data license: {}".format(f.get("license", "[Unknown]")))

        # Check license
        if f.get("license", "") not in ACCEPTABLE_LICENSES:
            print()
            print("*****************")
            print("COULD NOT USE")
            print("REASON: Invalid license {}".format(f.get("license", "[Unknown]")))
            print("*****************")
            print()
            results["unacceptable_license"].append(
                (f.get("publisher", {}).get("name"), f.get("license", "[Unknown]"))
            )
            continue

        for k, d in enumerate(f.get("distribution", [])):
            filename = d.get("downloadURL")
            filetype = get_filetype(filename)
            usefile = os.path.join(save_dir, '{}-{}'.format(f.get("identifier"), k))
            if filetype:
                usefile += "." + filetype
            usefile_json = os.path.join(save_dir, '{}-{}.{}'.format(f.get("identifier"), k, "json"))
            try:
                (usefile, filetype) = fetch_url(filename, usefile, filetype)
            except (urllib.error.HTTPError, urllib.error.URLError) as e:
                print()
                print("*****************")
                print("DOWNLOAD FAILED")
                print("URL: {}".format(filename))
                print("REASON: {}".format(str(e)))
                print("*****************")
                print()
                results["download_failed"].append(
                    (f.get("publisher", {}).get("name"), filename, str(e))
                )
                continue

            if filetype != "json":
                convert_spreadsheet(usefile, usefile_json, filetype)
                os.remove(usefile)
                print("Converted to json: {}".format(usefile_json))

            db.downloads.replace_one({"_id": filename}, {
                "downloadFile": usefile_json,
                "downloadedOn": datetime.datetime.now()
            }, upsert=True)

            grants_imported = import_file(usefile_json, source=d.get("accessURL"), license=f.get("license"))
            results["files_imported"].append(usefile_json)
            results["grants_imported"] += grants_imported
            print()

    # log result of exercise
    messages = [
        "{:,.0f} files successfully imported".format(len(results["files_imported"])),
        "{:,.0f} grants successfully imported".format(results["grants_imported"]),
        "{:,.0f} files skipped due to incompatible license:".format(len(results["unacceptable_license"]))
    ]
    for i in results["unacceptable_license"]:
        messages.append("  - {} [{}]".format(i[0], i[1]))
    messages.append("{:,.0f} files skipped due to download failing:".format(len(results["download_failed"])))
    for i in results["download_failed"]:
        messages.append("  - {} [{}] Error: {}".format(i[0], i[1], i[2]))
    current_app.logger.info("\r\n".join(messages))


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


def import_file(filename, inner="grants", source=None, license=None):
    db = get_db()

    if os.path.isfile(filename):
        usefile = filename
        print("Using existing file: %s" % usefile)
    else:
        usefile = "data/grants.json"
        print("Downloading from: %s" % filename)
        fetch_url(filename, usefile, "json")
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
        i["dataset"] = {
            "license": license,
            "source": source
        }
        bulk.find({'_id': i["_id"]}).upsert().replace_one(i)

    result = bulk.execute()
    print_mongo_bulk_result(result, "grants", ["** Importing file **"])
    return max([result["n" + i] for i in ["Inserted", "Matched", "Modified", "Upserted"]])


def process_grant(i):

    # clean up the fundingOrganization name
    for f in i.get("fundingOrganization", []):
        f["name"] = f.get("name").strip()
    funder = i["fundingOrganization"][0]["name"]

    # work out fund slug
    i.setdefault("grantProgramme", [{}])
    # default grant programme is "main fund"
    grantprogramme = i["grantProgramme"][0].get("title", "Main Fund")
    i["grantProgramme"][0]["title_original"] = i["grantProgramme"][0].get("title")

    # check whether we're swapping the fund name
    if funder in SWAP_FUNDS:
        if SWAP_FUNDS[funder] == "":
            grantprogramme = "Main Fund"
        elif "swap_all" in SWAP_FUNDS[funder]:
            grantprogramme = SWAP_FUNDS[funder]["swap_all"]
        elif grantprogramme in SWAP_FUNDS[funder]:
            grantprogramme = SWAP_FUNDS[funder][grantprogramme]

        # swap fund name based on grant amount
        # based on a particular pattern in the SWAP_FUNDS variable
        if isinstance(SWAP_FUNDS[funder], dict)  \
            and SWAP_FUNDS[funder].get("fund_amounts") \
                and grantprogramme == "Main Fund":
                    fund_amounts = SWAP_FUNDS[funder].get("fund_amounts")
                    grantprogramme = fund_amounts["funds"][-1]
                    for k, v in enumerate(fund_amounts["amounts"]):
                        if i.get("amountAwarded") < v:
                            grantprogramme = fund_amounts["funds"][k]
                            break

        # swap fund name based on classification details
        # based on a particular pattern in the SWAP_FUNDS variable
        if isinstance(SWAP_FUNDS[funder], dict)  \
           and SWAP_FUNDS[funder].get("classifications.title"):
            fund_classifications = SWAP_FUNDS[funder].get("classifications.title")
            grant_classifications = [c.get("title") for c in i.get("classifications", [])]
            intersection = set.intersection(set(fund_classifications), set(grant_classifications))
            if len(intersection) == 1:
                grantprogramme = list(intersection)[0]

        # swap fund name based on spliting the existing grantprogramme
        # based on a particular pattern in the SWAP_FUNDS variable
        if isinstance(SWAP_FUNDS[funder], dict)  \
           and SWAP_FUNDS[funder].get("split_on"):
            split_on = SWAP_FUNDS[funder].get("split_on")
            grantprogramme = grantprogramme.split(split_on["split"])
            if len(grantprogramme) > split_on["take"]:
                grantprogramme = grantprogramme[split_on["take"]]

    # slugify the funder and grant programme
    funder = slugify(funder)
    i["fundingOrganization"][0]["slug"] = funder
    i["grantProgramme"][0]["title"] = grantprogramme
    grantprogramme = slugify(grantprogramme)
    i["grantProgramme"][0]["slug"] = grantprogramme
    i["fund_slug"] = "{}-{}".format(funder, grantprogramme)

    # transform dates
    for d in ["awardDate", "dateModified"]:
        if d in i and isinstance(i[d], str):
            i[d] = parse_date(i[d])
    if "plannedDates" in i:
        for pd in i["plannedDates"]:
            for d in ["endDate", "startDate"]:
                if d in pd and isinstance(pd[d], str):
                    pd[d] = parse_date(pd[d])
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
                    r["charityNumber"] = r["id"]

            if not r.get("companyNumber") or r["companyNumber"] == "":
                if r.get("id", "").startswith("GB-COH-"):
                    r["companyNumber"] = r["id"]

            if r.get("charityNumber") and r.get("charityNumber", "").strip().lower() in ["n/a", "-", "no", ""]:
                r["charityNumber"] = None

            if r.get("charityNumber"):
                r["charityNumber"] = r["charityNumber"].replace("GB-CHC-", "")

            if r.get("companyNumber"):
                r["companyNumber"] = r["companyNumber"].replace("GB-COH-", "")

    return i


def print_mongo_bulk_result(result, name="records", messages=[]):
    messages.extend(["{:,.0f} {} {}".format(result["n" + i], name, i.lower())
                    for i in ["Inserted", "Matched", "Modified", "Removed", "Upserted"]])
    current_app.logger.info("\r\n".join(messages))


def fetch_data(registry="http://data.threesixtygiving.org/data.json",
               files_since=None, funders=None, skip_funders=None):

    if files_since:
        files_since = parse_date(files_since)

    fetch_register(registry)
    process_register(files_since, funders, skip_funders)
