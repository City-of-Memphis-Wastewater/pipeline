
### Key Risk Areas (I checked twice)

| Risk | Mitigated? | How |
|------|------------|-----|
| `typer.Exit` in library code | YES | Removed everywhere |
| Web server crash on no VPN | YES | Only `EdsTimeoutError` raised |
| Breaking existing imports | YES | Old file untouched |
| Missing `requests` import | YES | Added in `session.py` |
| Context manager not closing session | YES | `__exit__` always closes |
| Inconsistent error messages | YES | All use same text |

### Final Step (optional, later)

When ready, add this to `src/pipeline_eds/api/__init__.py`:

```python
# Backward compatibility — remove when migration complete
from ..api.eds import EdsRestClient, EdsTimeoutError, EdsAuthError
```

