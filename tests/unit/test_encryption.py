from base64 import b64encode

from Crypto.Random import get_random_bytes
from django.test import TestCase
from api.igb.encryption import AESCypher


class EncryptionTestCase(TestCase):
    key = b64encode(get_random_bytes(16))

    def test_encryption_works(self):
        test_data = "this is a test string"
        encrypt_cipher = AESCypher(self.key)

        cipyhertext = encrypt_cipher.encrypt(test_data)

        decode_cipher = AESCypher(self.key)
        plain_text = decode_cipher.decrypt(cipyhertext)

        self.assertEqual(test_data, plain_text)
