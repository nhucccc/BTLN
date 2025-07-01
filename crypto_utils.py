from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA512
from Crypto.Signature import pkcs1_15
from Crypto.Random import get_random_bytes
import base64

def load_key(path):
    with open(path, 'rb') as f:
        return RSA.import_key(f.read())

def sign_metadata(metadata_str, private_key):
    h = SHA512.new(metadata_str.encode())
    signature = pkcs1_15.new(private_key).sign(h)
    return base64.b64encode(signature).decode()

def verify_signature(metadata_str, signature_b64, public_key):
    h = SHA512.new(metadata_str.encode())
    try:
        pkcs1_15.new(public_key).verify(h, base64.b64decode(signature_b64))
        return True
    except:
        return False

def encrypt_file_aes(file_path, aes_key):
    with open(file_path, 'rb') as f:
        data = f.read()
    nonce = get_random_bytes(12)
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    cipher_data, tag = cipher.encrypt_and_digest(data)
    return nonce, cipher_data, tag

def decrypt_file_aes(nonce, cipher_data, tag, aes_key):
    cipher = AES.new(aes_key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(cipher_data, tag)

def hash_integrity(nonce, cipher_data, tag):
    h = SHA512.new(nonce + cipher_data + tag)
    return h.hexdigest()

def encrypt_aes_key(aes_key, rsa_pub):
    cipher_rsa = PKCS1_OAEP.new(rsa_pub)
    return cipher_rsa.encrypt(aes_key)

def decrypt_aes_key(encrypted_key, rsa_priv):
    cipher_rsa = PKCS1_OAEP.new(rsa_priv)
    return cipher_rsa.decrypt(encrypted_key)
