import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
import base64
from crypto_utils import *
from drive_utils import *
import socket
import json
import time

client_private = load_key("keys/rsa_private.pem")
client_public = load_key("keys/rsa_public.pem")
server_public = load_key("keys/server_public.pem")
server_private = load_key("keys/server_private.pem")

DRIVE_FILENAME = "secure_sensor_package.json"

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Secure Sensor File Transfer")
        self.root.geometry("700x600")
        self.root.configure(bg="#c9eed9")

        style = ttk.Style()
        style.theme_use("clam")

        # Đổi màu background và nút
        style.configure("TButton",
                        font=("Segoe UI", 10, "bold"),
                        padding=6,
                        background="#3735d7",
                        foreground="white")
        style.map("TButton",
                  background=[('active', "#3653aa")])

        style.configure("TLabel", background="#40d2d2", font=("Segoe UI", 10))

        # File path
        frame_top = ttk.Frame(root)
        frame_top.pack(padx=20, pady=10, fill="x")

        self.filepath_var = tk.StringVar()
        ttk.Entry(frame_top, textvariable=self.filepath_var, width=60).pack(side="left", padx=(0, 10))
        ttk.Button(frame_top, text="Browse...", command=self.browse_file).pack(side="left")

        # Button Grid
        frame_btn = ttk.Frame(root)
        frame_btn.pack(padx=20, pady=10, fill="x")

        ttk.Button(frame_btn, text="Upload to Drive", command=self.upload_drive).grid(row=0, column=0, padx=5, pady=5, sticky="we")
        ttk.Button(frame_btn, text="Upload to Server", command=self.upload_server).grid(row=0, column=1, padx=5, pady=5, sticky="we")
        ttk.Button(frame_btn, text="Download from Drive", command=self.download_drive).grid(row=1, column=0, padx=5, pady=5, sticky="we")
        ttk.Button(frame_btn, text="Download from Server", command=self.download_server).grid(row=1, column=1, padx=5, pady=5, sticky="we")
        ttk.Button(root, text="Delete file on Drive", command=self.delete_drive_file).pack(padx=20, pady=10, fill="x")

        # Logs
        ttk.Label(root, text="Logs:").pack(anchor="w", padx=20)
        self.log_area = scrolledtext.ScrolledText(root, height=10, font=("Consolas", 10))
        self.log_area.pack(padx=20, pady=5, fill="both", expand=True)

        # File content
        ttk.Label(root, text="Downloaded file content:").pack(anchor="w", padx=20, pady=(10,0))
        self.content_area = scrolledtext.ScrolledText(root, height=10, font=("Consolas", 10))
        self.content_area.pack(padx=20, pady=5, fill="both", expand=True)

    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.filepath_var.set(path)

    def log(self, text):
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.see(tk.END)

    def upload_drive(self):
        path = self.filepath_var.get()
        if not os.path.exists(path):
            messagebox.showerror("Error", "File does not exist!")
            return

        aes_key = get_random_bytes(32)
        enc_key = encrypt_aes_key(aes_key, server_public)

        metadata = f"{os.path.basename(path)}|{int(time.time())}|temp"
        sig = sign_metadata(metadata, client_private)
        nonce, cipher, tag = encrypt_file_aes(path, aes_key)
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
        upload_json(service, DRIVE_FILENAME, package)
        self.log(f"Uploaded {path} to Google Drive.")

    def download_drive(self):
        service = get_service()
        data = download_json(service, DRIVE_FILENAME)
        if not data:
            self.log("No file found on Drive.")
            return

        nonce = base64.b64decode(data["nonce"])
        cipher = base64.b64decode(data["cipher"])
        tag = base64.b64decode(data["tag"])
        enc_key = base64.b64decode(data["key"])

        if hash_integrity(nonce, cipher, tag) != data["hash"]:
            self.log("Hash mismatch!")
            return

        if not verify_signature(data["metadata"], data["sig"], client_public):
            self.log("Signature mismatch!")
            return

        aes_key = decrypt_aes_key(enc_key, server_private)
        plain = decrypt_file_aes(nonce, cipher, tag, aes_key)
        with open("downloaded_sensor_data.txt", "wb") as f:
            f.write(plain)

        self.log("Downloaded and decrypted file from Drive.")
        self.content_area.delete(1.0, tk.END)
        self.content_area.insert(tk.END, plain.decode(errors="ignore"))

    def delete_drive_file(self):
        service = get_service()
        files = service.files().list(q=f"name='{DRIVE_FILENAME}'", fields="files(id, name)").execute().get("files", [])
        if not files:
            self.log("File not found on Drive.")
            return
        file_id = files[0]['id']
        service.files().delete(fileId=file_id).execute()
        self.log(f"Deleted {DRIVE_FILENAME} from Drive.")

    def upload_server(self):
        path = self.filepath_var.get()
        if not os.path.exists(path):
            messagebox.showerror("Error", "File does not exist!")
            return

        aes_key = get_random_bytes(32)
        enc_key = encrypt_aes_key(aes_key, server_public)

        metadata = f"{os.path.basename(path)}|{int(time.time())}|temp"
        sig = sign_metadata(metadata, client_private)
        nonce, cipher, tag = encrypt_file_aes(path, aes_key)
        hash_value = hash_integrity(nonce, cipher, tag)

        payload = {
            "metadata": metadata,
            "sig": sig,
            "key": base64.b64encode(enc_key).decode(),
            "nonce": base64.b64encode(nonce).decode(),
            "cipher": base64.b64encode(cipher).decode(),
            "tag": base64.b64encode(tag).decode(),
            "hash": hash_value
        }

        s = socket.socket()
        s.connect(('localhost', 9999))
        s.send(b"Hello!")
        ack = s.recv(1024)
        if ack != b"Ready!":
            self.log("Server not ready.")
            return
        s.send(json.dumps(payload).encode())
        result = s.recv(1024).decode()
        self.log("Server response: " + result)
        s.close()

    def download_server(self):
        s = socket.socket()
        s.connect(('localhost', 9999))
        s.send(b"DOWNLOAD")

        req_text = "download_request|" + str(int(time.time()))
        sig = sign_metadata(req_text, client_private)
        s.send(json.dumps({"req": req_text, "sig": sig}).encode())
        data = json.loads(s.recv(100000).decode())

        if data["status"] != "OK":
            self.log("Server NACK: " + data["status"])
            s.close()
            return

        nonce = base64.b64decode(data["nonce"])
        cipher = base64.b64decode(data["cipher"])
        tag = base64.b64decode(data["tag"])
        enc_key = base64.b64decode(data["key"])

        if hash_integrity(nonce, cipher, tag) != data["hash"]:
            self.log("Hash mismatch.")
            s.close()
            return

        if not verify_signature(data["metadata"], data["sig"], server_public):
            self.log("Signature mismatch.")
            s.close()
            return

        aes_key = decrypt_aes_key(enc_key, client_private)
        plain = decrypt_file_aes(nonce, cipher, tag, aes_key)

        with open("downloaded_sensor_data.txt", "wb") as f:
            f.write(plain)

        s.send(b"ACK")
        self.log("Downloaded and decrypted file from server.")
        self.content_area.delete(1.0, tk.END)
        self.content_area.insert(tk.END, plain.decode(errors="ignore"))
        s.close()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
