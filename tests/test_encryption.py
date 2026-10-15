import os

from backend.security.encryption import decrypt_text, encrypt_text, label_digest, reencrypt_text


KEY_A = "key-a:AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
KEY_B = "key-b:AQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQE"


def test_aes_gcm_round_trip_and_rotation(monkeypatch):
    monkeypatch.setenv("SINOPIA_ENV", "production")
    monkeypatch.setenv("SINOPIA_ENCRYPTION_KEYS", KEY_A)
    encrypted = encrypt_text("athlete-code-01")
    assert encrypted != "athlete-code-01"
    assert decrypt_text(encrypted) == "athlete-code-01"

    monkeypatch.setenv("SINOPIA_ENCRYPTION_KEYS", KEY_B + "," + KEY_A)
    rotated = reencrypt_text(encrypted)
    assert rotated != encrypted
    assert rotated.startswith("enc:v1:key-b:")
    assert decrypt_text(rotated) == "athlete-code-01"
    assert label_digest(" Athlete 01 ") == label_digest("athlete 01")


def test_plaintext_legacy_values_are_encrypted_during_rotation(monkeypatch):
    monkeypatch.setenv("SINOPIA_ENV", "production")
    monkeypatch.setenv("SINOPIA_ENCRYPTION_KEYS", KEY_B + "," + KEY_A)
    rotated = reencrypt_text("legacy-label")
    assert rotated.startswith("enc:v1:key-b:")
    assert decrypt_text(rotated) == "legacy-label"
