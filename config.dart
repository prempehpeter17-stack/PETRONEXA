class AppConfig {
  static const apiBaseUrl = String.fromEnvironment(
    'PETRONEXA_API_URL',
    defaultValue: '',
  );

  static bool get isConfigured => apiBaseUrl.isNotEmpty;
}
