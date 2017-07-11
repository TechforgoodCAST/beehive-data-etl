import os
import unittest
import tempfile

from flask import g, current_app, appcontext_pushed
from flask_login import login_user
from contextlib import contextmanager
import mongomock

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
        beehivedata.db.init_db()
        self.setup_test_user()
        self.setup_test_data()

    def setup_database(self):
        client = mongomock.MongoClient()
        self.db = client['360giving_test']
        setattr(g, 'db', self.db)
        current_app.logger.info("Connected to '%s' mongomock database [host: %s, port: %s]" % (
            self.db.name,
            self.db.client.address[0],
            self.db.client.address[1]
        ))

    def setup_test_user(self):
        register_user("test@example.com", "test", "Test User")
        app.config['WTF_CSRF_ENABLED'] = False

    def setup_test_data(self):
        db = beehivedata.db.get_db()

        fetch_register(os.path.join(os.path.dirname(__file__), "seed_data/dcat.json"), self.tempdir.name)

        # change file urls to the test data
        for i in db["files"].find():
            i["distribution"][0]["downloadURL"] = os.path.join(os.path.dirname(__file__), i["distribution"][0]["downloadURL"])
            db["files"].replace_one({"_id": i["_id"]}, i)

        process_register(save_dir=self.tempdir.name)

    def login(self, username, password):
        return self.app.post('/login', data=dict(
            email=username,
            password=password
        ), follow_redirects=True)

    def logout(self):
        return self.app.get('/logout', follow_redirects=True)

    def tearDown(self):
        db = beehivedata.db.get_db()
        current_app.logger.info("Disconnecting from '%s' mongomock database [host: %s, port: %s]" % (
            db.name,
            db.client.address[0],
            db.client.address[1]
        ))
        db.client.close()
        self.app_context.pop()
        self.tempdir.cleanup()


if __name__ == '__main__':
    unittest.main()
