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
