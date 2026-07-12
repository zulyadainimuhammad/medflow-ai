import pytest

from app.security.password_policy import PasswordPolicy, PasswordPolicyViolationError


@pytest.mark.parametrize(
    "password",
    [
        "VeryStrongPassw0rd!",
        "An0ther#SecurePassword",
    ],
)
def test_password_policy_accepts_valid_passwords(password: str) -> None:
    policy = PasswordPolicy()

    policy.validate(password)


def test_password_policy_rejects_too_short_password() -> None:
    policy = PasswordPolicy()

    with pytest.raises(PasswordPolicyViolationError) as exc_info:
        policy.validate("Ab1!")

    assert any("at least 12" in violation for violation in exc_info.value.violations)


def test_password_policy_rejects_missing_uppercase() -> None:
    policy = PasswordPolicy()

    with pytest.raises(PasswordPolicyViolationError) as exc_info:
        policy.validate("lowercase123!")

    assert any("uppercase" in violation.lower() for violation in exc_info.value.violations)


def test_password_policy_rejects_missing_lowercase() -> None:
    policy = PasswordPolicy()

    with pytest.raises(PasswordPolicyViolationError) as exc_info:
        policy.validate("UPPERCASE123!")

    assert any("lowercase" in violation.lower() for violation in exc_info.value.violations)


def test_password_policy_rejects_missing_numeric() -> None:
    policy = PasswordPolicy()

    with pytest.raises(PasswordPolicyViolationError) as exc_info:
        policy.validate("NoNumberPass!")

    assert any("numeric" in violation.lower() for violation in exc_info.value.violations)


def test_password_policy_rejects_missing_special_character() -> None:
    policy = PasswordPolicy()

    with pytest.raises(PasswordPolicyViolationError) as exc_info:
        policy.validate("NoSpecialPass123")

    assert any("special" in violation.lower() for violation in exc_info.value.violations)


def test_password_policy_rejects_common_password_blacklist() -> None:
    policy = PasswordPolicy()

    with pytest.raises(PasswordPolicyViolationError) as exc_info:
        policy.validate("password123")

    assert any("too common" in violation.lower() for violation in exc_info.value.violations)


def test_password_policy_rejects_password_reuse_via_hook() -> None:
    policy = PasswordPolicy()

    with pytest.raises(PasswordPolicyViolationError) as exc_info:
        policy.validate("VeryStrongPassw0rd!", password_reuse_checker=lambda _: True)

    assert any("reuse" in violation.lower() for violation in exc_info.value.violations)
