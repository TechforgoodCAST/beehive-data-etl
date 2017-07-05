import os
from beehivedata.beehivedata import app
import beehivedata.db
import unittest
import tempfile
from flask import g
import mongomock


class BeehivedataTestCase(unittest.TestCase):

    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        with app.app_context():
            self.setup_database()
            beehivedata.db.init_db()
            self.import_db()

    def setup_database(self):
        client = mongomock.MongoClient()
        g.db = client['360giving']

    def tearDown(self):
        pass

    def test_home(self):
        rv = self.app.get('/')
        assert b'High quality data about charitable funding' in rv.data

    def test_status(self):
        rv = self.app.get('/status')
        assert rv.status_code == 401

if __name__ == '__main__':
    unittest.main()
