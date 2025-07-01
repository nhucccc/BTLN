import json
import base64
from crypto_utils import decrypt_aes_key, decrypt_file_aes, hash_integrity, load_key

# Load server private key
server_private = load_key("keys/server_private.pem")

# Load JSON
with open("secure_sensor_package.json", "r") as f:
    data = json.load(f)

# Parse metadata để lấy tên file
metadata_str = data["metadata"]
file_name = metadata_str.split("|")[0]

print(">> File original name:", file_name)

# Decode các trường
nonce = base64.b64decode(data["nonce"])
cipher = base64.b64decode(data["cipher"])
tag = base64.b64decode(data["tag"])
enc_key = base64.b64decode(data["key"])

# Giải mã AES key
aes_key = decrypt_aes_key(enc_key, server_private)

# Check hash
if hash_integrity(nonce, cipher, tag) != data["hash"]:
    print(" Hash mismatch! Dữ liệu có thể bị chỉnh sửa!")
else:
    # Giải mã dữ liệu
    plain = decrypt_file_aes(nonce, cipher, tag, aes_key)

    # Lưu lại file gốc với đúng tên
    with open(f"recovered_{file_name}", "wb") as f:
        f.write(plain)

    print(f"✅ File recovered successfully as recovered_{file_name}")
