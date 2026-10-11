# Web Project Structure

| Path | Purpose |
|---|---|
| `app.py` | Streamlit web interface and web-app authentication flow |
| `ui/drilling.py` | Drilling and cementing workspace UI |
| `ui/reservoir.py` | Reservoir engineering workspace UI |
| `physics.py` | Drilling hydraulics and diagnostics calculations |
| `cementing_engine.py` | Cementing design calculations |
| `reservoir/engine.py` | Reservoir engineering calculations |
| `database.py` | SQLAlchemy models, sessions and schema migration |
| `auth.py`, `security.py`, `router.py` | Authentication schemas, password security and API routes |
| `main.py` | Optional FastAPI service for engineering endpoints |
| `test_*.py` | Automated tests |

The repository is intentionally web-only. Flutter/Dart source and mobile build artefacts have been removed from this version.
