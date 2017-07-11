from test_beehivedata import BeehivedataTestCase
from beehivedata.actions.fetch_data import *
import beehivedata.db
import os
import datetime


class IntegrationsTestCase(BeehivedataTestCase):

    def test_fund_summary(self):
        rv = self.app.get('/v1/integrations/fund_summary/millfield-house-foundation-main-fund')
        assert rv.status_code == 401

        rv = self.login("test@example.com", 'test')
        assert b'Logged in successfully' in rv.data

        rv = self.app.get('/v1/integrations/fund_summary/millfield-house-foundation-main-fund')
        assert rv.status_code == 200
