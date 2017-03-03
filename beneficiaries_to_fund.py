from pymongo import MongoClient
import json

client = MongoClient('localhost', 27017)
gdb = client['360giving']

funds = {}
grantCounts = {}

for k,grant in enumerate(gdb.grants.find()):

    # Set up 
    grantProgramme = 'default'
    if "grantProgramme" in grant:
        if "title" in grant["grantProgramme"][0]:
            grantProgramme = grant["grantProgramme"][0]["title"]
    funder = grant["fundingOrganization"][0]["name"]

    if funder not in funds:
        funds[funder] = {}
        grantCounts[funder] = {}

    if grantProgramme not in funds[funder]:
        funds[funder][grantProgramme] = {}
        grantCounts[funder][grantProgramme] = 0


    has_ben = False
    for key,org in enumerate(grant["recipientOrganization"]):
        if "beneficiaries" in org:
            for b in org["beneficiaries"]:
                if b not in funds[funder][grantProgramme]:
                    funds[funder][grantProgramme][b] = 0
                funds[funder][grantProgramme][b] += 1
                has_ben = True

    if has_ben:
        grantCounts[funder][grantProgramme] += 1

    if k % 10000 == 0:
        print k


new_funds = {}
for funder in funds:
    new_funds[funder] = {}
    for grantProgramme in funds[funder]:
        new_funds[funder][grantProgramme] = {}
        for b in funds[funder][grantProgramme]:
            new_funds[funder][grantProgramme][b] = float(funds[funder][grantProgramme][b]) / float(grantCounts[funder][grantProgramme])
funds = new_funds

with open('beneficiaries_by_fund.json', 'wb') as bens:
    json.dump(funds, bens, indent=4)
    print "Funds saved"
