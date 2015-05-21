'''
Functions to manage private/public keys encryption.
This module needs Crypto module.
'''

from Crypto.PublicKey import RSA
from base64 import b64decode

def generate_RSA(bits=2048):
  '''
  Generate an RSA keypair with an exponent of 65537 in PEM format
  param: bits The key length in bits
  Return private key and public key
  '''
  new_key = RSA.generate(bits)
  public_key = new_key.publickey().exportKey("PEM")
  private_key = new_key.exportKey("PEM")
  return private_key, public_key

def encrypt_RSA(public_key_loc, message):
  '''
  param: public_key_loc Path to public key
  param: message String to be encrypted
  return base64 encoded encrypted string
  '''
  key = open(public_key_loc, "r").read()
  rsakey = RSA.importKey(key)
  encrypted = rsakey.encrypt(message,None)[0]
  return encrypted.encode('base64')


def decrypt_RSA(private_key_loc, package):
  '''
  param: public_key_loc Path to your private key
  param: package String to be decrypted
  return decrypted string
  '''
  key = open(private_key_loc, "r").read()
  rsakey = RSA.importKey(key)
  decrypted = rsakey.decrypt(b64decode(package))
  return decrypted
