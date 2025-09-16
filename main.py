# main.py
from security import hash_password, verify_password
import os

HASH_FILE = "password.hash"

def save_hash(hash_bytes: bytes):
    with open(HASH_FILE, "wb") as f:
        f.write(hash_bytes)

def load_hash() -> bytes:
    if not os.path.exists(HASH_FILE):
        return None
    with open(HASH_FILE, "rb") as f:
        return f.read()

if __name__ == "__main__":
    stored_hash = load_hash()

    if stored_hash is None:
        password = input("Insérer mot de passe ")
        hashed = hash_password(password)
        save_hash(hashed)
        print("Password saved.")
    else:
        attempt = input("Entrer  mot de passe : ")
        if verify_password(stored_hash, attempt):
            print("Correct password.")
        else:
            print("Incorrect password.")

