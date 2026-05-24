import os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from app.config import settings

def get_master_key() -> bytes:
    return bytes.fromhex(settings.VAULT_MASTER_KEY)

def encrypt_secret(plaintext: str) -> tuple[str, str]:
    key = get_master_key()
    iv  = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(iv, plaintext.encode(), None)
    return (base64.b64encode(ciphertext).decode(), base64.b64encode(iv).decode())

def decrypt_secret(ciphertext_b64: str, iv_b64: str) -> str:
    key = get_master_key()
    iv  = base64.b64decode(iv_b64)
    ct  = base64.b64decode(ciphertext_b64)
    aesgcm = AESGCM(key)
    return aesgcm.decrypt(iv, ct, None).decode()
