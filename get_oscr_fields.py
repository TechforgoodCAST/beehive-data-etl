from pymongo import MongoClient
from sets import Set
import json

client = MongoClient('localhost', 27017)
db = client['charity-base']
fields = {"beneficiaries":Set([]),"purposes":Set([]),"activities":Set([])}
for k,org in enumerate(db.charities.find()):
    for i in ["beneficiaries","purposes","activities"]:
        if "beta" in org:
            if i in org["beta"]:
                if len(org["beta"][i])>0:
                    try:
                        fields[i].update(org["beta"][i])
                    except TypeError:
                        pass

for i in ["beneficiaries","purposes","activities"]:
    fields[i] = list(fields[i])

with open("oscr-fields.json", "wb") as a:
    json.dump(fields, a, indent=4)
