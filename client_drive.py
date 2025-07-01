import base64, time
from crypto_utils import *
from drive_utils import *

client_private = load_key("keys/rsa_private.pem")
client_public = load_key("keys/rsa_public.pem")
server_public = load_key("keys/server_public.pem")
server_private = load_key("keys/server_private.pem")  


def upload_to_cloud():
    aes_key = get_random_bytes(32)
    enc_key = encrypt_aes_key(aes_key, server_public)

    metadata = f"sensor_data.txt|{int(time.time())}|temp"
    sig = sign_metadata(metadata, client_private)
    nonce, cipher, tag = encrypt_file_aes("sensor_data.txt", aes_key)
    hash_value = hash_integrity(nonce, cipher, tag)

    package = {
        "metadata": metadata,
        "sig": sig,
        "key": base64.b64encode(enc_key).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "cipher": base64.b64encode(cipher).decode(),
        "tag": base64.b64encode(tag).decode(),
        "hash": hash_value
    }

    service = get_service()
    upload_json(service, "secure_sensor_package.json", package)
    print(" Uploaded encrypted package to Google Drive.")

def download_from_cloud():
    service = get_service()
    data = download_json(service, "secure_sensor_package.json")
    if not data:
        print(" File not found on Drive"); return

    nonce = base64.b64decode(data["nonce"])
    cipher = base64.b64decode(data["cipher"])
    tag = base64.b64decode(data["tag"])
    enc_key = base64.b64decode(data["key"])

    if hash_integrity(nonce, cipher, tag) != data["hash"]:
        print(" Hash mismatch!"); return

    # kiểm tra chữ ký bằng client_public (client là người ký)
    if not verify_signature(data["metadata"], data["sig"], client_public):
        print(" Signature mismatch!"); return

    aes_key = decrypt_aes_key(enc_key, server_private)  
    plain = decrypt_file_aes(nonce, cipher, tag, aes_key)
    with open("downloaded_sensor_data.txt", "wb") as f:
        f.write(plain)

    print(" File downloaded and verified successfully.")

if __name__ == "__main__":
    upload_to_cloud()
    download_from_cloud()
