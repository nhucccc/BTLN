import socket, json, base64, time
from crypto_utils import *

server_private = load_key("keys/server_private.pem")
client_public = load_key("keys/rsa_public.pem")

def send_json(conn, data): conn.sendall(json.dumps(data).encode())
def recv_json(conn): return json.loads(conn.recv(100000).decode())

def log(msg):
    with open("transaction_log.txt", "a") as f:
        f.write(f"[{time.ctime()}] {msg}\n")

s = socket.socket(); s.bind(('localhost', 9999)); s.listen(1)
print("Server listening on port 9999...")

while True:
    conn, _ = s.accept()
    first = conn.recv(1024).decode()

    if first == "Hello!":
        conn.send(b"Ready!")
        data = recv_json(conn)

        key = decrypt_aes_key(base64.b64decode(data["key"]), server_private)
        nonce = base64.b64decode(data["nonce"])
        cipher = base64.b64decode(data["cipher"])
        tag = base64.b64decode(data["tag"])
        if hash_integrity(nonce, cipher, tag) != data["hash"]:
            conn.send(b"NACK - Hash Fail"); continue

        if not verify_signature(data["metadata"], data["sig"], client_public):
            conn.send(b"NACK - Signature Fail"); continue

        try:
            plain = decrypt_file_aes(nonce, cipher, tag, key)
            with open("uploaded_sensor_data.txt", "wb") as f:
                f.write(plain)
            log("UPLOAD OK")
            conn.send(b"ACK")
        except:
            conn.send(b"NACK - Decryption Fail")
    elif first == "DOWNLOAD":
        req = recv_json(conn)
        if not verify_signature(req["req"], req["sig"], client_public):
            send_json(conn, {"status": "NACK - Signature Fail"}); continue

        with open("uploaded_sensor_data.txt", "rb") as f:
            filedata = f.read()
        aes_key = get_random_bytes(32)
        enc_key = encrypt_aes_key(aes_key, client_public)
        nonce, cipher, tag = encrypt_file_aes("uploaded_sensor_data.txt", aes_key)
        metadata = "sensor_data_download|" + str(int(time.time()))
        sig = sign_metadata(metadata, server_private)

        send_json(conn, {
            "status": "OK",
            "nonce": base64.b64encode(nonce).decode(),
            "cipher": base64.b64encode(cipher).decode(),
            "tag": base64.b64encode(tag).decode(),
            "hash": hash_integrity(nonce, cipher, tag),
            "sig": sig,
            "metadata": metadata,
            "key": base64.b64encode(enc_key).decode()
        })
        ack = conn.recv(1024)
        if ack == b"ACK":
            log("DOWNLOAD OK")
