"""
pipeline_eds.api.eds — Clean, modern, future-proof EDS API client package

This package replaces the legacy monolithic eds.py while maintaining full
backward compatibility during migration.

Public API:
    EdsRestClient           - Main class (context manager, REST + SOAP)
    EdsTimeoutError     - VPN/no connection
    EdsAuthError        - Bad credentials
    EdsAPIError         - General API failure
"""

from .client import EdsRestClient
from .exceptions import EdsTimeoutError, EdsAuthError, EdsAPIError
from .session import login_to_session, login_to_session_with_credentials
from .points import get_point_live, get_points_export, get_points_metadata
from .trend import load_historic_data
from .graphics import export_graphic, save_graphic

__all__ = [
    "EdsRestClient",
    "EdsTimeoutError",
    "EdsAuthError",
    "EdsAPIError",
    "login_to_session",
    "login_to_session_with_credentials",
    "get_point_live",
    "get_points_export",
    "get_points_metadata",
    "load_historic_data",
    "export_graphic",
    "save_graphic",
]
