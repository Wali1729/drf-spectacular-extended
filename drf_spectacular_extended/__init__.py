import django
import json
from datetime import datetime
from pathlib import Path

# PEP 440-compliant version for PyPI distribution of the extended fork.
__version__ = '0.29.0.post1'

# region agent log
try:
    debug_payload = {
        "sessionId": "fd5a68",
        "runId": "version-resolution",
        "hypothesisId": "H1",
        "location": "drf_spectacular_extended/__init__.py:version",
        "message": "Imported drf_spectacular_extended and resolved __version__",
        "data": {"version": __version__},
        "timestamp": int(datetime.utcnow().timestamp() * 1000),
    }
    debug_log_path = Path("/Users/macbookpro/codebases/drf-spectacular-extended/.cursor/debug-fd5a68.log")
    debug_log_path.parent.mkdir(parents=True, exist_ok=True)
    with debug_log_path.open("a", encoding="utf-8") as _f:
        _f.write(json.dumps(debug_payload) + "\n")
except Exception:
    # Debug logging must not interfere with package import
    pass
# endregion agent log

if django.VERSION < (3, 2):
    default_app_config = 'drf_spectacular_extended.apps.SpectacularConfig'
