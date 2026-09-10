# PetroNexa mobile/desktop client

Flutter client for Android, iOS, Windows, macOS and Linux. The project is intentionally kept separate from the Python engineering core: the API exposes the same tested engines to every client.

## First run

1. Install Flutter 3.24+.
2. From this folder run `flutter create .` to generate the standard platform folders (Android/iOS/Windows/macOS/Linux).
3. Run `flutter pub get`.
4. Start the PetroNexa FastAPI backend.
5. Run with `flutter run`.

For a phone talking to a backend on your laptop, replace `http://127.0.0.1:8000` in `lib/services/api_client.dart` with the laptop's LAN IP, for example `http://192.168.1.10:8000`.

For production, use HTTPS and a deployed API URL.
