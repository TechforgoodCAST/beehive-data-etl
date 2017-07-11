import os
from beehivedata.beehivedata import app
from beehivedata.login import register_user, User
import beehivedata.db
import unittest
import tempfile
from flask import g, current_app, appcontext_pushed
from flask_login import login_user
from contextlib import contextmanager
import mongomock


class BeehivedataTestCase(unittest.TestCase):

    def setUp(self):
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
        pass

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


if __name__ == '__main__':
    unittest.main()
