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
from ..assets.name_parse import parse_name
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
    TERMS_AND_CONDITIONS_TEXT = "ContentPlaceHolderDefault_WebsiteContent_ctl05_CharityRegDownload_10_lblTermsConditions"
    TERMS_AND_CONDITIONS_CHECKBOX = "ctl00$ctl00$ctl00$ContentPlaceHolderDefault$WebsiteContent$ctl05$CharityRegDownload_10$cbTermsConditions"

    browser = mechanicalsoup.StatefulBrowser()
    print("[OSCR] Using url: %s" % oscr)
    browser.open(oscr)

    # get the terms and conditions box
    page = browser.get_current_page()
    tandcs = page.find(id=TERMS_AND_CONDITIONS_TEXT)
    print("[OSCR] To continue accept the following terms and conditions")
    print(tandcs.text)
    accept = input("[OSCR] Do you accept the terms and conditions? (y/n) ")
    if accept[0].strip().lower()!="y":
        print("[OSCR] Did not download OSCR data as terms and conditions not accepted")
        return

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
    print("[OSCR] importing charities")
    with open(datafile, encoding="latin1") as a:
        csvreader = csv.DictReader(a)
        for count, row in enumerate(csvreader):
            row = oscr_row_to_object(row)
            bulk.find({'_id': row["_id"]}).upsert().replace_one(row)
            if count % 10000 == 0:
                print('\r', "[OSCR] %s charities imported" % count, end='')
        print('\r', "[OSCR] %s charities imported" % count)

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


# get charity commission area of operation mapping file
def fetch_ccew_aoo(aoo_file):
    print("[CCEW] Using url: %s" % aoo_file)
    download_file(aoo_file, os.path.join('data', 'ccew_aoo.csv'))
    print("[CCEW] AOO mapping downloaded")

ccew_csv_options = {"escapechar": "\\", "doublequote": False}

def import_ccew():
    db = get_db()
    ccew_folder = os.path.join("data", "ccew")

    # first reset some initial data
    db.charities.update_many({"source": "Charity Commission for England and Wales"}, {"$set": {
        "purpose": [],
        "beneficiaries": [],
        "activities": [],
        "active": False
    }})

    # then run imports for specific tables
    charities = import_ccew_charity(ccew_folder)
    charities = import_ccew_main_charity(ccew_folder, charities)
    charities = import_ccew_classification(ccew_folder, charities)
    charities = import_ccew_financial(ccew_folder, charities)
    charities = import_ccew_registration(ccew_folder, charities)
    charities = import_ccew_objects(ccew_folder, charities)
    charities = import_ccew_geography(ccew_folder, charities)


    print("[CCEW] %s charities to import to database" % len(charities))
    bulk = db.charities.initialize_unordered_bulk_op()
    for i in charities:
        bulk.find({'_id': i}).upsert().replace_one(charities[i])

    print_mongo_bulk_result(bulk.execute(), "charities", [
                            "** Importing CCEW data **"])


