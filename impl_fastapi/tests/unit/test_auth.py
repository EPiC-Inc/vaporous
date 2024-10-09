"""Tests the auth module."""

from unittest import TestCase, main

import auth

CLEARTEXT: str = "test2"
HASHES: tuple[str] = (
	"ce3a942627cba9d93454b36de08bb136$4096$8$4$1fbd8c44619fbe77c1605f102406b4a48de49d9f76137a72952fa2f0fe380652",
	"787011905edc4c1b4d613f3702833e6c$1024$8$4$66f0761eaa343e048472b1a92b88b5e377de60a3aff2405a870940bca6696a3a",
	"ec2afe592f73d6cdae2a28980e19a075$4096$8$4$9d8a6a09ca7543f1a1288a4891fdc3f2c70e82b74b5acd3780510fc2b0f35a255899affa5e15a47716c2fef5121688279a5c56c262ea75978dcd5a16fef2bf43",
	"1686db205d3c147461d7bf6f474253a6$4096$8$4$4ac6c6f6f76cb5ec35593248a45dcf48c8459a97a67cdc9132078048668cbd1f",
)

USERNAMES_VALID: tuple[str] = (
	"test",
	"Test",
	"an unusual username",
	"val_id",
	r"this%should&work"
)
USERNAMES_INVALID: tuple[str] = (
	r"&&||",
	r"/etc/passwd",
	"?????????",
	"not:valid",
	"not*valid",
	"this_is_way_too_long_to_be_a_username"
)

class TestUsernameValidity(TestCase):
	def test_valid_usernames(self):
		for username in USERNAMES_VALID:
			with self.subTest(msg=f"Username: {username}"):
				self.assertTrue(auth.validate_username(username))

	def test_invalid_usernames(self):
		for username in USERNAMES_INVALID:
			with self.subTest(msg=f"Username: {username}"):
				self.assertFalse(auth.validate_username(username))

	def test_password_hashing(self):
		for hash_ in HASHES:
			self.assertTrue(auth.checkpw(CLEARTEXT, hash_))

if __name__ == "__main__":
	main()
