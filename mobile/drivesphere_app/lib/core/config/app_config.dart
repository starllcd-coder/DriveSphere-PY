class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://127.0.0.1:8000/api',
  );

  static const String googleServerClientId = String.fromEnvironment(
    'GOOGLE_SERVER_CLIENT_ID',
    defaultValue: '',
  );

  static const String googleWebClientId = String.fromEnvironment(
    'GOOGLE_WEB_CLIENT_ID',
    defaultValue: '',
  );

  static const String appleClientId = String.fromEnvironment(
    'APPLE_CLIENT_ID',
    defaultValue: '',
  );

  static const String hyperPayEntityId = String.fromEnvironment(
    'HYPERPAY_ENTITY_ID',
    defaultValue: '',
  );

  static const bool enableDemoMode = bool.fromEnvironment(
    'ENABLE_DEMO_MODE',
    defaultValue: false,
  );
}
