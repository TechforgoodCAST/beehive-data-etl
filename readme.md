From 360 Giving to Beehive Data
===============================

1. Download from grantnav
-------------------------

Use this file: <http://grantnav.threesixtygiving.org/api/grants.json>. Big file:
 ~450Mb.

Shown on the [Developer page](http://grantnav.threesixtygiving.org/developers).

2. Import into mongo
--------------------

```python
from pymongo import MongoClient
import json

client = MongoClient('localhost', 27017)
db = client['360giving']


grantnav = 'grantnav-20170301150836.json'

with open(grantnav) as g:
    grants = json.load(g)

bulk_limit = 10000
bulk = []
for i in grants["grants"]:
    bulk.append(i)
    if len(bulk)>=bulk_limit:
        db.grants.insert_many(bulk)
        bulk = []

if len(bulk)>0:
    db.grants.insert_many(bulk)
```

Found in `to_mongo.py`.

3. Make `charity-base` work
---------------------------

Need to make sure that the `mainCharity.companyNumber` field has an index on
to make lookups quicker

4. Add classification details
-----------------------------

Run `add_class.py`. This currently adds organisation classification details
by matching with data about charities, found in the `charity-base` mongo
collection.

These are based on the codes used by the Charity Commission and OSCR, rather
than the Beehive categories. A readacross between the two is found in
`field-readacross.csv`.

**@todo** Add keyword searching for beneficiaries based on the grant description
(ie classify at the grant level not organisation level). Some exploration of
this started in

5. Transform into Beehive data structure
----------------------------------------

Structure found here: <https://beehive-data.api-docs.io/v1/grants/NL6w7tWRLTM2vhdSE>

Need to:

### 1. Change data schema to match Beehive data

Use similar to [this rake task on Beehive data](https://github.com/TechforgoodCAST/beehive-data/blob/master/lib/tasks/import.rake)
to transform the grant record into the right format.

### 2. Add charity details from charity-base.


### 3. Add company details from Companies House API/URIs.


### 4. Add `beneficiaries` and `locations` data to grant record.


### 5. Add the fund slug


6. Import into Beehive data
---------------------------

Options:

- Rake task? From JSON output by this process?
- Convert above to ruby code and integrate into `beehive-data`.
