from test_beehivedata import BeehivedataTestCase
import json


class InsightTestCase(BeehivedataTestCase):

    def test_beneficiaries(self):
        data = {
            "data": {
                'crime': 1
            }
        }
        rv = self.app.post('/insight/beneficiaries',
                           data=json.dumps(data),
                           content_type='application/json'
                           )
        assert rv.status_code == 401

        rv = self.login("test@example.com", 'test')
        assert b'Logged in successfully' in rv.data

        rv = self.app.post('/insight/beneficiaries',
                           data=json.dumps(data),
                           content_type='application/json'
                           )
        assert rv.status_code == 200
        data = json.loads(rv.data.decode('utf8'))
        assert data['joseph-rowntree-charitable-trust-cross-cutting'] > 0

    def test_amounts(self):
        data = {"data": {'amount': 6000}}
        rv = self.app.post('/insight/amounts',
                           data=json.dumps(data),
                           content_type='application/json'
                           )
        assert rv.status_code == 401

        rv = self.login("test@example.com", 'test')
        assert b'Logged in successfully' in rv.data

        rv = self.app.post('/insight/amounts',
                           data=json.dumps(data),
                           content_type='application/json'
                           )
        assert rv.status_code == 200
        data = json.loads(rv.data.decode('utf8'))
        assert data['joseph-rowntree-charitable-trust-sustainable-future'] > 0

    def test_duration(self):
        data = {"data": {'duration': 24}}
        rv = self.app.post('/insight/durations',
                           data=json.dumps(data),
                           content_type='application/json'
                           )
        assert rv.status_code == 401

        rv = self.login("test@example.com", 'test')
        assert b'Logged in successfully' in rv.data

        rv = self.app.post('/insight/durations',
                           data=json.dumps(data),
                           content_type='application/json'
                           )
        assert rv.status_code == 200
        data = json.loads(rv.data.decode('utf8'))
        assert data['joseph-rowntree-charitable-trust-northern-ireland'] > 0

    def test_insight_all(self):
        data = {"data": {
            'duration': 24,
            'amount': 6000,
            'beneficiaries': {"crime": 1}
        }}
        rv = self.app.post('/insight/all',
                           data=json.dumps(data),
                           content_type='application/json'
                           )
        assert rv.status_code == 401

        rv = self.login("test@example.com", 'test')
        assert b'Logged in successfully' in rv.data

        rv = self.app.post('/insight/all',
                           data=json.dumps(data),
                           content_type='application/json'
                           )
        assert rv.status_code == 200
        data = json.loads(rv.data.decode('utf8'))
        assert data['joseph-rowntree-charitable-trust-sustainable-future']["amounts"] > 0
        assert data['joseph-rowntree-charitable-trust-northern-ireland']["durations"] > 0
        assert data['joseph-rowntree-charitable-trust-cross-cutting']["beneficiaries"] > 0
