# PetroNexa v1.0 — Store-Ready Source

PetroNexa is structured as a Flutter client + FastAPI engineering backend.

## What was fixed from the supplied ZIP

- Repaired the corrupted/duplicated `main.py` (the supplied file contained two concatenated versions and was not valid Python).
- Restored the missing authentication schemas and `get_current_user` dependency.
- Unified registration/login with the PBKDF2 security implementation already used by `router.py`.
- Moved the Flutter client into a standard `mobile_app/lib/...` structure.
- Added the missing Flutter `assets/` directory and PetroNexa logo.
- Added persistent JWT session checking.
- Added proper logout navigation.
- Added input validation/error handling around engineering calls.
- Added a production-safe API URL override using `--dart-define`.
- Kept the existing Python engineering engines instead of rewriting their equations.

## Important: this is source-ready, not signed-store binaries

I cannot create a genuine signed Android APK/AAB or iOS IPA without the Flutter SDK, Android/iOS build toolchains, certificates and store credentials. The package is prepared so those platform folders can be generated cleanly.

## 1. Prepare Flutter platforms

```bash
cd mobile_app
flutter create . --platforms=android,ios,windows,macos,linux
flutter pub get
flutter analyze
```

## 2. Run against a deployed HTTPS API

```bash
flutter run --dart-define=PETRONEXA_API_URL=https://YOUR-API-DOMAIN
```

Do **not** ship the default `https://api.example.com`. Replace it with the real deployed PetroNexa API.

For Android emulator local development, use `http://10.0.2.2:8000` and configure Android cleartext traffic only for a development build. For a physical phone, use the computer's LAN IP and the appropriate network configuration.

## 3. Backend

Install Python dependencies:

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

For production set:

- `ENVIRONMENT=production`
- `JWT_SECRET_KEY=<strong-secret-from-secret-manager>`
- `DATABASE_URL=postgresql+asyncpg://...`
- `CORS_ORIGINS=<only your approved app/web origins>`

Use HTTPS at the reverse proxy/load balancer.

## 4. Store build

Android:

```bash
flutter build appbundle --release --dart-define=PETRONEXA_API_URL=https://YOUR-API-DOMAIN
```

iOS (on macOS with Xcode):

```bash
flutter build ipa --release --dart-define=PETRONEXA_API_URL=https://YOUR-API-DOMAIN
```

Then sign/upload the resulting build through Google Play Console / App Store Connect.

## Current v1 scope

- Authentication
- Hydraulics calculation + diagnostics
- Primary cementing design
- Project listing
- Persistent session
- PetroNexa branding

Next modules can be added without changing the engineering-core architecture: mud engineering, trajectory/MCM, pressure window, bit hydraulics, BHA/MWD, surge/swab, well control, petrophysics, reservoir/PVT, production and economics.

## Engineering disclaimer

PetroNexa outputs are engineering decision-support aids. They are not automatic operational authority. Inputs, assumptions, units and results must be reviewed by a qualified petroleum/drilling/cementing engineer before field use.
