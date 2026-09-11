class AppConfig {
  static const apiBaseUrl = String.fromEnvironment(
    'PETRONEXA_API_URL',
    defaultValue: 'https://api.example.com',
  );

  static bool get isConfigured =>
      apiBaseUrl.startsWith('https://') && !apiBaseUrl.contains('example.com');
}
