# utilities
def clean_row(row):
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

    return row


# get oscr data
def fetch_oscr(oscr):
    with zipfile.ZipFile(oscr) as oscrzip:
        files = oscrzip.infolist()
        if len(files) != 1:
            raise ValueError("More than one file in OSCR zip")
        with open(os.path.join("data", "oscr.csv"), "wb") as oscrcsv:
            oscrcsv.write(oscrzip.read(files[0]))
        print("[OSCR] data extracted")


def import_oscr(datafile):

    # go through the Scottish charities
    with open(datafile, encoding="latin1") as a:
        csvreader = csv.DictReader(a)
        ccount = 0
        cadded = 0
        cupdated = 0
        for row in csvreader:
            row = clean_row(row)


# get charity commission data
def fetch_ccew(ccew):
    ccew_html = urllib.request.urlopen(ccew)
    ccew_out = os.path.join("data", "ccew.zip")
    ccew_folder = os.path.join("data", "ccew")
    if ccew_html.status != 200:
        raise ValueError("[CCEW] Could not find Charity Commission data page. Status %s %s" % (ccew_data.status, ccew_data.reason))
    ccew_html = ccew_html.read()
    ccew_soup = BeautifulSoup(ccew_html, 'html.parser')
    zip_regex = re.compile("http://apps.charitycommission.gov.uk/data/.*?/RegPlusExtract.*?\.zip")
    ccew_data_url = ccew_soup.find("a", href=zip_regex)["href"]
    print("[CCEW] Using url: %s" % ccew_data_url)
    urllib.request.urlretrieve(ccew_data_url, ccew_out)
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


# download Northern Ireland register of charities
def fetch_ccni(ccni):
    print("[CCNI] Using url: %s" % ccni)
    urllib.request.urlretrieve(ccni, os.path.join('data', 'ccni.csv'))
    print("[CCNI] CSV downloaded")
