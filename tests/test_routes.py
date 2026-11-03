import os
import tempfile
import unittest
from app import create_app
from app.db import get_db
from app.routes import auth_with_password, sha1


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = create_app({'TESTING': True, 'DATABASE': os.path.join(self.tmp.name, 'test.db')})
        self.client = self.app.test_client()
        self.password = 'TestFixtureOnly'
        self.signup('alice')

    def tearDown(self):
        self.tmp.cleanup()

    def signup(self, name):
        return self.client.post('/Signup', data={
            'username': name, 'email': name + '@example.test',
            'password': self.password, 'confirm_password': self.password,
        })

    def create_swap(self, alias='hello', content='Hello\n中文 Swap'):
        return self.client.post('/alice/addSwap', data={
            'password': self.password, 'alias': alias, 'content': content,
        })

    def update_swap(self, **overrides):
        data = dict(password=self.password, swap_id='1', alias='hello', last_alias='hello', content='Updated')
        data.update(overrides)
        return self.client.post('/alice/updateSwap', data=data)

    def test_signup_and_duplicate(self):
        self.assertEqual(self.client.get('/alice').status_code, 200)
        self.assertIn(b'username have been taken', self.signup('ALICE').data)

    def test_create_read_and_strip(self):
        self.assertEqual(self.create_swap().status_code, 302)
        self.assertIn('中文 Swap', self.client.get('/alice/hello').text)
        response = self.client.get('/alice/hello?strip=true')
        self.assertEqual(response.text, 'Hello\n中文 Swap')
        self.assertEqual(response.mimetype, 'text/plain')

    def test_empty_create_displays_error(self):
        response = self.create_swap(content='')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'content cannot be empty', response.data)

    def test_wrong_update_password_displays_error_without_mutation(self):
        self.create_swap()
        response = self.update_swap(password='wrong')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'wrong password', response.data)
        self.assertEqual(self.client.get('/alice/hello?strip=true').text, 'Hello\n中文 Swap')

    def test_bad_pagination_and_bounds(self):
        for query in ('offset=invalid', 'limit=invalid', 'offset=-1&limit=-1', 'limit=999999'):
            self.assertEqual(self.client.get('/alice?' + query).status_code, 200)

    def test_update_own_swap(self):
        self.create_swap()
        self.assertEqual(self.update_swap().status_code, 302)
        self.assertEqual(self.client.get('/alice/hello?strip=true').text, 'Updated')

    def test_other_user_cannot_update_or_read_numeric_swap(self):
        self.create_swap()
        self.signup('bob')
        response = self.client.post('/bob/updateSwap', data={
            'password': self.password, 'swap_id': '1', 'alias': 'hello',
            'last_alias': 'hello', 'content': 'Changed by Bob',
        })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(self.client.get('/bob/1').status_code, 404)
        self.assertEqual(self.client.get('/alice/hello?strip=true').text, 'Hello\n中文 Swap')

    def test_invalid_swap_id(self):
        for value in ('not-an-id', '', '999'):
            self.assertEqual(self.update_swap(swap_id=value).status_code, 404)

    def test_alias_validation_uses_stored_alias(self):
        self.create_swap()
        self.create_swap(alias='taken')
        response = self.update_swap(alias='taken', last_alias='taken')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'alias have been taken', response.data)

    def test_no_universal_password(self):
        response = self.client.post('/alice/addSwap', data={
            'password': 'superweakdancer', 'alias': 'blocked', 'content': 'Not saved',
        })
        self.assertIn(b'wrong password', response.data)
        self.assertEqual(self.client.get('/alice/blocked?strip=true').text, '')

    def test_password_hashes_are_salted(self):
        self.signup('bob')
        with self.app.app_context():
            hashes = [row['password'] for row in get_db().execute('SELECT password FROM think_user')]
        self.assertEqual(len(set(hashes)), 2)
        self.assertTrue(all(len(value) > 40 for value in hashes))

    def test_existing_sha1_account_upgrades(self):
        with self.app.app_context():
            db = get_db()
            db.execute('UPDATE think_user SET password = ? WHERE username = ?', (sha1(self.password), 'alice'))
            db.commit()
            user = db.execute('SELECT * FROM think_user WHERE username = ?', ('alice',)).fetchone()
            self.assertFalse(auth_with_password(user, 'wrong'))
            self.assertTrue(auth_with_password(user, self.password))
            stored = db.execute('SELECT password FROM think_user WHERE username = ?', ('alice',)).fetchone()['password']
            self.assertGreater(len(stored), 40)

    def test_html_is_text_and_links_are_safe(self):
        content = '<script>alert(1)</script> https://example.test/?a=1&b=2'
        self.create_swap(content=content)
        response = self.client.get('/alice/hello')
        self.assertNotIn('<script>alert(1)</script>', response.text)
        self.assertIn('&lt;script&gt;alert(1)&lt;/script&gt;', response.text)
        self.assertIn('rel="noopener noreferrer"', response.text)
        self.assertEqual(self.client.get('/alice/hello?strip=true').text, content)

    def test_blank_password_is_rejected(self):
        response = self.client.post('/Signup', data={
            'username': 'blank', 'email': 'blank@example.test',
            'password': '', 'confirm_password': '',
        })
        self.assertIn(b'password cannot be empty', response.data)
        self.assertEqual(self.client.get('/blank').status_code, 404)


if __name__ == '__main__':
    unittest.main()
