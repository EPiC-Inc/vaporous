"""Tests whether the app starts up and can respond."""

from unittest import TestCase, main

from fastapi.responses import Response
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient

try:
    from impl_fastapi.main import app
except:
    from main import app

ACCESSIBLE_WHEN_LOGGED_OUT: tuple[list[str, str]] = (["/", "/login"], ["/login", "/login"])
PREPEND_URL = "http://testserver"

class TestServer(TestCase):
    def setUp(self):
        self.test_app: TestClient = TestClient(app)

    def test_server_start(self):
        self.assertIsNotNone(self.test_app.app_state)

    def test_server_pages_logged_out(self):
        for page, redirect_to in ACCESSIBLE_WHEN_LOGGED_OUT:
            with self.subTest(msg=f"Page: {page}"):
                response = self.test_app.get(page)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(str(response.url), f"{PREPEND_URL}{redirect_to}")

    def tearDown(self):
        self.test_app.close()


if __name__ == "__main__":
    main()