def import_ccew_charity(ccew_folder, charities = {}):
    # go through the main charity file
    db = get_db()

    print("[CCEW] importing ccew_charity")
    with open(os.path.join(ccew_folder, "extract_charity.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a, **ccew_csv_options)
        for count, row in enumerate(csvreader):
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
            charities[new_row["_id"]] = new_row
            if count % 10000 == 0:
                print('\r', "[CCEW] %s records imported" % count, end='')
        print('\r', "[CCEW] %s records imported" % count)

    return charities


def import_ccew_main_charity(ccew_folder, charities):
    # go through the main_charity file
    db = get_db()

    print("[CCEW] importing ccew_main_charity")
    with open(os.path.join(ccew_folder, "extract_main_charity.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a, **ccew_csv_options)
        for count, row in enumerate(csvreader):
            if len(row) < 10 or row[0].strip()=="":
                continue
            charity_id = row[0].strip()
            new_row = {
                "company_number": row[1].strip(),
                "web": row[9].strip(),
                "email": row[8].strip(),
            }
            charities[charity_id].update(new_row)
            if count % 10000 == 0:
                print('\r', "[CCEW] %s records imported" % count, end='')
        print('\r', "[CCEW] %s records imported" % count)

    return charities

def import_ccew_classification(ccew_folder, charities):
    # go through the classification file
    db = get_db()

    with open(os.path.join(ccew_folder, "extract_class_ref.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a, **ccew_csv_options)
        class_ref = {}
        for count, row in enumerate(csvreader):
            if len(row) < 2 or row[0].strip()=="":
                continue
            class_ref[row[0]] = row[1]
    
    print("[CCEW] importing ccew_classification")
    with open(os.path.join(ccew_folder, "extract_class.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a, **ccew_csv_options)
        class_types = {
            "1": "purpose",
            "2": "beneficiaries",
            "3": "activities"
        }
        for count, row in enumerate(csvreader):
            if len(row) < 2 or row[0].strip()=="":
                continue
            charity_id = row[0].strip()
            class_ = row[1].strip()
            class_type = class_types.get(class_[0])
            class_data = class_ref.get(class_)

            if class_type not in charities[charity_id]:
                charities[charity_id][class_type] = []
            charities[charity_id][class_type].append(class_data)
            if count % 10000 == 0:
                print('\r', "[CCEW] %s records imported" % count, end='')
        print('\r', "[CCEW] %s records imported" % count)

    return charities

def import_ccew_financial(ccew_folder, charities):
    # go through the finances file
    db = get_db()

    print("[CCEW] importing ccew_financial")
    with open(os.path.join(ccew_folder, "extract_financial.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a, **ccew_csv_options)
        charity_finances = {}
        for count, row in enumerate(csvreader):
            if len(row) < 2 or row[0].strip()=="":
                continue
            row = clean_row(row, int_fields=[3,4], date_order="YMD")
            charity_id = row[0]
            if charity_id not in charity_finances:
                charity_finances[charity_id] = {}
            fyend = datetime.datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S")
            if row[3] or row[4]:
                charity_finances[charity_id][fyend.date().strftime("%Y%m%d")] = {
                    "fyend": fyend,
                    "fystart": datetime.datetime.strptime(row[1], "%Y-%m-%d %H:%M:%S"),
                    "income": row[3],
                    "expend": row[4],
                }
            if count % 10000 == 0:
                print('\r', "[CCEW] %s records imported" % count, end='')
        print('\r', "[CCEW] %s records imported" % count)

    # go through the partb file
    print("[CCEW] importing ccew_partb")
    with open(os.path.join(ccew_folder, "extract_partb.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a, **ccew_csv_options)
        for count, row in enumerate(csvreader):
            if len(row) < 2 or row[0].strip()=="":
                continue
            row = clean_row(row, int_fields=list(range(4, 43)), date_order="YMD")
            charity_id = row[0]
            if charity_id not in charity_finances:
                charity_finances[charity_id] = {}
            fyend = datetime.datetime.strptime(row[3][0:19], "%Y-%m-%d %H:%M:%S")
            if row[3] or row[4]:
                partb = {
                    "fyend": fyend,
                    "fystart": datetime.datetime.strptime(row[2][0:19], "%Y-%m-%d %H:%M:%S"),
                    "inc_leg": row[4],
                    "inc_end": row[5],
                    "inc_vol": row[6],
                    "inc_fr": row[7],
                    "inc_char": row[8],
                    "inc_invest": row[9],
                    "inc_other": row[10],
                    "inc_total": row[11],
                    "invest_gain": row[12],
                    "asset_gain": row[13],
                    "pension_gain": row[14],
                    "exp_vol": row[15],
                    "exp_trade": row[16],
                    "exp_invest": row[17],
                    "exp_grant": row[18],
                    "exp_charble": row[19],
                    "exp_gov": row[20],
                    "exp_other": row[21],
                    "exp_total": row[22],
                    "exp_support": row[23],
                    "exp_dep": row[24],
                    "reserves": row[25],
                    "asset_open": row[26],
                    "asset_close": row[27],
                    "fixed_assets": row[28],
                    "open_assets": row[29],
                    "invest_assets": row[30],
                    "cash_assets": row[31],
                    "current_assets": row[32],
                    "credit_1": row[33],
                    "credit_long": row[34],
                    "pension_assets": row[35],
                    "total_assets": row[36],
                    "funds_end": row[37],
                    "funds_restrict": row[38],
                    "funds_unrestrict": row[39],
                    "funds_total": row[40],
                    "employees": row[41],
                    "volunteers": row[42],
                    "cons_acc": row[43]=="Y",
                    "charity_acc": row[44]=="Y"
                }
                if fyend.date().strftime("%Y%m%d") not in charity_finances[charity_id]:
                    charity_finances[charity_id][fyend.date().strftime("%Y%m%d")] = {}
                charity_finances[charity_id][fyend.date().strftime("%Y%m%d")].update(partb)
            if count % 10000 == 0:
                print('\r', "[CCEW] %s records imported" % count, end='')
        print('\r', "[CCEW] %s records imported" % count)

    print("[CCEW] processing ccew_financial and ccew_partb")
    for i in charity_finances:
        update = {"finances": charity_finances[i]}
        years = [int(k) for k in charity_finances[i].keys()]
        if len(years):
            latest_year = max(years)
            update["income"] = charity_finances[i][str(latest_year)]["income"]
            update["expend"] = charity_finances[i][str(latest_year)]["expend"]
            update["employees"] = charity_finances[i][str(latest_year)].get("employees")
            update["volunteers"] = charity_finances[i][str(
                latest_year)].get("volunteers")
            update["grants_made"] = charity_finances[i][str(
                latest_year)].get("exp_grant")
            update["fye"] = charity_finances[i][str(latest_year)]["fyend"]
        update["finances"] = [update["finances"][i] for i in sorted(update["finances"].keys())]
        charities[i].update(update)

    return charities

def import_ccew_registration(ccew_folder, charities):
    # go through the registration file
    db = get_db()

    print("[CCEW] importing ccew_registration")
    with open(os.path.join(ccew_folder, "extract_registration.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a, **ccew_csv_options)
        charity_registrations = {}
        for count, row in enumerate(csvreader):
            if len(row) < 2 or row[0].strip()=="" or int(row[1]) != 0:
                continue
            row = clean_row(row)
            charity_id = row[0]
            if charity_id not in charity_registrations:
                charity_registrations[charity_id] = []
            charity_registrations[charity_id].append({
                "regdate": datetime.datetime.strptime(row[2], "%Y-%m-%d %H:%M:%S"),
                "remdate": datetime.datetime.strptime(row[3], "%Y-%m-%d %H:%M:%S") if row[3] else None,
                "remcode": row[3],
            })
            if count % 10000 == 0:
                print('\r', "[CCEW] %s records imported" % count, end='')
        print('\r', "[CCEW] %s records imported" % count)

    print("[CCEW] processing ccew_registration")
    for i in charity_registrations:
        reg_years = sorted(charity_registrations[i], key=lambda k: k["regdate"])
        charities[i].update({
                "date_registered": reg_years[0]["regdate"],
                "date_removed": reg_years[-1]["remdate"],
            })

    return charities

def import_ccew_objects(ccew_folder, charities):
    # go through the objects file
    db = get_db()
    bulk = db.charities.initialize_unordered_bulk_op()

    print("[CCEW] importing ccew_objects")
    with open(os.path.join(ccew_folder, "extract_objects.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a, **ccew_csv_options)
        charity_objects = {}
        for count, row in enumerate(csvreader):
            if len(row) < 2 or row[0].strip()=="" or int(row[1]) != 0:
                continue
            row = clean_row(row)
            charity_id = row[0]
            if charity_id not in charity_objects:
                charity_objects[charity_id] = []
            charity_objects[charity_id].append([row[2], row[3]])
            if count % 10000 == 0:
                print('\r', "[CCEW] %s records imported" % count, end='')
        print('\r', "[CCEW] %s records imported" % count)

    print("[CCEW] processing ccew_objects")
    for i in charity_objects:
        seqnos = [o[0] for o in charity_objects[i]]
        objects = []
        for o in charity_objects[i]:
            if not o[1]:
                continue
            for s in seqnos:
                if o[1].endswith(s):
                    o[1] = o[1][:-4]
            objects.append(o[1])
        charities[i]["objects"] = "".join(objects)

    return charities

def import_ccew_geography(ccew_folder, charities):
    # go through the geography file
    db = get_db()

    with open(os.path.join("data", "ccew_aoo.csv")) as a:
        csvreader = csv.DictReader(a, **ccew_csv_options)
        aoo = {}
        for count, row in enumerate(csvreader):
            row["aooname"] = parse_name(
                row["aooname"].strip().replace("THROUGHOUT ", "").replace(" CITY", ""))
            row["aoosort"] = parse_name(
                row["aoosort"].strip().replace("THROUGHOUT ", "").replace(" CITY", ""))
            row["iso3166_1"] = row.pop("ISO3166-1", None)
            row["iso3166_2_GB"] = row.pop("ISO3166-2:GB", None)
            aoo[(row["aootype"], row["aookey"])] = row

    print("[CCEW] importing ccew_geography")
    with open(os.path.join(ccew_folder, "extract_charity_aoo.csv"), encoding="latin1") as a:
        csvreader = csv.reader(a, **ccew_csv_options)
        charity_aoos = {}
        for count, row in enumerate(csvreader):
            if len(row) < 2 or row[0].strip()=="":
                continue
            row = clean_row(row)
            charity_id = row[0]
            if charity_id not in charity_aoos:
                charity_aoos[charity_id] = []
            area_id = (row[1], row[2])
            if area_id not in aoo:
                print("Area %s not found" % area_id)
            charity_aoos[charity_id].append(aoo[area_id])
            if count % 10000 == 0:
                print('\r', "[CCEW] %s records imported" % count, end='')
        print('\r', "[CCEW] %s records imported" % count)

    print("[CCEW] processing ccew_geography")
    for i in charity_aoos:
        geo_area = get_geo_area(charity_aoos[i])
        charities[i].update({
            "areas": charity_aoos[i],
            "geo_area": get_geo_area(charity_aoos[i])
        })

    return charities

def get_geo_area(areas):

    if len(areas) == 1:
        return areas[0]["aooname"]

    types = list(set([a["aootype"] for a in areas]))

    continent_lookup = {
        "AF": "Africa",
        "AS": "Asia",
        "EU": "Europe",
        "NA": "North America",
        "SA": "South America",
        "OC": "Oceania",
        "AN": "Antarctica",
    }
    uk = { 
        "aootype": "D",
        "aookey": "",
        "aooname": "United Kingdom",
        "aoosort": "United Kingdom",
        "welsh": "",
        "master": "",
        "GSS": "",
        "iso3166_1": "GB",
        "iso3166_2_GB": "",
        "ContinentCode": "EU",
        "oldCode": "",
    }
    continents = sorted(list(set([continent_lookup[a["ContinentCode"]] for a in areas])))
    countries = sorted(list(set([a["iso3166_1"] for a in areas])))
    districts = sorted(list(set([a["iso3166_2_GB"] for a in areas if a["iso3166_2_GB"] != ""])))

    if countries == ["GB"]:

        if districts == sorted(["GB-SCT", "GB-NIR", "GB-EAW"]):
            return "United Kingdom"
        if districts == sorted(["GB-SCT", "GB-EAW"]):
            return "Great Britain"
        if districts == sorted(["GB-SCT", "GB-NIR"]):
            return "Scotland and Northern Ireland"
        if districts == sorted(["GB-EAW", "GB-NIR"]):
            return "England, Wales and Northern Ireland"

    if len(types) == 1:

        if types[0] == "B" or types[0] == "C":
            if len(areas) <= 5:
                return to_sentence([a["aooname"] for a in areas])
            else:
                return "{:,.0f} areas across the UK".format(len(areas))

        if types[0] == "D":
            if len(areas) <= 5:
                return to_sentence([a["aooname"] for a in areas])
            elif len(continents) <= 2:
                return "{:,.0f} countries across {}".format(len(areas), to_sentence(continents))
            elif len(areas) > 100:
                return "Worldwide"
            else:
                return "{:,.0f} countries".format(len(areas))

    if len(countries) > 1:
        if "GB" in countries:
            return get_geo_area([a for a in areas if a["aootype"] == "D" and a["iso3166_2_GB"] == ""] + [uk])
        else:
            return get_geo_area([a for a in areas if a["aootype"] == "D" and a["iso3166_2_GB"] == ""])


def to_sentence(array, words_connector=", ", two_words_connector=" and ", last_word_connector=", and "):
    if len(array) == 1:
        return array[0]
    if len(array) == 2:
        return two_words_connector.join(array)

    return words_connector.join(array[:-1]) + last_word_connector + array[-1]


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
    print("[CCNI] importing charities")
    with open(datafile, encoding="latin1") as a:
        csvreader = csv.DictReader(a)
        for count, row in enumerate(csvreader):
            row = ccni_row_to_object(row)
            bulk.find({'_id': row["_id"]}).upsert().replace_one(row)
            if count % 10000 == 0:
                print('\r', "[CCNI] %s charities imported" % count, end='')
        print('\r', "[CCNI] %s charities imported" % count)

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
