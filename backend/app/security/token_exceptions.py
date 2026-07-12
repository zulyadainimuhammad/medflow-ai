from __future__ import annotations


class TokenServiceError(Exception):
    """Base exception for token utility failures."""


class TokenDecodeError(TokenServiceError):
    pass


class TokenExpiredError(TokenServiceError):
    pass


class TokenInvalidAudienceError(TokenServiceError):
    pass


class TokenInvalidIssuerError(TokenServiceError):
    pass


class TokenRevokedError(TokenServiceError):
    pass


class TokenTypeError(TokenServiceError):
    pass
