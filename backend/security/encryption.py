"""Application-level encryption for athlete labels and pain-area values."""
import base64
import hashlib
import hmac
import os
import re
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

_PREFIX = "enc:v1:"
_KEY_ID = re.compile(r"^[A-Za-z0-9_-]{1,32}$")


def _keys() -> list[tuple[str, bytes]]:
    raw = os.environ.get("SINOPIA_ENCRYPTION_KEYS", "").strip()
    if not raw:
        if os.environ.get("SINOPIA_ENV", "production").lower() == "production":
            raise RuntimeError("SINOPIA_ENCRYPTION_KEYS is required in production.")
        return []
    parsed: list[tuple[str, bytes]] = []
    for item in raw.split(","):
        key_id, separator, encoded = item.strip().partition(":")
        if not separator or not _KEY_ID.fullmatch(key_id):
            raise RuntimeError("Invalid SINOPIA_ENCRYPTION_KEYS entry.")
        try:
            key = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
        except Exception as exc:
            raise RuntimeError("Invalid encoded encryption key.") from exc
        if len(key) != 32:
            raise RuntimeError("Each Sinopia encryption key must decode to exactly 32 bytes.")
        if any(existing_id == key_id for existing_id, _ in parsed):
            raise RuntimeError("Encryption key IDs must be unique.")
        parsed.append((key_id, key))
    return parsed


def validate_encryption_config() -> None:
    _keys()


def encrypt_text(value: str) -> str:
    keys = _keys()
    if not keys:
        return value
    key_id, key = keys[0]
    nonce = secrets.token_bytes(12)
    ciphertext = AESGCM(key).encrypt(nonce, value.encode("utf-8"), None)
    encode = lambda part: base64.urlsafe_b64encode(part).decode("ascii").rstrip("=")
    return _PREFIX + key_id + ":" + encode(nonce) + ":" + encode(ciphertext)


def decrypt_text(value: str | None) -> str | None:
    if value is None or not value.startswith(_PREFIX):
        return value
    parts = value[len(_PREFIX):].split(":")
    if len(parts) != 3:
        raise RuntimeError("Stored encrypted value has an invalid format.")
    key_id, encoded_nonce, encoded_ciphertext = parts
    key = next((key for current_id, key in _keys() if current_id == key_id), None)
    if key is None:
        raise RuntimeError("An encryption key required by stored data is missing.")
    decode = lambda part: base64.urlsafe_b64decode(part + "=" * (-len(part) % 4))
    try:
        plaintext = AESGCM(key).decrypt(
            decode(encoded_nonce), decode(encoded_ciphertext), None
        )
    except Exception as exc:
        raise RuntimeError("Stored encrypted value could not be decrypted.") from exc
    return plaintext.decode("utf-8")


def reencrypt_text(value: str | None) -> str | None:
    if value is None:
        return None
    plaintext = decrypt_text(value)
    keys = _keys()
    if not keys:
        return plaintext
    if value.startswith(_PREFIX + keys[0][0] + ":"):
        return value
    return encrypt_text(plaintext)


def label_digest(value: str) -> str:
    normalized = " ".join(value.split()).casefold()
    keys = _keys()
    if keys:
        return hmac.new(keys[0][1], normalized.encode("utf-8"), hashlib.sha256).hexdigest()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
