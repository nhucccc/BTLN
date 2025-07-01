import socket, json, base64, time
from crypto_utils import *

client_private = load_key("keys/rsa_private.pem")
client_public = load_key("keys/rsa_public.pem")
server_public = load_key("keys/server_public.pem")

def send_json(sock, data): sock.sendall(json.dumps(data).encode())
def recv_json(sock): return json.loads(sock.recv(100000).decode())

def upload_file():
    s = socket.socket(); s.connect(('localhost', 9999))
    s.send(b"Hello!")
    if s.recv(1024).decode() != "Ready!": return

    aes_key = get_random_bytes(32)
    enc_key = encrypt_aes_key(aes_key, server_public)

    metadata = f"sensor_data.txt|{int(time.time())}|temperature"
    signature = sign_metadata(metadata, client_private)
    nonce, cipher, tag = encrypt_file_aes("sensor_data.txt", aes_key)
    integrity = hash_integrity(nonce, cipher, tag)

    send_json(s, {
        "key": base64.b64encode(enc_key).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "cipher": base64.b64encode(cipher).decode(),
        "tag": base64.b64encode(tag).decode(),
        "hash": integrity,
        "sig": signature,
        "metadata": metadata
    })

    ack = s.recv(1024).decode()
    print("Server response:", ack)
    s.close()

def download_file():
    s = socket.socket(); s.connect(('localhost', 9999))
    s.send(b"DOWNLOAD")
    metadata = f"download_request|{int(time.time())}"
    sig = sign_metadata(metadata, client_private)
    send_json(s, {"req": metadata, "sig": sig})

    data = recv_json(s)
    if data["status"] != "OK": print("Failed:", data["status"]); return

    nonce = base64.b64decode(data["nonce"])
    cipher = base64.b64decode(data["cipher"])
    tag = base64.b64decode(data["tag"])
    hash_check = hash_integrity(nonce, cipher, tag)
    if hash_check != data["hash"]:
        print("Integrity failed!"); return

    if not verify_signature(data["metadata"], data["sig"], server_public):
        print("Signature failed!"); return

    aes_key = decrypt_aes_key(base64.b64decode(data["key"]), client_private)
    plaintext = decrypt_file_aes(nonce, cipher, tag, aes_key)
    with open("downloaded_sensor_data.txt", "wb") as f:
        f.write(plaintext)
    print("File downloaded successfully.")
    s.send(b"ACK")
    s.close()

if __name__ == "__main__":
    upload_file()
    download_file()
