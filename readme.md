Beehive Data
============

Status
------

[![CircleCI](https://circleci.com/gh/TechforgoodCAST/beehive-data-etl.svg?style=svg&circle-token=375a079d309e74528c5e5600d3646bc20c881f50)](https://circleci.com/gh/TechforgoodCAST/beehive-data-etl)

Initial setup
-------------

- Setup MongoDB and get it running
- Setup CharityBase and import the data into the database
- setup virtual environment, and activate it
- install any needed requirements `pip install -r requirements.txt`
- install the application package through `pip install -e .`
- Add an environment variable `FLASK_APP` pointing to `beehivedata.beehivedata`
- Initialise the database by running `flask init_db`
- Fetch any data using `flask fetch_all`
- Run the server with `flask run`

External libraries used
-----------------------

(Installed through `requirements.txt`)

- [flask](http://flask.pocoo.org/)
- [flass-sass](https://github.com/imiric/flask-sass) - no pypi package
- [flask_login](https://flask-login.readthedocs.io/en/latest/)
- [flask_wtf](https://flask-wtf.readthedocs.io/en/stable/)
- [gunicorn](http://gunicorn.org/) - for deployed version
- [numpy](http://www.numpy.org/) (for windows use [numpy-1.12.1+mkl-cp35-cp35m-win32.whl](http://www.lfd.uci.edu/~gohlke/pythonlibs/#numpy))
- [pymongo](https://api.mongodb.com/python/current/)
- [pytest](https://docs.pytest.org/en/latest/)
- [python-dateutil](https://dateutil.readthedocs.io/en/stable/)
- [requests](http://docs.python-requests.org/en/master/)
- [scipy](https://www.scipy.org/) (for windows use [scipy-0.19.0-cp35-cp35m-win32.whl](http://www.lfd.uci.edu/~gohlke/pythonlibs/#scipy))
- [sklearn](http://scikit-learn.org/stable/)
- [slugify](https://github.com/un33k/python-slugify)
- [flatten-tool](https://github.com/OpenDataServices/flatten-tool) - no pypi package

Run development server
----------------------

Run `flask run` from the command line.

For development/debug mode set `FLASK_DEBUG` environmental variable to `1`.

Setup `charity-base`
--------------------

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


Fetch 360 Giving data
---------------------

This step can either be run in one go using `flask fetch_all`, or in the individual
steps shown below. You can also run all the update procedures without fetching
new data by running `flask update_all`

### 1. Download published data and import into Mongo

This command will fetch the [data registry](http://data.threesixtygiving.org/data.json)
and save it to a mongo database. It then goes through the data registry,
downloads each file, converts to json (if needed) and save all the grants in
the database.

Run the command using:

```bash
$ flask fetch_data
```

The command can also be run to just fetch the files that have been updated since
a given date:

```bash
$ flask fetch_data --files-since 2017-01-01
```

You can also set it to just download the data for a particular funder, using a
comma-separated list of the funder prefixes, slugs or names. Eg:

```bash
$ flask fetch_data --funders 360G-ocf
```

The command line options for this are:

- `--files-since`: fetch only files updated after this date (in `YYYY-MM-DD` format, default all files)
- `--funders`: only fetch these funders (list of funder prefixes separated by comma, default all funders)
- `--registry`: where to find the data registry (default `http://data.threesixtygiving.org/data.json`)

### 2. Update organisation and charity details

These two steps update the organisations in the data. They are run using:

```bash
$ flask update_organisations
$ flask update_charity
```

`update_organisations` tries to guess the organisation type of the recipient
organisation and apply the Beehive codes to it. It also processes the grant
according to the function in `fetch_data`, so it can be useful to rerun if
you don't want to fetch all the data again

`update_charities` gets data about the recipient from the `charity-base`.`charities`
MongoDB collection. It then tries to work out the type of organisation, how long
they have operated for, and get the latest financial information.

_Note: this stage allows for multiple recipients, but the end result only
outputs the first recipient._

**@todo**: Add in companies data here too.

The `update_charity` script has `--host`, `--port`, `--db` which are used
to connect to the charitybase database (the defaults are `localhost:3306/charities`).

### 3. Update beneficiaries

Using regexes and other techniques, try to identify the beneficiaries of each
grant, including the age range and gender.

```bash
$ flask update_beneficiaries
```

### 4. Update geography

Using regexes and other techniques, try to identify the countries served by
each grant.

```bash
$ flask update_geography
```

Deploy to Heroku
----------------

The site is designed to be deployed using Heroku. You'll need to run a mongodb
instance and make the [connection URI](https://docs.mongodb.com/manual/reference/connection-string/)
available as a config variable `MONGODB_URI`.


Run tests
---------

The site uses `pytest` to run the tests. The test database will be created with
a different database name, and then destroyed at the end of every test.

The tests use seed data from `tests/seed_data` which is based on actual 360giving
data. Some of the files have been changed to give a wider range of test scenarios.

The tests are run by running:

```bash
$ python -m pytest tests
```

The deployed version of the site also has [circleci](https://circleci.com/) integration meaning the tests are run after every github commit. The current test status is:

[![CircleCI](https://circleci.com/gh/TechforgoodCAST/beehive-data-etl.svg?style=svg&circle-token=375a079d309e74528c5e5600d3646bc20c881f50)](https://circleci.com/gh/TechforgoodCAST/beehive-data-etl)
