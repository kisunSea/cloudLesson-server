"""
common salt: settings.SECRET_KEY

support:
    * PKCS #5: use HMAC
"""
from django.conf.global_settings import SECRET_KEY
import hashlib
import binascii


def sha256(data):
    b_data = bytes(data, encoding='utf-8')
    salt = bytes(SECRET_KEY, encoding='utf-8')
    dk = hashlib.pbkdf2_hmac('sha256', b_data, salt, 100000)
    return str(binascii.hexlify(dk), encoding='utf-8')


if __name__ == '__main__':
    print(sha256('123'))
    print(sha256('123'))
    print(sha256('123'))
    # print(sha256(bytes('123', encoding='utf-8')))
    # print(sha256(bytes('123', encoding='utf-8')))
