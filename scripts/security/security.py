# security.py
import bcrypt

def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt)

def verify_password(stored_hash: bytes, password_attempt: str) -> bool:
    return bcrypt.checkpw(password_attempt.encode(), stored_hash)

