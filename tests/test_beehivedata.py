import os
import unittest
import tempfile

from flask import g, current_app, appcontext_pushed
from flask_login import login_user
from contextlib import contextmanager

from beehivedata.beehivedata import app
from beehivedata.login import register_user, User
import beehivedata.db
from beehivedata.actions.fetch_data import *


class BeehivedataTestCase(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        app.testing = True
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        self.setup_database()

    def setup_database(self):
        for i in ["MONGODB_URI", "MONGODB_PORT", "MONGODB_HOST"]:
            if current_app.config.get(i.replace("MONGODB_", "MONGODB_TEST_")):
                current_app.config[i] = current_app.config.get(i.replace("MONGODB_", "MONGODB_TEST_"))

        current_app.config["MONGODB_DB"] = current_app.config.get("MONGODB_TEST_DB")
        beehivedata.db.init_db()
        self.db = beehivedata.db.get_db()
        self.setup_test_user()
        self.setup_test_data()

    def setup_test_user(self):
        self.db.users.drop()
        register_user("test@example.com", "test", "Test User")
        app.config['WTF_CSRF_ENABLED'] = False

    def setup_test_data(self):
        fetch_register(os.path.join(os.path.dirname(__file__), "seed_data/dcat.json"), self.tempdir.name)

        # change file urls to the test data
        for i in self.db["files"].find():
            i["distribution"][0]["downloadURL"] = os.path.join(os.path.dirname(__file__), i["distribution"][0]["downloadURL"])
            self.db["files"].replace_one({"_id": i["_id"]}, i)

        process_register(save_dir=self.tempdir.name)

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            email=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def tearDown(self):
        current_app.logger.info("Deleting data from '%s' mongo database [host: %s, port: %s]" % (
            self.db.name,
            self.db.client.address[0],
            self.db.client.address[1]
        ))
        self.db.users.drop()
        self.db.client.drop_database(self.db.name)
        self.app_context.pop()
        self.tempdir.cleanup()


if __name__ == '__main__':
    unittest.main()
