From 360 Giving to Beehive Data
===============================

## 1. Download grantnav and import into Mongo

Use this file: <http://grantnav.threesixtygiving.org/api/grants.json>. Big file:
 ~450Mb.

Shown on the [Developer page](http://grantnav.threesixtygiving.org/developers).

Do this by running:

```bash
$ python input.py
```

The command line options for this are:

- `--grantnav`: location of the grantnav JSON file, can be a local file or a URL.
  Default is <http://grantnav.threesixtygiving.org/api/grants.json>
- `--mongo-port`: port for acccessing mongo (default `27017`)
- `--mongo-host`: host for accessing mongo (default `localhost`)
- `--mongo-db`: name of the database to insert into (default `360giving`)
- `--limit`: number of records to insert at once (default `10000`)

## 2. Setup `charity-base`

Clone from [Github Repository](https://github.com/tithebarn/charity-base).
[Download the OSCR register](http://www.oscr.org.uk/charities/search-scottish-charity-register/charity-register-download),
and then run commands to add Charity Commission and OSCR data to MongoDB:

```bash
$ npm install
$ node data/download-register.js --year 2016 --month 09 --out ./data/cc-register.zip
$ node data/zip-to-csvs.js --in ./data/cc-register.zip --out ./data/cc-register-csvs --type cc
$ node data/zip-to-csvs.js --in ./data/CharityExport-17-Mar-2017.zip --out ./data/oscr-register-csvs --type oscr
$ node data/csvs-to-mongo.js --in ./data/oscr-register-csvs --dbName oscr-register --type oscr
$ node data/csvs-to-mongo.js --in ./data/cc-register-csvs/RegPlusExtract_March_2017 --dbName cc-register --type cc
$ node data/merge-extracts.js --batchSize 5000
$ mongo charity-base --eval "db.charities.createIndex({'mainCharity.companyNumber': 1})" # create index on companyNumber
$ node supplement.js --scrapeBatchSize 5 # optional
```

You'll also need to make sure that the `mainCharity.companyNumber` field has an
index to make lookups quicker. This is done by running `mongo charity-base --eval "db.charities.createIndex({'mainCharity.companyNumber': 1})"`.
If you don't do this then the next step will take too long.

## 3. Add classification details and transform into Beehive data structure

Run `output.py`. This iterates through all the grants in the `360giving`.`grants`
MongoDB collection. Using the `Grant` class in `grant.py` it creates an object
for each grant.

```bash
$ python output.py
```

The `g.process_grant()` function does the following:

1.  Get data about the recipient from the `charity-base`.`charities` MongoDB
    collection (`Grant.fetch_recipients()`). This also tries to work out the
    type of organisation, how long they have operated for, and get the latest
    financial information.

    _Note: this stage allows for multiple recipients, but the end result only
    outputs the first recipient._

    **@todo**: Add in companies data here too.

2.  Produce a list of beneficiaries for the grant (`Grant.get_beneficiaries()`).
    This is based on the list found in the `Grant.ben_categories` variable. The
    list is generated in two ways:

    1. Through mapping the Charity Commission and OSCR beneficiary categories
    for the recipient organisation to the Grant.ben_categories. These mappings
    are found in `Grant.cc_to_beehive` and `Grant.oscr_to_beehive`.

    2. Through applying a series of regular expressions to the title and
    description of the grant. These regular expressions are found in `Grant.ben_regexes`.
    If a regular expression matches then that beneficiary category is added to
    the grant.

3.  Fill in the `affect_people` and `affect_other` variables using
    `Grant.get_affected()`.

4.  Get a list of the age ranges that the grant relates to using
    `Grant.get_ages()`. This is done in two ways:

    1. Through applying a series of regular expressions for keywords (like "child"
    "elderly", etc) to the grant title and description. These are found in
    `Grant.age_regexes` and they are transformed into age ranges based on
    `Grant.age_bens`.

    2. Through applying a regular expression that looks for strings like "5-15
    years" in the grant description, and extracting the resulting start and end
    ages.

    These two results are transformed into the Beehive age categories (found in
    `Grant.age_categories` through looking at overlap in the age ranges.

5.  Attempt to classify the genders intended to benefit from the grant. This
    uses a series of regexes (in `Grant.gender_regexes`) to look for grants that
    mention ("men", "women" or "transgender"). If only one of those categories
    are selected then it is chosen, otherwise the field is "All genders".

**@todo**: Add location classification details.

After the `Grant.process_grant()` is run the grant is ready to be output in the
[correct structure for `beehive-data`](https://beehive-data.api-docs.io/v1/grants/NL6w7tWRLTM2vhdSE).
This is done using `Grant.beehive_output()`.

The only non-formatting change that happens at the output stage is to pass the
funder and grant programme through `Grant.get_grant_programme()` which uses
`Grant.swap_funds` to change the name of some of the grant programmes in the
data to make them more useful. Not all funders and funds are included - any not
found in `Grant.swap_funds` are passed through as-is.

The command line options for `output.py` are:

- `--mongo-port`: port for acccessing mongo (default `27017`)
- `--mongo-host`: host for accessing mongo (default `localhost`)
- `--grant-db`: name of the database holding 360 giving data (default `360giving`)
- `--charity-db`: name of the database holding charity data from `charity-base` (default `charity-base`)
- `--output-db`: name of the database to output data in correct format (default `beehive-data`)
- `--limit`: number of records to insert at once (default `10000`)

## 4. Import into Beehive data

Options:

- Rake task? From JSON output by this process?
- Convert above to ruby code and integrate into `beehive-data`.
