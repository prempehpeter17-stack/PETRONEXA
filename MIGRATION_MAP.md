# PetroNexa migration map

| File | Decision | Reason |
|---|---|---|
| `physics.py` | KEEP + branding cleanup | Existing drilling hydraulics engine and tests work. |
| `cementing_engine.py` | KEEP + branding cleanup | Existing cementing engine works and is covered by tests. |
| `gradients.py` | KEEP | Reusable pressure-window logic. |
| `mud_parser.py` | KEEP | Reusable input/parsing engine. |
| `benchmarks.py` | KEEP | Reusable comparison logic. |
| `pdf_generator.py` | MODIFY | Keep report engine; rebrand and use from API. |
| `app.py` | KEEP temporarily | Existing Streamlit client remains available as the web/legacy UI. |
| `main.py` | MODIFY/REPLACE | Becomes the clean client-facing PetroNexa API. |
| `database.py` | MODIFY | Environment-driven DB; local SQLite + production PostgreSQL. |
| `security.py` | MODIFY | Remove hardcoded secret and centralise security settings. |
| `auth.py` | MODIFY | Stronger validation and unified settings. |
| `router.py` | MODIFY | Registration/login fixes and PetroNexa API conventions. |
| `requirements.txt` | MODIFY | Add complete runtime dependencies including PostgreSQL driver. |
| `docker.yml` | REMOVE | Old compose file referenced a missing Dockerfile and hardcoded secrets. |
| `Dockerfile` | NEW | Reproducible backend/frontend container image. |
| `docker-compose.yml` | NEW | Local two-service development stack. |
| `config.py` | NEW | Central configuration. |
| `test_api.py` | NEW | API smoke/auth coverage. |
| `mobile_app/` | NEW | Flutter Android/iOS/desktop client. |
| `docs/` | NEW | Architecture and release controls. |
| `create_admin.py` | MODIFY | No credentials in source. |
| `check_user.py` | MODIFY | No credential/hash output. |
| `README.md` | REPLACE | PetroNexa setup and migration documentation. |
