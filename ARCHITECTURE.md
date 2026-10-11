# PetroNexa Web Architecture

```text
Browser
  |
  v
Streamlit web interface (app.py)
  |-- UI modules (ui/drilling.py, ui/reservoir.py)
  |-- Engineering calculation modules
  |-- SQLAlchemy async database layer

Optional HTTP API service (main.py)
  |-- Authentication and project endpoints
  |-- Drilling hydraulics and PDF endpoints
  |-- Reservoir calculation endpoints
  |-- SQLAlchemy database layer
```

## Key design rules

- Keep engineering calculations in reusable Python modules, separate from UI code.
- Treat student/professional account type as profile information, not as a security permission.
- Keep secrets in environment variables or a managed secret store; never commit `.env` files.
- Apply database migrations when existing user tables gain new profile fields.
- Do not enable SMS marketing until a provider is configured and consent/unsubscribe handling is implemented.
- Validate engineering calculations against trusted benchmarks before operational use.
