"""
Functions to manage private/public keys encryption.
This module needs Crypto module.
"""

from base64 import b64decode, b64encode

import Crypto
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA

if [int(x) for x in Crypto.__version__.split(".")] < [2, 1]:
    # pyrypro <= 2.0.x is not suitable since it is missing needed functions
    # such as exportKey() and importKey()
    raise ImportError(
        "Crypto module (pycrypto) is too old for soma.crypt "
        "- please install pycryptodome"
    )


def generate_RSA(bits=2048):
    """
    Generate an RSA keypair with an exponent of 65537 in PEM format
    param: bits The key length in bits
    Return private key and public key
    """
    if [int(x) for x in Crypto.__version__.split(".")] < [2, 1]:
        import random

        def gen_func(n):
            return "".join([chr(random.randrange(0, 256, 1)) for i in range(n)])

        new_key = RSA.generate(bits, gen_func)
    else:
        new_key = RSA.generate(bits)
    public_key = new_key.publickey().exportKey("PEM")
    private_key = new_key.exportKey("PEM")
    return private_key, public_key


def encrypt_RSA(public_key_loc, message):
    """
    param: public_key_loc Path to public key
    param: message String to be encrypted
    return base64 encoded encrypted string
    """
    key = open(public_key_loc, "rb").read()
    rsakey = RSA.importKey(key)
    if not isinstance(message, bytes):
        message = message.encode()
    cipher = PKCS1_OAEP.new(rsakey)
    encrypted = cipher.encrypt(message)
    return b64encode(encrypted)


def decrypt_RSA(private_key_loc, package):
    """
    param: public_key_loc Path to your private key
    param: package String to be decrypted
    return decrypted string
    """
    key = open(private_key_loc, "rb").read()
    rsakey = RSA.importKey(key)
    cipher = PKCS1_OAEP.new(rsakey)
    decrypted = cipher.decrypt(b64decode(package))
    return decrypted
