"""Tests the auth module."""

from unittest import TestCase, main

import auth

usernames_valid = (
	"test",
	"Test",
	"an unusual username",
	"val_id",
	r"this%should&work"
	)

usernames_invalid = (
	r"&&||",
	r"\/\/\/\/\/\/\/",
	"?????????",
	"not:valid",
	"some*times",
	"this_is_way_too_long_to_be_a_username"
	)

class TestUsernameValidity(TestCase):
	def test_valid_usernames(self):
		for username in usernames_valid:
			with self.subTest(msg=f"Username: {username}"):
				self.assertTrue(auth.validate_username(username))

	def test_invalid_usernames(self):
		for username in usernames_invalid:
			with self.subTest(msg=f"Username: {username}"):
				self.assertFalse(auth.validate_username(username))

if __name__ == "__main__":
	main()
