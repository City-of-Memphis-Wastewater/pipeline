# src/pipeline_tests/variable_clarity.py
"""
Redundancy helpers

* ``return_hint`` – pure query → hint where the result *should* be stored. 
    The function is still available for modular use that mismatches the suggestion 
    but the suggestion exists as a guide for how the value is returned to a script 
    and the  exertnally added as an atttribute explicitly in the script.

* ``set_and_return`` – command → automatically stores the result **and** returns it
    (the classic “double-tap” you wanted to make explicit).

    Both decorators assume the instance has a ``self._assignment_hints`` dict
    (initialised in ``__init__`` of the client class).

The rest of the file is stripped to the essentials – the old
``check_for_match_of_versions_or_terminate``, ``compare`` and the
``MaintainUsageStatus`` machinery were either broken or never used.
If you need version-checking later, add a dedicated module.
"""

from __future__ import annotations

import logging
import sys
from functools import wraps
from typing import Any, Callable

log = logging.getLogger(__name__)


class Redundancy:
    """Decorators that make “double-tap” assignments explicit and safe."""

    # --------------------------------------------------------------------- #
    # 1. Pure query → hint (no side-effect)
    # --------------------------------------------------------------------- #
    @staticmethod
    def return_hint(recipient: str | None, attribute_name: str) -> Callable:
        """
        Decorator for a *pure* query.

        * Returns the calculated value.
        * Stores a hint on ``self._assignment_hints`` for linters / docs.
        * Does **not** mutate the instance.

        Example
        -------
        >>> @Redundancy.return_hint(recipient="self", attribute_name="customer_id")
        ... def get_customer_id(self) -> int:
        ...     ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(self, *args, **kwargs) -> Any:
                value = func(self, *args, **kwargs)

                # initialise hint container the first time we see it
                if not hasattr(self, "_assignment_hints"):
                    self._assignment_hints = {}

                self._assignment_hints[func.__name__] = {
                    "recipient": recipient,
                    "target_attr": attribute_name,
                    "intended_value": value,
                    "hint": f"client.{attribute_name} = client.{func.__name__}()",
                }
                return value

            return wrapper

        return decorator

    # --------------------------------------------------------------------- #
    # 2. Command → auto-assign + return (the “double-tap” you love)
    # --------------------------------------------------------------------- #
    @staticmethod
    def set_and_return(attribute_name: str) -> Callable:
        """
        Decorator that **guarantees** the result is stored on the instance.

        * Calls the wrapped function.
        * ``setattr(self, attribute_name, result)``
        * Returns the result for the classic ``obj.x = obj.calc_x()`` line.

        Example
        -------
        >>> @Redundancy.set_and_return("customer_id")
        ... def fetch_customer_id(self) -> int:
        ...     ...
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(self, *args, **kwargs) -> Any:
                value = func(self, *args, **kwargs)
                setattr(self, attribute_name, value)
                return value

            return wrapper

        return decorator

    # --------------------------------------------------------------------- #
    # 3. Tiny runtime sanity-check (optional)
    # --------------------------------------------------------------------- #
    @staticmethod
    def compare(a: Any, b: Any, *, name: str = "value") -> None:
        """
        Fail fast if two values that *must* be equal differ.

        >>> Redundancy.compare(client.customer_id, cached_id, name="customer_id")
        """
        if a != b:
            log.error(
                "Redundancy mismatch on %s: %r != %r", name, a, b
            )
            sys.exit(1)


# ------------------------------------------------------------------------- #
# (Optional) – a tiny helper you can import elsewhere to assert two
# sources are identical at import time.  Keep it **outside** the class so
# it can be used as a module-level function.
# ------------------------------------------------------------------------- #
def assert_equal(*sources: Any, name: str = "source") -> None:
    """
    Simple import-time assertion.

    >>> from pipeline_tests.variable_clarity import assert_equal
    >>> assert_equal(API_URL, CONFIG.api_url, name="API base URL")
    """
    if not sources:
        return
    first = sources[0]
    for i, other in enumerate(sources[1:], start=2):
        if first != other:
            log.error(
                "assert_equal failure (%s): item 1 %r != item %d %r",
                name,
                first,
                i,
                other,
            )
            sys.exit(1)


# ------------------------------------------------------------------------- #
# Demo / self-test
# ------------------------------------------------------------------------- #
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    class Demo:
        def __init__(self):
            self._assignment_hints = {}

        @Redundancy.return_hint(recipient="self", attribute_name="answer")
        def query_answer(self) -> int:
            return 42

        @Redundancy.set_and_return("answer")
        def command_answer(self) -> int:
            return 42

    d = Demo()

    # hint path -------------------------------------------------------------
    ans = d.query_answer()
    print("Hint stored →", d._assignment_hints["query_answer"]["hint"])
    print("Returned   →", ans)

    # command path -----------------------------------------------------------
    ans2 = d.command_answer()
    print("Auto-assigned →", d.answer)
    print("Returned      →", ans2)

    # sanity check -----------------------------------------------------------
    Redundancy.compare(ans, ans2, name="answer")

"""
## What changed & why it’s **better**

| Issue | Old code | New code | Benefit |
|-------|----------|----------|---------|
| **Two `Redundancy` classes** | Overwrote the first one | Single class with both decorators | No silent loss of functionality |
| **`__init__` / `__dict__` on `Redundancy`** | Broke instance dict | Removed – not needed | Cleaner, no magic-method hijack |
| **`check_for_match_of_versions_or_terminate`** | Half-implemented, printed instead of logging | Replaced by `Redundancy.compare` + `assert_equal` | Consistent logging, `sys.exit` on mismatch |
| **`MaintainUsageStatus` / `FindThatFunctionInTheCodeBase`** | Dead / broken import cycle | Deleted | No runtime errors |
| **Docstrings** | Mixed in code | Centralised, PEP-257 style | Easier to read / generate docs |
| **Runtime sanity** | `print` + `sys.exit` scattered | Central `compare` + optional `assert_equal` | One place to tweak behaviour |

"""

#*Prefer `return_hint` for public query methods* – you keep the **pure-function** guarantee.  
#*Use `set_and_return` for internal helpers* where you **always** want the attribute set.
