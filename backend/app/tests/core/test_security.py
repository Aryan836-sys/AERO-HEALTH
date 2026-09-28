import time

import pytest

from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_hash_password_is_not_the_plaintext():
    hashed = hash_password("correct horse battery staple")
    assert hashed != "correct horse battery staple"


def test_verify_password_accepts_the_right_password():
    hashed = hash_password("correct horse battery staple")
    assert verify_password("correct horse battery staple", hashed) is True


def test_verify_password_rejects_the_wrong_password():
    hashed = hash_password("correct horse battery staple")
    assert verify_password("wrong password", hashed) is False


def test_access_token_round_trips_to_the_same_user_id():
    token = create_access_token(user_id=42)
    assert decode_token(token, expected_type="access") == 42


def test_refresh_token_round_trips_to_the_same_user_id():
    token = create_refresh_token(user_id=42)
    assert decode_token(token, expected_type="refresh") == 42


def test_access_token_rejected_as_refresh_token():
    token = create_access_token(user_id=42)
    with pytest.raises(TokenError):
        decode_token(token, expected_type="refresh")


def test_garbage_token_raises_token_error_not_a_raw_jose_exception():
    with pytest.raises(TokenError):
        decode_token("not.a.real.token", expected_type="access")


def test_tampered_token_is_rejected():
    token = create_access_token(user_id=42)
    tampered = token[:-4] + "abcd"
    with pytest.raises(TokenError):
        decode_token(tampered, expected_type="access")


def test_password_over_72_bytes_raises_a_clear_error():
    too_long = "x" * 100
    with pytest.raises(ValueError):
        hash_password(too_long)
