from app.api.auth.routes import PasswordHasherAdapter
from app.security.argon2_hasher import Argon2PasswordHasher


def test_password_hasher_adapter_hash_and_verify() -> None:
    adapter = PasswordHasherAdapter(Argon2PasswordHasher())
    password = "StrongPassw0rd!"

    hashed = adapter.hash_password(password)

    assert hashed != password
    assert adapter.verify_password(password, hashed) is True


def test_password_hasher_adapter_verify_rejects_incorrect_password() -> None:
    adapter = PasswordHasherAdapter(Argon2PasswordHasher())
    hashed = adapter.hash_password("StrongPassw0rd!")

    assert adapter.verify_password("WrongPassw0rd!", hashed) is False
