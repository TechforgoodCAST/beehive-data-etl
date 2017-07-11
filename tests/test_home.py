from test_beehivedata import BeehivedataTestCase


class HomeTestCase(BeehivedataTestCase):

    def test_home(self):
        rv = self.app.get('/')
        assert b'High quality data about charitable funding' in rv.data

    def test_login(self):
        rv = self.login("test@example.com", 'test')
        assert b'Logged in successfully' in rv.data

    def test_login_wrong_email(self):
        rv = self.login("wrongemail@example.com", 'test')
        assert b'Wrong username or password' in rv.data

    def test_login_wrong_password(self):
        rv = self.login("test@example.com", 'wrongpassword')
        assert b'Wrong username or password' in rv.data

    def test_status(self):
        rv = self.app.get('/status')
        assert rv.status_code == 401

        rv = self.login("test@example.com", 'test')
        assert b'Logged in successfully' in rv.data

        rv = self.app.get('/status')
        assert rv.status_code == 200
