"""Tests the auth module."""

from typing import Generator
from unittest import TestCase, main
from unittest.mock import MagicMock

import file_handler

file_handler.Path = MagicMock()
file_handler.FileHandler.UPLOAD_DIRECTORY = MagicMock()


class TestFileHandlingWithPublic(TestCase):
    def setUp(self) -> None:
        file_handler.FileHandler.PUBLIC_DIRECTORY = MagicMock()

    def test_file_list(self):
        test_file_handler = file_handler.FileHandler("")
        self.assertIsInstance(test_file_handler.list_files(), Generator)
        self.assertEqual(len(list(test_file_handler.list_files())), 1)

    def tearDown(self) -> None:
        file_handler.FileHandler.PUBLIC_DIRECTORY = None

class TestFileHandlingWithOutPublic(TestCase):
    def setUp(self) -> None:
        file_handler.FileHandler.PUBLIC_DIRECTORY = None

    def test_file_list(self):
        test_file_handler = file_handler.FileHandler("")
        self.assertIsInstance(test_file_handler.list_files(), Generator)
        self.assertEqual(len(list(test_file_handler.list_files())), 0)

if __name__ == "__main__":
    main()
