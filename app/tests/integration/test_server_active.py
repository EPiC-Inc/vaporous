"""Tests whether the app starts up and can respond."""

from urllib.parse import urlparse
from unittest import TestCase, main

from fastapi.testclient import TestClient

import config

config.CONFIG["database_uri"] = "sqlite+pysqlite:///:memory:"

from main import app


ACCESSIBLE_WHEN_LOGGED_OUT: tuple[tuple[str, str], ...] = (("/", "/login"), ("/login", "/login"))


class TestServer(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_app: TestClient = TestClient(app)

    def test_server_start(self):
        self.assertIsNotNone(self.test_app.app_state)

    def test_server_pages_logged_out(self):
        for page, redirect_to in ACCESSIBLE_WHEN_LOGGED_OUT:
            with self.subTest(msg=f"Page: {page}"):
                response = self.test_app.get(page)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(urlparse(str(response.url)).path, redirect_to)

    @classmethod
    def tearDownClass(cls):
        cls.test_app.close()


if __name__ == "__main__":
    main()
