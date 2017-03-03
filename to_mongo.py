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
