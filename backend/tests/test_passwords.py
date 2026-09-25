import unittest

from app.core.passwords import hash_password, verify_password


class PasswordTests(unittest.TestCase):
    def test_hash_is_salted_and_password_is_not_stored_verbatim(self):
        first_hash = hash_password("correct horse battery staple")
        second_hash = hash_password("correct horse battery staple")

        self.assertNotEqual(first_hash, "correct horse battery staple")
        self.assertNotEqual(first_hash, second_hash)
        self.assertEqual(
            verify_password("correct horse battery staple", first_hash),
            (True, None),
        )
        self.assertFalse(verify_password("incorrect password", first_hash)[0])

    def test_legacy_plaintext_password_returns_replacement_hash(self):
        valid, replacement_hash = verify_password("legacy-secret", "legacy-secret")

        self.assertTrue(valid)
        self.assertIsNotNone(replacement_hash)
        self.assertEqual(verify_password("legacy-secret", replacement_hash), (True, None))

    def test_rejects_oversized_password(self):
        self.assertFalse(verify_password("x" * 1025, hash_password("valid password"))[0])


if __name__ == "__main__":
    unittest.main()