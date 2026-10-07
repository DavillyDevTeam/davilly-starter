import os
import tempfile
from pathlib import Path

_database = Path(tempfile.mkdtemp(prefix="davilly-auth-")) / "test.db"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_database}"
os.environ["SECRET"] = "test-secret-not-for-production-use"
os.environ["SPA_ORIGIN"] = "http://testserver"
os.environ["CORS_ORIGINS"] = "http://testserver"
for _name in (
    "GOOGLE_OAUTH_CLIENT_ID",
    "GOOGLE_OAUTH_CLIENT_SECRET",
    "GITHUB_OAUTH_CLIENT_ID",
    "GITHUB_OAUTH_CLIENT_SECRET",
    "AUTH_CSRF_COOKIE_SECURE",
):
    _ = os.environ.pop(_name, None)
