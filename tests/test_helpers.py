from pipeline import helpers

def test_helpers_module_exists():
    assert hasattr(helpers, "__file__")

def test_function_view_output(capsys):
    helpers.function_view()
    captured = capsys.readouterr()
    assert "function_view" in captured.out
