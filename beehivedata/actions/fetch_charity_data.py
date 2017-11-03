import mechanicalsoup
import os
import zipfile
import requests
from bs4 import BeautifulSoup
import re
import dateparser
import csv
import datetime

from .fetch_data import print_mongo_bulk_result
from ..assets import bcp
from ..db import get_db

# utilities
def clean_row(row, date_fields=[], date_order="DMY", int_fields=[], csv_fields=[], csv_format={}):
    if isinstance(row, dict):
        row = {k: row[k].strip() for k in row}
        for k in row:
            if row[k] == "":
                row[k] = None
    elif isinstance(row, list):
        row = [v.strip() for v in row]
        for k, v in enumerate(row):
            if v == "":
                row[k] = None

    for f in date_fields:
        if isinstance(row, dict) and row.get(f) is None:
            continue
        if isinstance(row, list) and (len(row) < f or row[f] is None):
            continue
        row[f] = dateparser.parse(row[f], settings={'DATE_ORDER': date_order})
                                  
    for f in int_fields:
        if isinstance(row, dict) and row.get(f) is None:
            continue
        if isinstance(row, list) and (len(row) < f or row[f] is None):
            continue
        row[f] = int(row[f])
    
    for f in csv_fields:
        if isinstance(row, dict) and row.get(f) is None:
            continue
        if isinstance(row, list) and (len(row) < f or row[f] is None):
            continue
        reader = csv.reader([row[f]], **csv_format)
        row[f] = list(reader)[0]

    return row


def download_file(url, filename):
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, "wb") as outputfile:
        outputfile.write(response.content)


OSCR_FIELD_MAP = {
    "Charity Number": "reg_number",
    "Charity Name": "name",
    "Registered Date": "date_registered",
    "Postcode": "postcode",
    "Constitutional Form": "constitution",
    "Geographical Spread": "geographical_spread",
    "Main Operating Location": "operating_location",
    "Purposes": "purpose",
    "Beneficiaries": "beneficiaries",
    "Activities": "activities",
    "Objectives": "objects",
    "Principal Office/Trustees Address": "address",
    "Website": "web",
    "Most recent year income": "income",
    "Most recent year expenditure": "spending",
    "Year End": "fye",
}


# get oscr data
def fetch_oscr(oscr):
    oscr_out = os.path.join("data", "oscr.zip")
    oscr_folder = os.path.join("data", "oscr")

    FORM_ID = "#uxSiteForm"
    TERMS_AND_CONDITIONS_CHECKBOX = "ctl00$ctl00$ctl00$ContentPlaceHolderDefault$WebsiteContent$ctl05$CharityRegDownload_10$cbTermsConditions"

    browser = mechanicalsoup.StatefulBrowser()
    print("[OSCR] Using url: %s" % oscr)
    browser.open(oscr)

    browser.select_form(FORM_ID)
    browser[TERMS_AND_CONDITIONS_CHECKBOX] = True
    resp = browser.submit_selected()
    print("[OSCR] Form submitted")
    try:
        resp.raise_for_status()
    except:
        raise ValueError("[OSCR] Could not download OSCR data. Status %s %s" % (
            resp.status, resp.reason))
    
    with open(oscr_out, "wb") as oscrfile:
        oscrfile.write(resp.content)
    print("[OSCR] ZIP downloaded")

    with zipfile.ZipFile(oscr_out) as oscrzip:
        files = oscrzip.infolist()
        if len(files) != 1:
            raise ValueError("More than one file in OSCR zip")
        with open(os.path.join("data", "oscr.csv"), "wb") as oscrcsv:
            oscrcsv.write(oscrzip.read(files[0]))
        print("[OSCR] data extracted")


