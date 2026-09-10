class AppConfig {
  // Override this value per environment before release.
  static const apiBaseUrl = String.fromEnvironment('PETRONEXA_API_URL', defaultValue: 'http://127.0.0.1:8000');
}
