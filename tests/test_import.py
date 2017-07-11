from test_beehivedata import BeehivedataTestCase
from beehivedata.actions.fetch_data import *
import beehivedata.db
import os
import datetime


class ImportTestCase(BeehivedataTestCase):

    def setup_test_data(self):
        pass

    def test_fetch_register(self):
        fetch_register(os.path.join(os.path.dirname(__file__), "seed_data/dcat.json"), self.tempdir.name)
        assert self.db["files"].count() == 2

        funder_1 = "a002400000lfOfMAAU"
        i = self.db["files"].find_one({"_id": funder_1})
        assert i["_id"] == funder_1
        assert isinstance(i["issued"], datetime.datetime)
        assert isinstance(i["modified"], datetime.datetime)
        assert i["publisher"]["slug"] == "millfield-house-foundation"

    def test_process_register(self):
        fetch_register(os.path.join(os.path.dirname(__file__), "seed_data/dcat.json"), self.tempdir.name)

        # change file urls to the test data
        for i in self.db["files"].find():
            i["distribution"][0]["downloadURL"] = os.path.join(os.path.dirname(__file__), i["distribution"][0]["downloadURL"])
            self.db["files"].replace_one({"_id": i["_id"]}, i)

        process_register(save_dir=self.tempdir.name)

        # check all grants imported
        assert self.db["grants"].count() == 43

        # check an individual grant
        grant = self.db["grants"].find_one({"_id": "360g-mhfdn-PhilanthropyStory2014"})
        assert grant["fundingOrganization"][0]["slug"] == "millfield-house-foundation"
        assert grant["grantProgramme"][0]["slug"] == "main-fund"
        assert grant["fund_slug"] == "millfield-house-foundation-main-fund"
        assert isinstance(grant["awardDate"], datetime.datetime)
        assert grant["recipientOrganization"][0]["charityNumber"] == "700510"
