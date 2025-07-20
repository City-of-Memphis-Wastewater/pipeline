from pipeline import status_api

def test_status_api_has_state():
    assert hasattr(status_api, "get_status")
