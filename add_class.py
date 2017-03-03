from pymongo import MongoClient

client = MongoClient('localhost', 27017)
gdb = client['360giving']
cdb = client['charity-base']

classes = {}
for i in client['cc-register'].extract_class_ref.find():
    if i["classtext"]:
        classes[i["classno"]] = i["classtext"]
print classes

def parseCharityNumber(regno):
    regno = regno.replace('No.', '')
    regno = regno.replace('GB-CHC-', '')
    regno = regno.replace(' ', '').upper().replace('O', '0');
    return regno

for k,grant in enumerate(gdb.grants.find()):
    update = False

    if "beneficiaries" not in grant:
        grant["beneficiaries"] = []
    beneficiaries = grant["beneficiaries"]

    for key,org in enumerate(grant["recipientOrganization"]):
        if "charityNumber" in org:
            ccnumber = parseCharityNumber(org["charityNumber"])
            char = cdb.charities.find_one({"charityNumber": ccnumber, "subNumber": 0})
            if char:
                if "class" in char:
                    beneficiaries += [classes[str(c)] for c in char["class"] if c>200 and c<300]
                if "beta" in char:
                    if "beneficiaries" in char["beta"]:
                        beneficiaries += char["beta"]["beneficiaries"]
                #print grant["_id"], ccnumber, beneficiaries
                #gdb.grants.update_one({"_id": grant["_id"]}, grant)
            else:
                print ccnumber, "NOT FOUND"

    if len(beneficiaries)>0:
        beneficiaries = [b.lower().replace(' / ', '/') for b in beneficiaries]
        beneficiaries = list(set(beneficiaries))
        update = True
        grant["beneficiaries"] = beneficiaries

    if update:
        gdb.grants.replace_one({"_id": grant["_id"]}, grant)

    if k % 10000==0:
        print "Processed row", k
