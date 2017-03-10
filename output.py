from __future__ import print_function
from grant import Grant
import json
from pymongo import MongoClient

if __name__ == '__main__':

    # Connect to MongoDB databases
    client = MongoClient('localhost', 27017)
    db = client['360giving']

    # iterate through every grant in 360giving database
    for k,g in enumerate(db.grants.find()):
        g = Grant(g, client['charity-base']) # generate grant object
        g.process_grant() # process the grant details
        g_output = g.beehive_output() # produce output in Beehive format
        client["beehive-data"].grants.replace_one({"grant_identifier": g_output["grant_identifier"]}, g_output, upsert=True) # add to MongoDB collection
        #print(json.dumps(g_output}, indent=4))
        if k % 1000 == 0:
            print(k)
