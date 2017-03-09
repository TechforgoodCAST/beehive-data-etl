from __future__ import print_function
from grant import Grant
import json
from pymongo import MongoClient

if __name__ == '__main__':

    client = MongoClient('localhost', 27017)
    db = client['360giving']
    cdb = client['charity-base']

    #for k,g in enumerate(db.grants.aggregate([{"$sample": {"size":1000}}])):
    for k,g in enumerate(db.grants.find()):
        g = Grant(g, cdb)
        g.process_grant()
        g_output = g.beehive_output()
        client["beehive-data"].grants.replace_one({"grant_identifier": g_output["grant_identifier"]}, g_output, upsert=True)
        #print(json.dumps({i: g_output["recipient"][i] for i in ["income","spending","employees","volunteers"]}, indent=4))
        if k % 1000 == 0:
            print(k)
