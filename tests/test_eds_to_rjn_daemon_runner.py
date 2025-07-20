# tests/test_eds_to_rjn_daemon_runner.py
import pytest

@pytest.mark.slow
def test_run_hourly_tabular_trend_eds_to_rjn_test_mode():
    """
    This test runs the ETL logic in test mode (no live RJN transmission).
    It will raise errors if anything in the pipeline fails.
    """
    from workspaces.eds_to_rjn.scripts.daemon_runner import run_hourly_tabular_trend_eds_to_rjn
    try:
        run_hourly_tabular_trend_eds_to_rjn(test=True)
    except Exception as e:
        pytest.fail(f"ETL run in test mode failed: {e}")

