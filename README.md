# PetroNexa v1.0 — Release-Ready Source

This package contains the PetroNexa FastAPI backend and the Flutter mobile/desktop client source.

**Important:** it is release-ready source, not a signed Android/iOS store binary. The Flutter SDK, native build tools, Apple/Google developer accounts and signing credentials are required to produce store submissions.

## Key repairs made
1. Repaired the supplied `main.py`, which was corrupted by two concatenated versions.
2. Restored the authentication schemas and `get_current_user` dependency that the API imports.
3. Unified registration/login around the existing PBKDF2 security implementation.
4. Moved the Flutter source into a normal `mobile_app/lib` structure.
5. Added the missing Flutter assets and the approved PetroNexa logo.
6. Added persistent JWT session checking and correct logout navigation.
7. Added a production API URL override and input/error handling.
8. Preserved the existing Python engineering engines rather than rewriting their equations.

## Backend
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Production environment must use a strong `JWT_SECRET_KEY`, PostgreSQL and HTTPS. Restrict CORS to actual web origins.

## Flutter
```bash
cd mobile_app
flutter create . --platforms=android,ios,windows,macos,linux
flutter pub get
flutter analyze
flutter run --dart-define=PETRONEXA_API_URL=https://YOUR-API-DOMAIN
```

Android release:
```bash
flutter build appbundle --release --dart-define=PETRONEXA_API_URL=https://YOUR-API-DOMAIN
```

iOS release (macOS/Xcode required):
```bash
flutter build ipa --release --dart-define=PETRONEXA_API_URL=https://YOUR-API-DOMAIN
```

## Current mobile scope
- Secure login/session
- Hydraulics calculation and diagnostics
- Primary cementing design
- Project listing
- PetroNexa branding

The API already provides project creation and PDF reporting endpoints for the next UI pass.

## Engineering modules
The Python core currently includes drilling hydraulics, cementing, pressure gradients, mud parsing and benchmarking. The architecture is ready for trajectory/MCM, bit hydraulics, BHA/MWD, surge/swab, well control, petrophysics, reservoir/PVT, production and economics.

## Store submission
Before launch, complete `RELEASE_CHECKLIST.md`, configure the native Android/iOS identifiers and signing, publish the privacy policy and terms, prepare screenshots/store copy, and validate the engineering calculations with a qualified engineer.
