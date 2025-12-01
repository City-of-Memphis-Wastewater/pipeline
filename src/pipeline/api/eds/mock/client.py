from __future__ import annotations
from contextlib import contextmanager
from .session import login_to_session_with_credentials
from .exceptions import EdsTimeoutError

class EdsRestClient:
    def __init__(self, credentials: dict):
        self.credentials = credentials
        self.session = None

    @contextmanager
    def connect(self):
        try:
            self.session = login_to_session_with_credentials(self.credentials)
            yield self.session
        except EdsTimeoutError:
            print("\n[EDS CLIENT] Connection to the EDS API timed out. Please check your VPN connection and try again.")
            raise
        finally:
            if hasattr(self, "session") and self.session:
                try:
                    self.session.close()
                except:
                    pass

    def __enter__(self):
        self.session = login_to_session_with_credentials(self.credentials)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            self.session.close()
        return False
