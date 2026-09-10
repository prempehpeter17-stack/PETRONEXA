# PetroNexa release checklist

## Engineering
- [ ] Every new equation has a reference and unit test.
- [ ] Python reference results are cross-checked against the mobile implementation before offline mode is enabled.
- [ ] Boundary cases and invalid units are tested.
- [ ] Reports clearly state assumptions and inputs.
- [ ] Safety-critical outputs are labelled as engineering aids, not automatic operational authority.

## Security
- [ ] Production `JWT_SECRET_KEY` is set from a secret manager.
- [ ] Production PostgreSQL is configured.
- [ ] CORS contains only known client origins.
- [ ] HTTPS is enforced.
- [ ] Database backups are configured.
- [ ] Rate limiting and account lockout are added before public launch.
- [ ] No `.env` or credentials are committed.

## Mobile/Desktop
- [ ] `flutter analyze` passes.
- [ ] Android release build is signed.
- [ ] iOS release build is signed.
- [ ] Windows/macOS/Linux builds are tested.
- [ ] App icon and splash assets are supplied in all required sizes.
- [ ] API base URL is environment-specific.
- [ ] Offline sync conflict rules are tested before enabling offline edits.

## Store/legal
- [ ] Privacy policy published.
- [ ] Terms of use published.
- [ ] Support contact published.
- [ ] App screenshots and store descriptions prepared.
- [ ] Engineering disclaimer reviewed by the project owner/qualified engineer.
