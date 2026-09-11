# PetroNexa v1.0 release checklist

## Fixed in this package
- [x] Python backend syntax repaired.
- [x] Authentication dependency/schemas restored.
- [x] Flutter source moved to standard `mobile_app/lib` structure.
- [x] Flutter logo assets included.
- [x] API URL made environment-specific.
- [x] JWT session persistence and logout fixed.

## Still required before public store launch
- [ ] Deploy the FastAPI backend on HTTPS.
- [ ] Set production JWT secret using a secret manager.
- [ ] Use PostgreSQL in production.
- [ ] Restrict CORS to approved origins.
- [ ] Add rate limiting/account lockout.
- [ ] Configure database backups/monitoring.
- [ ] Generate Android/iOS platform folders with Flutter.
- [ ] Set Android application ID and iOS bundle identifier.
- [ ] Configure signing keys/certificates.
- [ ] Create app icons/splash sizes for all platforms.
- [ ] Publish privacy policy and terms.
- [ ] Prepare store screenshots, description and support contact.
- [ ] Complete Flutter analyse/tests on a real build environment.
- [ ] Validate engineering outputs against the Python reference tests.
- [ ] Review the engineering disclaimer with a qualified engineer.

## Critical distinction

This ZIP is **store-ready source**, not a finished signed Play Store/App Store binary. Store binaries require the Flutter SDK, native build toolchains and the developer's signing credentials.
