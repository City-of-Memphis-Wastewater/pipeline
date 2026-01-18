# tests/test_sys_path_debug.py
from pipeline_eds import helpers, philosophy  # Make sure at least one real module is used

def test_show_sys_path():
    import sys
    print("\n--- sys.path ---")
    for p in sys.path:
        print(p)

    assert hasattr(helpers, "__file__")  # ✅ harmless
    helpers.function_view()
    print(philosophy.Philosophy())
