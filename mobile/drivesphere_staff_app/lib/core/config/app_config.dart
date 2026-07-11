class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'https://drivesphere-demo-production.up.railway.app/api/v1',
  );

  static const String appEnv = String.fromEnvironment(
    'APP_ENV',
    defaultValue: 'Production',
  );
}