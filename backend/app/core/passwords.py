import base64
import hashlib
import hmac
import secrets


_SCRYPT_PREFIX = "scrypt"
_SCRYPT_N = 1 << 14
_SCRYPT_R = 8
_SCRYPT_P = 1
_DUMMY_HASH = "scrypt$16384$8$1$AAAAAAAAAAAAAAAAAAAAAA$AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"


def hash_password(password: str) -> str:
    if len(password) > 1024:
        raise ValueError("Password must be 1024 characters or fewer.")
    salt = secrets.token_bytes(16)
    derived_key = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=_SCRYPT_N,
        r=_SCRYPT_R,
        p=_SCRYPT_P,
        dklen=32,
    )
    encode = lambda value: base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")
    return f"{_SCRYPT_PREFIX}${_SCRYPT_N}${_SCRYPT_R}${_SCRYPT_P}${encode(salt)}${encode(derived_key)}"


def verify_password(password: str, stored_value: str | None) -> tuple[bool, str | None]:
    if len(password) > 1024:
        hashlib.scrypt(
            b"invalid-password",
            salt=b"0123456789abcdef",
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            dklen=32,
        )
        return False, None

    if stored_value is None or not stored_value.startswith(f"{_SCRYPT_PREFIX}$"):
        candidate_hash = hash_password(password)
        valid = stored_value is not None and hmac.compare_digest(password, stored_value)
        return valid, candidate_hash if valid else None

    try:
        prefix, n_value, r_value, p_value, salt_value, hash_value = stored_value.split("$")
        n, r, p = int(n_value), int(r_value), int(p_value)
        if prefix != _SCRYPT_PREFIX or (n, r, p) != (_SCRYPT_N, _SCRYPT_R, _SCRYPT_P):
            raise ValueError("Unsupported password hash parameters.")
        decode = lambda value: base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))
        salt = decode(salt_value)
        expected = decode(hash_value)
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False, None

    return hmac.compare_digest(actual, expected), None


def burn_password_check(password: str) -> None:
    verify_password(password, _DUMMY_HASH)