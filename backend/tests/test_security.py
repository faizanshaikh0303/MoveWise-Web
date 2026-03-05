"""
Unit tests for app/core/security.py:
  - verify_password
  - get_password_hash
  - create_access_token
  - decode_access_token
"""
from datetime import timedelta

import pytest
from jose import jwt

from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
)
from app.core.config import settings


# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = get_password_hash("mysecret")
        assert hashed != "mysecret"

    def test_hash_starts_with_bcrypt_prefix(self):
        hashed = get_password_hash("mysecret")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_two_hashes_of_same_password_differ(self):
        """bcrypt uses a random salt each time."""
        h1 = get_password_hash("samepassword")
        h2 = get_password_hash("samepassword")
        assert h1 != h2

    def test_hash_length_is_reasonable(self):
        hashed = get_password_hash("short")
        assert len(hashed) >= 50


# ---------------------------------------------------------------------------
# verify_password
# ---------------------------------------------------------------------------

class TestVerifyPassword:
    def test_correct_password_returns_true(self):
        hashed = get_password_hash("correct_password")
        assert verify_password("correct_password", hashed) is True

    def test_wrong_password_returns_false(self):
        hashed = get_password_hash("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_empty_password_does_not_match_nonempty_hash(self):
        hashed = get_password_hash("notempty")
        assert verify_password("", hashed) is False

    def test_similar_but_different_password_returns_false(self):
        hashed = get_password_hash("Password123")
        assert verify_password("password123", hashed) is False  # case-sensitive


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------

class TestCreateAccessToken:
    def test_returns_non_empty_string(self):
        token = create_access_token(data={"sub": "user@example.com"})
        assert isinstance(token, str)
        assert len(token) > 20

    def test_token_contains_three_parts(self):
        """JWT format: header.payload.signature"""
        token = create_access_token(data={"sub": "user@example.com"})
        assert token.count(".") == 2

    def test_token_payload_contains_sub(self):
        token = create_access_token(data={"sub": "user@test.com"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["sub"] == "user@test.com"

    def test_token_payload_contains_exp(self):
        token = create_access_token(data={"sub": "user@test.com"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert "exp" in payload

    def test_custom_expiry_is_respected(self):
        short_token = create_access_token(
            data={"sub": "user@test.com"},
            expires_delta=timedelta(seconds=30),
        )
        long_token = create_access_token(
            data={"sub": "user@test.com"},
            expires_delta=timedelta(days=7),
        )
        short_payload = jwt.decode(short_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        long_payload = jwt.decode(long_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert short_payload["exp"] < long_payload["exp"]

    def test_additional_data_is_preserved(self):
        token = create_access_token(data={"sub": "user@test.com", "role": "admin"})
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert payload["role"] == "admin"


# ---------------------------------------------------------------------------
# decode_access_token
# ---------------------------------------------------------------------------

class TestDecodeAccessToken:
    def test_valid_token_returns_payload_dict(self):
        token = create_access_token(data={"sub": "user@example.com"})
        payload = decode_access_token(token)
        assert isinstance(payload, dict)
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
        expired_token = create_access_token(
            data={"sub": "user@example.com"},
            expires_delta=timedelta(seconds=-1),
        )
        assert decode_access_token(expired_token) is None

    def test_token_signed_with_different_key_returns_none(self):
        other_key = "completely-different-secret-key-xyz-123456"
        token = jwt.encode(
            {"sub": "user@example.com"},
            other_key,
            algorithm=settings.ALGORITHM,
        )
        assert decode_access_token(token) is None