def import_oscr(datafile=None):
    db = get_db()
    bulk = db.charities.initialize_unordered_bulk_op()

    # first reset some initial data
    db.charities.update_many({"source": "Office of the Scottish Charity Regulator"}, {"$set": {
        "active": False
    }})

    if not datafile:
        datafile = os.path.join("data", "oscr.csv")

    # go through the Scottish charities
    with open(datafile, encoding="latin1") as a:
        csvreader = csv.DictReader(a)
        for row in csvreader:
            row = oscr_row_to_object(row)
            bulk.find({'_id': row["_id"]}).upsert().replace_one(row)

    print_mongo_bulk_result(bulk.execute(), "charities", ["** Importing OSCR data **"])


def oscr_row_to_object(row):
    clean_params = {
        "date_fields": ["Registered Date", "Year End"],
        "date_order": "DMY",
        "int_fields": ["Most recent year income",
                      "Most recent year expenditure", "Mailing cycle"],
        "csv_fields": ["Purposes", "Beneficiaries", "Activities"],
        "csv_format": {"quotechar": "'"}
    }
    row = clean_row(row, **clean_params)
    new_row = {}

    for old_f in OSCR_FIELD_MAP:
        new_f = OSCR_FIELD_MAP[old_f]
        new_row[new_f] = row.get(old_f, None)

    new_row["source"] = "Office of the Scottish Charity Regulator"
    new_row["active"] = row["Charity Status"] != "Removed"
    new_row["dual_registered"] = row.get("Regulatory Type") == "Cross Border"
    new_row["last_updated"] = datetime.datetime.now()
    new_row["_id"] = new_row["reg_number"]
    return new_row



# get charity commission data
def fetch_ccew(ccew):
    ccew_out = os.path.join("data", "ccew.zip")
    ccew_folder = os.path.join("data", "ccew")
    ccew_html = requests.get(ccew)
    try:
        ccew_html.raise_for_status()
    except:
        raise ValueError("[CCEW] Could not find Charity Commission data page. Status %s %s" % (
            ccew_html.status, ccew_html.reason))
    ccew_soup = BeautifulSoup(ccew_html.text, 'html.parser')
    zip_regex = re.compile("http://apps.charitycommission.gov.uk/data/.*?/RegPlusExtract.*?\.zip")
    ccew_data_url = ccew_soup.find("a", href=zip_regex)["href"]
    print("[CCEW] Using url: %s" % ccew_data_url)
    download_file(ccew_data_url, ccew_out)
    print("[CCEW] ZIP downloaded")

    with zipfile.ZipFile(ccew_out) as ccew_zip:
        if not os.path.isdir(ccew_folder):
            os.makedirs(ccew_folder)
        for f in ccew_zip.infolist():
            bcp_content = ccew_zip.read(f)
            csv_content = bcp.convert(bcp_content.decode("latin1"))
            csv_filename = f.filename.replace(".bcp", ".csv")
            with open(os.path.join(ccew_folder, csv_filename), "w", encoding="latin1") as a:
                a.write(csv_content.replace('\x00', ''))
                print("[CCEW] write %s" % csv_filename)


