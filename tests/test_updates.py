from test_beehivedata import BeehivedataTestCase
from beehivedata.actions.fetch_data import *
from beehivedata.actions.update_beneficiaries import *
from beehivedata.actions.update_charity import *
from beehivedata.actions.update_geography import *
from beehivedata.actions.update_organisations import *
import beehivedata.db
import os
import datetime


class ImportTestCase(BeehivedataTestCase):

    def setup_test_data(self):
        fetch_register(os.path.join(os.path.dirname(__file__), "seed_data/dcat.json"), self.tempdir.name)

        # change file urls to the test data
        for i in self.db["files"].find():
            i["distribution"][0]["downloadURL"] = os.path.join(os.path.dirname(__file__), i["distribution"][0]["downloadURL"])
            self.db["files"].replace_one({"_id": i["_id"]}, i)

        process_register(save_dir=self.tempdir.name)

    def test_update_organisations(self):
        update_organisations()

        # look for organisation types
        grant = self.db["grants"].find_one({"_id": "360G-JRCT-9682"})
        assert grant["beehive"]["org_type"] == 1

        grant = self.db["grants"].find_one({"_id": "360g-mhfdn-RRFNE2015"})
        assert grant["beehive"]["org_type"] == 2

        grant = self.db["grants"].find_one({"_id": "360g-mhfdn-NCAB2015"})
        assert grant["beehive"]["org_type"] == 3

        grant = self.db["grants"].find_one({"_id": "360G-JRCT-9686"})
        assert grant["beehive"]["org_type"] == 4

        grant = self.db["grants"].find_one({"_id": "360G-JRCT-9722"})
        assert grant["beehive"]["org_type"] == 5

        grant = self.db["grants"].find_one({"_id": "360G-JRCT-9712"})
        assert grant["beehive"]["org_type"] == -1

    def test_update_beneficiaries(self):
        update_beneficiaries()

        for i in self.db["grants"].find():
            assert "beehive" in i
            assert "affect_people" in i["beehive"]
            if len(i["beehive"]["ages"]) > 0:
                print(i["_id"], i["beehive"]["ages"])

        grant = self.db["grants"].find_one({"_id": "360G-JRCT-9672"})
        assert "organisation" in grant["beehive"]["beneficiaries"]

        grant = self.db["grants"].find_one({"_id": "360G-JRCT-9629"})
        assert "Female" in grant["beehive"]["gender"]

        grant = self.db["grants"].find_one({"_id": "360g-mhfdn-YHNE2017"})
        assert len(grant["beehive"]["ages"]) == 2
