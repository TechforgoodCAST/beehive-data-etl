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

        data = json.loads(rv.data.decode('utf8'))

        assert len(data['grant_examples']) == 3
        assert data['grant_count'] == 12
        assert [g for g in data['beneficiary_distribution'] if g['sort'] == 'poverty'][0]['count'] == 3

    def test_amounts(self):
        rv = self.app.get('/v1/integrations/amounts')
        assert rv.status_code == 401

        rv = self.login("test@example.com", 'test')
        assert b'Logged in successfully' in rv.data

        rv = self.app.get('/v1/integrations/amounts')
        assert rv.status_code == 200

        data = json.loads(rv.data.decode('utf8'))
        for f in data:
            if f['fund_slug'] == 'millfield-house-foundation-main-fund':
                assert len(f['amounts']) == 12

    def test_durations(self):
        rv = self.app.get('/v1/integrations/durations')
        assert rv.status_code == 401

        rv = self.login("test@example.com", 'test')
        assert b'Logged in successfully' in rv.data

        rv = self.app.get('/v1/integrations/durations')
        assert rv.status_code == 200

        data = json.loads(rv.data.decode('utf8'))
        print(data)
        for f in data:
            if f['fund_slug'] == 'joseph-rowntree-charitable-trust-power-and-accountability':
                assert len(f['durations']) == 5
