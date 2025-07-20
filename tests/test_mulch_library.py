#tests/test_mulch_library.py
def test_mulch_import():
    import mulch
    assert hasattr(mulch, "__version__") or hasattr(mulch, "init")

def test_mulch_cli_simulation(monkeypatch, capsys):
    import mulch.cli  # adjust if needed
    monkeypatch.setattr("builtins.input", lambda _: "n")
    mulch.cli.main()
    output = capsys.readouterr().out.lower()
    assert "workspace" in output or "scaffold" in output
