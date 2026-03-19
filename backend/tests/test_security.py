"""Unit tests for security helpers (no DB or HTTP required)."""
import time
import pytest
from datetime import timedelta
from jose import jwt

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)
from app.core.config import settings


class TestPasswordHashing:
    def test_hash_differs_from_plaintext(self):
        assert get_password_hash("secret") != "secret"

    def test_verify_correct_password(self):
        hashed = get_password_hash("correct")
        assert verify_password("correct", hashed) is True

    def test_verify_wrong_password(self):
        hashed = get_password_hash("correct")
        assert verify_password("wrong", hashed) is False

    def test_bcrypt_random_salt_produces_unique_hashes(self):
        h1 = get_password_hash("same")
        h2 = get_password_hash("same")
        assert h1 != h2

    def test_both_hashes_still_verify(self):
        h1 = get_password_hash("same")
        h2 = get_password_hash("same")
        assert verify_password("same", h1) is True
        assert verify_password("same", h2) is True

    def test_empty_password_hashes_and_verifies(self):
        hashed = get_password_hash("")
        assert verify_password("", hashed) is True

    def test_empty_password_fails_against_nonempty_hash(self):
        hashed = get_password_hash("notempty")
        assert verify_password("", hashed) is False

    def test_special_characters(self):
        pw = "p@$$w0rd!#%^&*()"
        hashed = get_password_hash(pw)
        assert verify_password(pw, hashed) is True


class TestCreateAccessToken:
    def test_returns_string(self):
        token = create_access_token(data={"sub": "user@example.com"})
        assert isinstance(token, str)

    def test_token_contains_subject(self):
        token = create_access_token(data={"sub": "user@example.com"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "user@example.com"

    def test_token_has_expiry_field(self):
        token = create_access_token(data={"sub": "user@example.com"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload

    def test_default_expiry_is_in_future(self):
        token = create_access_token(data={"sub": "user@example.com"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["exp"] > int(time.time())

    def test_custom_expiry_is_respected(self):
        delta = timedelta(seconds=10)
        token = create_access_token(data={"sub": "u"}, expires_delta=delta)
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        # Should expire within ~10 seconds from now
        assert payload["exp"] - int(time.time()) <= 11

    def test_extra_fields_are_preserved(self):
        token = create_access_token(data={"sub": "user@example.com", "role": "admin"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["role"] == "admin"


class TestDecodeAccessToken:
    def test_valid_token_returns_payload(self):
        token = create_access_token(data={"sub": "user@example.com"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "user@example.com"

    def test_invalid_token_returns_none(self):
        assert decode_access_token("totally.invalid.token") is None

    def test_empty_string_returns_none(self):
        assert decode_access_token("") is None

    def test_tampered_signature_returns_none(self):
        token = create_access_token(data={"sub": "user@example.com"})
        tampered = token[:-5] + "XXXXX"
        assert decode_access_token(tampered) is None

    def test_expired_token_returns_none(self):
        expired = create_access_token(
            data={"sub": "user@example.com"},
            expires_delta=timedelta(seconds=-1),
        )
        assert decode_access_token(expired) is None

    def test_token_signed_with_wrong_secret_returns_none(self):
        from datetime import datetime, timezone
        payload = {
            "sub": "user@example.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        bad_token = jwt.encode(payload, "wrong-secret-key", algorithm=settings.ALGORITHM)
        assert decode_access_token(bad_token) is None

    def test_token_with_wrong_algorithm_returns_none(self):
        from datetime import datetime, timezone
        payload = {
            "sub": "user@example.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        hs512_token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS512")
        assert decode_access_token(hs512_token) is None
