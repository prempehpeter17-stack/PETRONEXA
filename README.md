# PetroNexa — Petroleum Engineering Web Platform

PetroNexa is a web-based petroleum engineering workspace built with Streamlit, with a FastAPI service for authenticated engineering endpoints.

## Current web features

- Email/password account registration and sign-in
- Separate tertiary-student and working-professional profiles
- User-provided institution or company name
- Optional SMS updates consent (SMS delivery requires a configured provider; it is not enabled by this code alone)
- Drilling hydraulics and diagnostics
- Cementing design and technical PDF reports
- Reservoir engineering calculations: reservoir properties, Darcy flow, radial flow, productivity index, Vogel IPR and material balance
- User project endpoints in the API

## Run the Streamlit web app

Python 3.11 or newer is recommended.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL printed by Streamlit (normally `http://localhost:8501`). The app uses SQLite by default and creates `petronexa.db` locally. Do not commit database files or `.env` secrets.

## Run the API service

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

API documentation is available at `/docs` while the service is running. For production, configure a persistent database, a strong `JWT_SECRET_KEY`, approved `CORS_ORIGINS`, HTTPS and a managed secret store. Never deploy with development secrets.

## Docker Compose

The included `docker-compose.yml` starts the API and Streamlit web interface as separate services. Create a local `.env` file with the required production/development settings before using Compose, or remove `env_file` from the Compose file for a local-only test environment.

## User accounts and SMS

Registration stores a user's full name, username, email, mobile number, country, account type and the relevant institution/company and study/job profile. SMS preference is stored, but sending SMS messages requires a provider integration and must not be advertised as active until configured. Account type is a profile category, not proof of professional accreditation or an authorisation role.

## Engineering notice

PetroNexa calculations are engineering decision-support tools. Inputs, assumptions, units and results must be checked against appropriate engineering references and reviewed by a qualified engineer before field use.
