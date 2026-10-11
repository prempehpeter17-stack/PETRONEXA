# PetroNexa Web Release Checklist

- [ ] Install dependencies from `requirements.txt` in a clean virtual environment.
- [ ] Run `python -m compileall .`.
- [ ] Run the automated test suite with `pytest -q`.
- [ ] Test registration for student and professional accounts.
- [ ] Test duplicate email and duplicate username handling.
- [ ] Test login with valid and invalid credentials.
- [ ] Test schema migration against a copy of any existing production database.
- [ ] Verify reservoir and drilling calculations against reference examples.
- [ ] Configure persistent production database and strong `JWT_SECRET_KEY`.
- [ ] Restrict CORS to the approved origins.
- [ ] Configure HTTPS and secure deployment secrets.
- [ ] Integrate and test an SMS provider before claiming SMS delivery is available.
- [ ] Review privacy policy, terms and applicable data-protection obligations.
- [ ] Verify the deployed Streamlit web app and API health endpoint.

This checklist covers web deployment only. Engineering outputs remain decision-support tools and require qualified review before field use.