def import_ccew():
    db = get_db()
    bulk = db.charities.initialize_unordered_bulk_op()
    ccew_folder = os.path.join("data", "ccew")

    # first reset some initial data
    db.charities.update_many({"source": "Charity Commission for England and Wales"}, {"$set": {
        "purpose": [],
        "beneficiaries": [],
        "activities": [],
        "active": False
    }})

    # go through the main charity file
    with open(os.path.join(ccew_folder, "extract_charity.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a)
        for row in csvreader:
            if len(row) < 18 or int(row[1]) != 0:
                continue
            new_row = {
                "_id": row[0].strip(),
                "reg_number": row[0].strip(),
                "name": row[2].strip(),
                "active": row[3].strip() == "R",
                "postcode": row[15].strip(),
                "constitution": row[4].strip(),
                "operating_location": row[5].strip(),
                "address": ", ".join([r.strip() for r in row[10:14] if r.strip() != ""]),
                "phone": row[16].strip(),
                "last_updated": datetime.datetime.now(),
                "source": "Charity Commission for England and Wales",
            }
            bulk.find({'_id': new_row["_id"]}).upsert().replace_one(new_row)

    print_mongo_bulk_result(bulk.execute(), "charities", [
                            "** Importing CCEW data from extract_charity.csv **"])
    bulk = db.charities.initialize_unordered_bulk_op()

    # go through the main_charity file
    with open(os.path.join(ccew_folder, "extract_main_charity.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a)
        for row in csvreader:
            if len(row) < 10 or row[0].strip()=="":
                continue
            charity_id = row[0].strip()
            new_row = {
                "$set": {
                    "company_number": row[1].strip(),
                    "web": row[9].strip(),
                    "email": row[8].strip(),
                }
            }
            bulk.find({'_id': charity_id}).update(new_row)

    print_mongo_bulk_result(bulk.execute(), "charities", [
                            "** Importing CCEW data from extract_main_charity.csv **"])
    bulk = db.charities.initialize_unordered_bulk_op()

    # go through the classification file
    with open(os.path.join(ccew_folder, "extract_class_ref.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a)
        class_ref = {}
        for row in csvreader:
            if len(row) < 2 or row[0].strip()=="":
                continue
            class_ref[row[0]] = row[1]
    
    with open(os.path.join(ccew_folder, "extract_class.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a)
        class_types = {
            "1": "purpose",
            "2": "beneficiaries",
            "3": "activities"
        }
        for row in csvreader:
            if len(row) < 2 or row[0].strip()=="":
                continue
            charity_id = row[0].strip()
            class_ = row[1].strip()
            class_type = class_types.get(class_[0])
            class_data = class_ref.get(class_)
            bulk.find({'_id': charity_id}).update(
                {"$addToSet": {class_type: class_data}})

    print_mongo_bulk_result(bulk.execute(), "classes", [
                            "** Importing CCEW data from extract_class.csv **"])
    bulk = db.charities.initialize_unordered_bulk_op()

    # go through the finances file
    with open(os.path.join(ccew_folder, "extract_financial.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a)
        charities = {}
        for row in csvreader:
            if len(row) < 2 or row[0].strip()=="":
                continue
            row = clean_row(row, int_fields=[3,4], date_order="YMD")
            charity_id = row[0]
            if charity_id not in charities:
                charities[charity_id] = {}
            fyend = datetime.datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
            if row[3] or row[4]:
                charities[charity_id][fyend.date().strftime("%Y%m%d")] = {
                    "fyend": fyend,
                    "fystart": datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S"),
                    "income": row[3],
                    "expend": row[4],
                }
            
    for i in charities:
        update = {"finances": charities[i]}
        years = [int(k) for k in charities[i].keys()]
        if len(years):
            latest_year = max(years)
            update["income"] = charities[i][str(latest_year)]["income"]
            update["expend"] = charities[i][str(latest_year)]["expend"]
            update["fye"] = charities[i][str(latest_year)]["fyend"]
        bulk.find({'_id': i}).update({"$set": update})
            
    print_mongo_bulk_result(bulk.execute(), "charities", [
                            "** Importing CCEW data from extract_financial.csv **"])
    bulk = db.charities.initialize_unordered_bulk_op()

    # go through the registration file
    with open(os.path.join(ccew_folder, "extract_registration.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a)
        charities = {}
        for row in csvreader:
            if len(row) < 2 or row[0].strip()=="" or int(row[1]) != 0:
                continue
            row = clean_row(row)
            charity_id = row[0]
            if charity_id not in charities:
                charities[charity_id] = []
            charities[charity_id].append({
                "regdate": datetime.datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"),
                "remdate": datetime.datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S") if row[3] else None,
                "remcode": row[3],
            })

    for i in charities:
        reg_years = sorted(charities[i], key=lambda k: k["regdate"])
        bulk.find({'_id': i}).update({"$set": {
                "date_registered": reg_years[0]["regdate"],
                "date_removed": reg_years[0]["remdate"],
            }})

    print_mongo_bulk_result(bulk.execute(), "charities", [
                            "** Importing CCEW data from extract_registration.csv **"])
    bulk = db.charities.initialize_unordered_bulk_op()

    # go through the objects file
    with open(os.path.join(ccew_folder, "extract_objects.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a, escapechar="\\", doublequote=False)
        charities = {}
        for row in csvreader:
            if len(row) < 2 or row[0].strip()=="" or int(row[1]) != 0:
                continue
            row = clean_row(row)
            charity_id = row[0]
            if charity_id not in charities:
                charities[charity_id] = []
            charities[charity_id].append([row[2], row[3]])

    for i in charities:
        seqnos = [o[0] for o in charities[i]]
        objects = []
        for o in charities[i]:
            if not o[1]:
                continue
            for s in seqnos:
                if o[1].endswith(s):
                    o[1] = o[1][:-4]
            objects.append(o[1])
        bulk.find({'_id': i}).update({"$set": {"objects": "".join(objects)}})

    print_mongo_bulk_result(bulk.execute(), "charities", [
                            "** Importing CCEW data from extract_objects.csv **"])


CCNI_FIELD_MAP = {
    "Reg charity number": "reg_number",
    "Charity name": "name",
    "Date registered": "date_registered",
    "What the charity does": "purpose",
    "Who the charity helps": "beneficiaries",
    "How the charity works": "activities",
    "Public address": "address",
    "Website": "web",
    "Total income": "income",
    "Total spending": "spending",
    "Date for financial year ending": "fye",
    "Email": "email",
    "Telephone": "phone",
    "Company number": "company_number",
}

# download Northern Ireland register of charities
def fetch_ccni(ccni):
    print("[CCNI] Using url: %s" % ccni)
    download_file(ccni, os.path.join('data', 'ccni.csv'))
    print("[CCNI] CSV downloaded")


def import_ccni(datafile=None):
    db = get_db()
    bulk = db.charities.initialize_unordered_bulk_op()

    # first reset some initial data
    db.charities.update_many({"source": "Charity Commission Northern Ireland"}, {"$set": {
        "active": False
    }})

    if not datafile:
        datafile = os.path.join("data", "ccni.csv")

    # go through the Northern Irish charities
    with open(datafile, encoding="latin1") as a:
        csvreader = csv.DictReader(a)
        for row in csvreader:
            row = ccni_row_to_object(row)
            bulk.find({'_id': row["_id"]}).upsert().replace_one(row)

    print_mongo_bulk_result(bulk.execute(), "charities", [
                            "** Importing CCNI data **"])


def ccni_row_to_object(row):
    clean_params = {
        "date_fields": ["Date registered", "Date for financial year ending"],
        "date_order": "DMY",
        "int_fields": ["Total income",
                       "Total spending",
                       "Charitable spending",
                       "Income generation and governance",
                       "Retained for future use",
                       ],
        "csv_fields": ["What the charity does",
                       "Who the charity helps",
                       "How the charity works",
                       ],
    }
    row = clean_row(row, **clean_params)
    new_row = {}

    for old_f in CCNI_FIELD_MAP:
        new_f = CCNI_FIELD_MAP[old_f]
        new_row[new_f] = row.get(old_f, None)

    new_row["source"] = "Charity Commission Northern Ireland"
    new_row["active"] = row["Status"] != "Removed"
    new_row["dual_registered"] = False
    new_row["last_updated"] = datetime.datetime.now()
    new_row["reg_number"] = "NI" + new_row["reg_number"]
    address = new_row["address"].split(",")
    if address[-1].strip().startswith("BT"):
        new_row["postcode"] = address[-1].strip()
        new_row["address"] = ",".join(address[:-1]).strip()
    else:
        new_row["postcode"] = None
    new_row["_id"] = new_row["reg_number"]
    return new_row
