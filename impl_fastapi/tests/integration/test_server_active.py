"""Tests whether the app starts up and can respond."""

from unittest import TestCase, main

from fastapi.testclient import TestClient

from impl_fastapi.main import app

class TestServer(TestCase):
    def setUp(self):
        self.test_app: TestClient = TestClient(app)

    def test_server_start(self):
        self.assertIsNotNone(self.test_app.get("/"))

    def tearDown(self):
        self.test_app.close()

if __name__ == "__main__":
    main()
