"""Tests the auth module."""

from unittest import TestCase, main

import auth

usernames_valid = (
	"test",
	"Test",
	"definitely valid",
	"val_id",
	)

usernames_invalid = (
	r"..\..",
	r"\/\/\/\/\/\/\/",
	"?????????",
	)

class TestUsernameValidity(TestCase):
	def test_valid_usernames(self):
		for username in usernames_valid:
			self.assertTrue(auth.validate_username(username))

	def test_invalid_usernames(self):
		for username in usernames_invalid:
			self.assertFalse(auth.validate_username(username))

if __name__ == "__main__":
	main()
