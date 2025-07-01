from Crypto.PublicKey import RSA
import os

def save_key(key, filepath):
    with open(filepath, 'wb') as f:
        f.write(key.export_key())

def generate_key_pair(name):
    key = RSA.generate(1024)
    private_key_path = f"keys/{name}_private.pem"
    public_key_path = f"keys/{name}_public.pem"

    save_key(key, private_key_path)
    save_key(key.publickey(), public_key_path)

    print(f" {name.capitalize()} key pair created:")
    print(f"    - Private: {private_key_path}")
    print(f"    - Public : {public_key_path}")

if __name__ == "__main__":
    if not os.path.exists("keys"):
        os.makedirs("keys")

    generate_key_pair("rsa")       # Client
    generate_key_pair("server")    # Server
