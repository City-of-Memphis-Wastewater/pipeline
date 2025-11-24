from __future__ import annotations

class EdsAPIError(RuntimeError):
    """Base exception for all EDS API errors"""
    pass

class EdsTimeoutError(EdsAPIError, ConnectionError):
    """Raised when EDS server is unreachable (no VPN, timeout)"""
    pass

class EdsAuthError(EdsAPIError, PermissionError):
    """Raised when login fails due to bad credentials"""
    pass

class EdsRequestError(EdsAPIError):
    """Raised when API returns error status but connection succeeded"""
    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


class EdsLoginException(Exception):
    """
    Custom exception raised when a login to the EDS API fails.

    This exception is used to differentiate between a simple network timeout
    and a specific authentication or API-related login failure.
    """

    def __init__(self, message: str = "Login failed for the EDS API. Check VPN and credentials."):
        """
        Initializes the EdsLoginException with a custom message.

        Args:
            message: A descriptive message for the error.
        """
        self.message = message
        super().__init__(self.message)

