from app.security.argon2_hasher import Argon2PasswordHasher


def test_hash_and_verify_success() -> None:
    hasher = Argon2PasswordHasher()
    raw_password = "StrongPassw0rd!"

    hashed = hasher.hash(raw_password)

    assert hashed != raw_password
    assert hasher.verify(raw_password, hashed) is True


def test_verify_returns_false_for_wrong_password() -> None:
    hasher = Argon2PasswordHasher()
    hashed = hasher.hash("StrongPassw0rd!")

    assert hasher.verify("WrongPassw0rd!", hashed) is False


def test_needs_rehash_returns_true_for_invalid_hash() -> None:
    hasher = Argon2PasswordHasher()

    assert hasher.needs_rehash("not-a-valid-argon2-hash") is True
