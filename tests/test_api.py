from test_beehivedata import BeehivedataTestCase
import json


class ApiTestCase(BeehivedataTestCase):

    def test_charity(self):
        rv = self.app.get('/v1/charity/1122057')
        data = json.loads(rv.data.decode('utf8'))
        assert len(data) == 1
        assert data[0]["recipientOrganization"][0]["charityNumber"] == "1122057"

    def test_charity_html(self):
        rv = self.app.get('/v1/charity/1122057.html')

        assert b'Action on Armed Violence' in rv.data

    def test_grant(self):
        rv = self.app.get('/v1/grant/360G-JRCT-9733')
        data = json.loads(rv.data.decode('utf8'))
        assert 'recipientOrganization' in data
        assert data['id'] == '360G-JRCT-9733'
        assert data['title'] == "Grant to Migrant Voice"

    def test_funders(self):
        rv = self.app.get('/v1/funders')
        data = json.loads(rv.data.decode('utf8'))
        assert len(data) == 2
        assert data[0]["funder_name"] == 'Millfield House Foundation'
        assert len(data[1]["funds"]) == 6
        assert data[0]["funds"][0]["count"] == 12

    def test_funders_html(self):
        rv = self.app.get('/v1/funders.html')

        assert b'Millfield House Foundation' in rv.data
        assert b'2 funders with data' in rv.data

    def test_funder(self):
        rv = self.app.get('/v1/funder/GB-CHC-210037')
        data = json.loads(rv.data.decode('utf8'))
        assert len(data) == 31
        assert data[0]["_id"] == '360G-JRCT-9682'
